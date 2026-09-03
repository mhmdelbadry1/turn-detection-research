#!/usr/bin/env python3
"""Stream a stereo wav (or two mono files) through StreamingVap.

From vap-runtime/:

    PYTHONPATH=third_party:. python examples/stream_file.py \\
        --stereo /path/to/stereo.wav

    PYTHONPATH=third_party:. python examples/stream_file.py \\
        --user ../recordings/00-source-tracks/human.ogg \\
        --agent ../recordings/00-source-tracks/agent.ogg

Prints last-frame p_now every 100 ms. First run downloads the CPC encoder
(~hundreds of MB) into torch hub cache, then into third_party/assets/.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "third_party"))

from breez_vap import StreamingVap, load_vap  # noqa: E402

SR = 16000
CHUNK = 1600  # 100 ms


def _mono(path: Path) -> np.ndarray:
    y, file_sr = sf.read(str(path), dtype="float32", always_2d=False)
    if y.ndim > 1:
        y = y.mean(axis=-1)
    if file_sr != SR:
        from torchaudio.functional import resample

        y = resample(torch.from_numpy(y).unsqueeze(0), file_sr, SR).squeeze(0).numpy()
    return y.astype(np.float32)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stereo", type=Path, help="(n, 2) or (2, n) wav, ch0=user ch1=agent")
    p.add_argument("--user", type=Path, help="mono user track")
    p.add_argument("--agent", type=Path, help="mono agent/TTS track")
    p.add_argument("--window", type=float, default=5.0, help="transformer context seconds")
    p.add_argument("--checkpoint", type=Path, default=None)
    args = p.parse_args()

    if args.stereo:
        y, file_sr = sf.read(str(args.stereo), dtype="float32", always_2d=True)
        if file_sr != SR:
            raise SystemExit(f"need {SR} Hz stereo (got {file_sr})")
        if y.shape[1] != 2:
            raise SystemExit(f"need 2 channels, got {y.shape}")
        user, agent = y[:, 0], y[:, 1]
    elif args.user and args.agent:
        user, agent = _mono(args.user), _mono(args.agent)
        n = min(len(user), len(agent))
        user, agent = user[:n], agent[:n]
    else:
        p.error("pass --stereo or both --user and --agent")

    model, device = load_vap(checkpoint=args.checkpoint)
    stream = StreamingVap(model, transformer_ctx_sec=args.window, device=device)
    stream.reset()

    print(f"device={device} window={args.window}s samples={len(user)} ({len(user)/SR:.1f}s)")
    i = 0
    last = None
    while i < len(user):
        chunk = np.stack([user[i : i + CHUNK], agent[i : i + CHUNK]], axis=0)
        if chunk.shape[1] < CHUNK:
            pad = np.zeros((2, CHUNK - chunk.shape[1]), dtype=np.float32)
            chunk = np.concatenate([chunk, pad], axis=1)
        out = stream.step(torch.from_numpy(chunk))
        i += CHUNK
        if out.get("n_feat_frames", 0) == 0:
            continue
        p_now = out["p_now"][0, -1].cpu().numpy()
        vad = out["vad"][0, -1].cpu().numpy()
        t = i / SR
        last = (t, p_now, vad)
        print(
            f"t={t:7.2f}s  p_user={p_now[0]:.3f}  p_agent={p_now[1]:.3f}  "
            f"vad_u={vad[0]:.2f}  vad_a={vad[1]:.2f}  yield={p_now[0] > p_now[1]}"
        )

    if last is None:
        print("no frames (audio too short)")
        return
    # flush 20 ms holdback at end of file
    out = stream.step(torch.zeros(2, 0), flush=True)
    print("done. live calls should NOT flush — leave the 20 ms holdback pending.")


if __name__ == "__main__":
    main()
