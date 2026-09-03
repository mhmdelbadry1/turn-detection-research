# Architecture: two heads, two clocks

## The two jobs

Voice agents decide two different things:

1. **Pause-EOT.** The user went quiet. Is the turn over so we may start TTS? This is what eot-bench scores. This is what NAMO / Smart Turn / v1-mini do. They run **after VAD silence**.
2. **Overlap / barge-in.** TTS is already playing. Is the user grabbing the floor, or just «eh» / «آه»? eot-bench cannot score this (no agent channel). This is what VAP is for.

Fusing them into one probability **hurts** the pause job (see `02-eot-bench-numbers.md`). Keep two clocks:

```
all call:
  Krisp VAD on user
  Smart Turn when VAD says silence  →  may start TTS
  VAP on stereo (user + TTS-at-playout)  →  scores only; no action yet

while TTS playing:
  if VAP p_user > p_agent:  yield, sticky until this TTS island ends
```

## Why VAP must run even when it must not act

VAP is causal over a rolling stereo context. The CPC encoder is unreliable for the first ~1–2 s after a cold start (our adapter needed 2.1 s of left-pad before features were usable). If you start VAP at TTS onset, it is worst exactly when barge-ins are most likely. **Consume audio all call; gate the mute, not the forward pass.**

## Channel alignment

VAP assumes ch0 and ch1 are aligned as the **user heard them**. In prod, ch1 should be the TTS reference at **playout**, not at generation. Generation can lead the ear by hundreds of ms (network + jitter buffer), which looks like overlap to the model.

After a yield, Smart Turn’s 8 s window may contain a period when the agent was audible. Feed the Krisp-cleaned **user** channel; consider trimming the window to post-yield audio. (Hypothesis — not measured.)

## Sticky yield

Once a TTS island is interrupted, stay interrupted. On/off muting stutters. The listen mixes in `recordings/` use this policy (`vap-runtime/breez_vap/policy.py`).

## Cost shape

Smart Turn fires a few times per minute (~22 ms). VAP is a 50 Hz encoder for the whole call. Naive implementation: **1–2 CPU cores per concurrent call**. Streaming CPC: **~0.19 cores** at 5 s / 10 Hz on M5. Re-measure on EKS before capacity planning.

Quantization is the wrong lever (see `vap-runtime/BEFORE_AFTER.md`).

## What we still have not beaten

The honest overlap baseline is **“ignore user speech shorter than ~300 ms while TTS plays.”** If that catches the same backchannels as VAP, VAP has to earn 0.19 cores. Unmeasured.
