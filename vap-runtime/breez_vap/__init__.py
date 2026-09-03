"""Breez VAP runtime — load, stream, and apply the overlap policy.

Typical use:

    from breez_vap import load_vap, StreamingVap, vap_only_mute

    model, device = load_vap()
    stream = StreamingVap(model, transformer_ctx_sec=5.0)  # 5 s is the default
    stream.reset()
    out = stream.step(stereo)  # stereo: (2, n) float32 @ 16 kHz
    # out["p_now"][:, :, 0] = P(user speaks in the next ~0.4 s)
"""

from breez_vap.load import load_vap
from breez_vap.naive import NaiveVap
from breez_vap.policy import twohead_mute, vap_only_mute
from breez_vap.streaming import (
    DS_CTX,
    HOLDBACK_HOPS,
    HOP,
    LOOKBACK_HOPS,
    StreamingVap,
)

__all__ = [
    "DS_CTX",
    "HOLDBACK_HOPS",
    "HOP",
    "LOOKBACK_HOPS",
    "NaiveVap",
    "StreamingVap",
    "load_vap",
    "twohead_mute",
    "vap_only_mute",
]
