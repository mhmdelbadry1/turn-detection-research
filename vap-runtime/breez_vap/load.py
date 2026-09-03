"""Load the English stereo VAP checkpoint used in this research."""
from __future__ import annotations

import sys
from pathlib import Path

import torch

_RUNTIME = Path(__file__).resolve().parent.parent
_THIRD = _RUNTIME / "third_party"
_DEFAULT_CKPT = _RUNTIME / "weights" / "VAP_3mmz3t0u_50Hz_ad20s_134-epoch9-val_2.56.pt"

if str(_THIRD) not in sys.path:
    sys.path.insert(0, str(_THIRD))


def load_vap(*, checkpoint: str | Path | None = None, device: str | None = None):
    """Return (model, device).

    First call may download Facebook's CPC encoder (~a few hundred MB) via
    torch.hub if it is not already cached. The VAP checkpoint then overwrites
    those weights with the Switchboard-trained stereo model.
    """
    from vap.model import VapConfig, VapGPT

    ckpt = Path(checkpoint) if checkpoint else _DEFAULT_CKPT
    if not ckpt.exists():
        raise FileNotFoundError(ckpt)

    if device is None:
        device = "mps" if torch.backends.mps.is_available() else "cpu"
    dev = torch.device(device)

    model = VapGPT(VapConfig())
    raw = torch.load(ckpt, map_location="cpu", weights_only=False)
    sd = raw["state_dict"] if isinstance(raw, dict) and "state_dict" in raw else raw
    model.load_state_dict(sd, strict=False)
    model.eval()
    return model.to(dev), dev
