"""Streaming VAP: persist CPC history, only attend over a short transformer window.

Matches the IWSDS 2024 real-time recipe (Inoue et al.): the CPC encoder is
autoregressive and keeps the full call; the transformers see only a short
window of features. KTH used ~1 s (silence shift/hold). On our 51Talk overlap
clips, **5 s is the default** — 1 s missed barge-in. This EncoderCPC has no
streaming path, so we wrap it.

gEncoder (strided convs) is not causal. Leftover-only chunking mismatches the
offline forward (mean abs ~0.4). Overlap-save of 4 hops (640 samples) plus
holding back the last 2 hops (320 samples) matches to ~1e-6.

The two stereo channels share one EncoderCPC. LSTM hidden state is therefore
kept *per channel* and passed into `gAR.baseNet` — we never set `keepHidden`
on the shared module (that would leak channel 0 into channel 1).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import einops
import torch
import torch.nn.functional as F

HOP = 160  # gEncoder downsample, 100 Hz
LOOKBACK_HOPS = 4  # 640 samples — covers RF ≈ 465
HOLDBACK_HOPS = 2  # 320 samples / 20 ms; last frames need right-context
DS_CTX = 4  # CConv1d causal pad (kernel 5)


@dataclass
class _ChannelState:
    leftover: torch.Tensor
    lookback: torch.Tensor
    pending: torch.Tensor
    lstm_hidden: Optional[tuple[torch.Tensor, torch.Tensor]]
    ds_ctx: torch.Tensor
    feat: torch.Tensor  # (1, T, dim) rolling 50 Hz features


class StreamingVap:
    def __init__(
        self,
        model,
        *,
        transformer_ctx_sec: float = 5.0,
        device: Optional[torch.device] = None,
        keep_all_features: bool = False,
    ) -> None:
        self.model = model.eval()
        self.device = device or next(model.parameters()).device
        self.sample_rate = int(model.sample_rate)
        self.frame_hz = int(model.frame_hz)
        self.dim = int(model.conf.dim)
        self.transformer_frames = max(1, int(round(transformer_ctx_sec * self.frame_hz)))
        self.transformer_ctx_sec = float(transformer_ctx_sec)
        self.keep_all_features = bool(keep_all_features)
        enc = model.encoder
        self._genc = enc.encoder.gEncoder
        self._lstm = enc.encoder.gAR.baseNet
        ds = enc.downsample
        self._ds_conv = ds[1]
        self._ds_ln = ds[2]
        self._ds_act = ds[3]
        self._states: list[_ChannelState] | None = None
        self.n_feat_frames = 0

    def reset(self) -> None:
        self._states = [self._empty_channel(), self._empty_channel()]
        self.n_feat_frames = 0

    def _empty_channel(self) -> _ChannelState:
        z = torch.zeros(1, 0, device=self.device)
        return _ChannelState(
            leftover=z,
            lookback=z,
            pending=z,
            lstm_hidden=None,
            ds_ctx=torch.zeros(1, DS_CTX, self.dim, device=self.device),
            feat=torch.zeros(1, 0, self.dim, device=self.device),
        )

    @torch.no_grad()
    def step(self, stereo: torch.Tensor, *, flush: bool = False, encode_only: bool = False) -> dict[str, torch.Tensor]:
        """Consume a stereo chunk `(2, n)` or `(1, 2, n)`. Returns last-frame outputs.

        `flush=True` emits the held-back hops (end of a finite file). Live calls
        leave them pending so the next chunk can supply right-context.
        """
        if stereo.ndim == 3:
            stereo = stereo[0]
        if stereo.shape[0] != 2:
            raise ValueError(f"expected (2, n) stereo, got {tuple(stereo.shape)}")
        stereo = stereo.to(self.device)
        if self._states is None:
            self.reset()

        new_frames = 0
        for ch, state in enumerate(self._states):
            new_frames = max(new_frames, self._push_channel(state, stereo[ch], flush=flush))

        t = min(s.feat.shape[1] for s in self._states)
        self.n_feat_frames = t
        if t == 0:
            return {"n_new_frames": 0, "n_feat_frames": 0}
        if encode_only:
            return {"n_new_frames": int(new_frames), "n_feat_frames": int(t)}

        win = min(self.transformer_frames, t)
        x1 = self._states[0].feat[:, -win:]
        x2 = self._states[1].feat[:, -win:]
        o1 = self.model.ar_channel(x1)["x"]
        o2 = self.model.ar_channel(x2)["x"]
        out = self.model.ar(o1, o2)
        logits = self.model.vap_head(out["x"])
        vad = torch.cat(
            (self.model.va_classifier(out["x1"]), self.model.va_classifier(out["x2"])),
            dim=-1,
        )
        probs = logits.softmax(dim=-1)
        p_now = self.model.objective.probs_next_speaker_aggregate(probs, from_bin=0, to_bin=1)
        self.n_feat_frames = t
        return {
            "logits": logits,
            "vad": vad.sigmoid(),
            "p_now": p_now,
            "n_new_frames": int(new_frames),
            "n_feat_frames": int(t),
        }

    def _push_channel(self, state: _ChannelState, wav: torch.Tensor, *, flush: bool) -> int:
        wav = wav.view(1, -1)
        buf = torch.cat([state.leftover, wav], dim=-1)
        n_hops = buf.shape[-1] // HOP
        state.leftover = buf[..., n_hops * HOP :]
        hops = buf[..., : n_hops * HOP]
        if n_hops == 0 and not flush:
            return 0

        audio = torch.cat([state.lookback, state.pending, hops], dim=-1)
        if audio.shape[-1] < HOP:
            return 0
        z = einops.rearrange(self._genc(audio.unsqueeze(1)), "b c n -> b n c")
        n_look = state.lookback.shape[-1] // HOP
        z = z[:, n_look:]
        consumed = torch.cat([state.pending, hops], dim=-1)

        if (not flush) and z.shape[1] > HOLDBACK_HOPS:
            finalized = z[:, :-HOLDBACK_HOPS]
            finalized_audio = consumed[..., : -HOLDBACK_HOPS * HOP]
            state.pending = consumed[..., -HOLDBACK_HOPS * HOP :]
            pool = torch.cat([state.lookback, finalized_audio], dim=-1)
            state.lookback = pool[..., -LOOKBACK_HOPS * HOP :]
        else:
            finalized = z
            pool = torch.cat([state.lookback, consumed], dim=-1)
            state.lookback = pool[..., -LOOKBACK_HOPS * HOP :]
            state.pending = consumed[..., :0]

        if finalized.shape[1] == 0:
            return 0

        z_ar, hidden = self._lstm(finalized, state.lstm_hidden)
        state.lstm_hidden = tuple(h.detach() for h in hidden)

        x = torch.cat([state.ds_ctx, z_ar], dim=1)
        xt = einops.rearrange(x, "b t d -> b d t")
        y = F.conv1d(xt, self._ds_conv.weight, self._ds_conv.bias, stride=2)
        y = self._ds_act(self._ds_ln(y))
        y = einops.rearrange(y, "b d t -> b t d")
        state.ds_ctx = x[:, -DS_CTX:]
        if y.shape[1] == 0:
            return 0
        feat = torch.cat([state.feat, y], dim=1)
        if not self.keep_all_features:
            feat = feat[:, -max(self.transformer_frames, 1) :]
        state.feat = feat
        return int(y.shape[1])

    @torch.no_grad()
    def decode_last(self, window_frames: int) -> tuple[torch.Tensor, torch.Tensor]:
        """p_now and vad at the last feature frame, attending over `window_frames`."""
        t = min(s.feat.shape[1] for s in self._states)
        w = min(int(window_frames), t)
        x1 = self._states[0].feat[:, -w:]
        x2 = self._states[1].feat[:, -w:]
        o1 = self.model.ar_channel(x1)["x"]
        o2 = self.model.ar_channel(x2)["x"]
        out = self.model.ar(o1, o2)
        logits = self.model.vap_head(out["x"])
        vad = torch.cat(
            (self.model.va_classifier(out["x1"]), self.model.va_classifier(out["x2"])),
            dim=-1,
        ).sigmoid()
        p_now = self.model.objective.probs_next_speaker_aggregate(
            logits.softmax(dim=-1), from_bin=0, to_bin=1
        )
        return p_now[0, -1], vad[0, -1]
