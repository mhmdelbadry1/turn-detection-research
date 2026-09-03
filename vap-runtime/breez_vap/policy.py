"""Mute / yield policies used on the 51Talk listen mixes.

These are *actions* on top of VAP scores. Run the model all call; only
apply a mute while TTS is playing.
"""
from __future__ import annotations

import numpy as np


def _islands(mask: np.ndarray) -> list[tuple[int, int]]:
    d = np.diff(mask.astype(np.int8), prepend=0, append=0)
    starts, ends = np.where(d == 1)[0], np.where(d == -1)[0]
    return list(zip(starts.tolist(), ends.tolist()))


def vap_only_mute(p_now: np.ndarray, vad: np.ndarray) -> np.ndarray:
    """Yield for the rest of a TTS island once VAP says the user will speak.

    `p_now` is `(T, 2)` — column 0 user, column 1 agent.
    `vad` is `(T, 2)` after sigmoid, 0.5 threshold.
    Sticky: first `p_user > p_agent` while agent VAD is on → mute until TTS ends.
    """
    agent = vad[:, 1] > 0.5
    p_u, p_a = p_now[:, 0], p_now[:, 1]
    mute = agent & (p_u > p_a)
    out = mute.copy()
    for s, e in _islands(agent):
        if mute[s:e].any():
            first = s + int(np.argmax(mute[s:e]))
            out[first:e] = True
    return out


def twohead_mute(
    p_now: np.ndarray,
    vad: np.ndarray,
    hz: float,
    pause_rows: list[dict],
    deny_key: str,
    slack_s: float = 0.05,
) -> np.ndarray:
    """Overlap: VAP. New TTS while the user is silent: pause-head deny list.

    `pause_rows` are `{t, smart_turn_complete, v1_mini_complete, ...}` from a
    pause classifier. `deny_key` is the boolean field that is True when the
    pause head says the user is *done* (so we may start TTS). If the user is
    silent at TTS onset and the pause head denied completion, mute the whole
    island (this is how «آه» was dropped with Smart Turn, not with VAP).
    """
    user = vad[:, 0] > 0.5
    agent = vad[:, 1] > 0.5
    p_u, p_a = p_now[:, 0], p_now[:, 1]
    mute = np.zeros(len(agent), dtype=bool)
    deny_t = np.array([r["t"] for r in pause_rows if not r[deny_key]], dtype=float)

    def denied(t: float) -> bool:
        if deny_t.size == 0:
            return False
        return bool(np.min(np.abs(deny_t - t)) <= slack_s)

    for s, e in _islands(agent):
        t = s / hz
        if (not user[s]) and denied(t):
            mute[s:e] = True
            continue
        ov = user[s:e] & (p_u[s:e] > p_a[s:e])
        if ov.any():
            first = s + int(np.argmax(ov))
            mute[first:e] = True
    return mute
