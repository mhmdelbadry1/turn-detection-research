"""Naive VAP — what we ran first, and why it cannot ship.

Re-encodes the last `context_sec` of stereo audio from scratch on every call.
Cost grows linearly with context (≈2 CPU cores per call at 5 s / 10 Hz).
"""
from __future__ import annotations

import torch


class NaiveVap:
    """Full-window re-forward. Matches `model(waveform)` on a rolling buffer."""

    def __init__(self, model, *, context_sec: float = 5.0):
        self.model = model.eval()
        self.sample_rate = int(model.sample_rate)
        self.context_sec = float(context_sec)
        self.max_samples = int(self.context_sec * self.sample_rate)
        self._buf: torch.Tensor | None = None

    def reset(self) -> None:
        self._buf = None

    @torch.no_grad()
    def step(self, stereo: torch.Tensor) -> dict[str, torch.Tensor]:
        """`stereo` is `(2, n)` new samples. Returns last-frame `p_now` (2,) and `vad` (2,)."""
        if stereo.ndim == 3:
            stereo = stereo[0]
        stereo = stereo.to(next(self.model.parameters()).device)
        if self._buf is None:
            self._buf = stereo
        else:
            self._buf = torch.cat([self._buf, stereo], dim=-1)
        if self._buf.shape[-1] > self.max_samples:
            self._buf = self._buf[:, -self.max_samples :]
        x = self._buf.unsqueeze(0)
        out = self.model(x)
        probs = out["logits"].softmax(dim=-1)
        p_now = self.model.objective.probs_next_speaker_aggregate(probs, from_bin=0, to_bin=1)
        vad = out["vad"].sigmoid()
        return {"p_now": p_now[0, -1], "vad": vad[0, -1], "logits": out["logits"]}
