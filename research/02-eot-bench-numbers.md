# eot-bench numbers (reproduced 2026-09-02)

Harness: LiveKit eot-bench, public `livekit/eot-bench-data` **validation**. Arabic 381 turns / 8546 points, English 400 / 11191. Score point 0.2 s. Metric: **false-cutoff @ 300 ms** (lower is better).

Smart Turn used the harness default `smart-turn-v3.2-gpu.onnx` **on CPU** (no CUDA on the research Mac). That is the same default as the published leaderboard.

v1-mini and Smart Turn match the published leaderboard **exactly** (unrounded).

## Arabic

| Model | FC@300ms | FC@600ms | Latency @ 5% cutoff | Latency @ 10% cutoff |
|---|---:|---:|---:|---:|
| LiveKit v1-mini | **24.4%** | **10.3%** | **811 ms** | **610 ms** |
| Smart Turn v3.2 | 39.2% | 13.2% | 814 ms | 636 ms |
| VAD baseline (silence only) | 54.8% | 14.8% | 900 ms | 700 ms |
| VAP (silent agent channel) | 54.8% | — | — | — |
| NAMO multilingual | **64.6%** | — | — | — |

300 ms operating points: v1-mini threshold 0.270, action_delay 0.200, timeout 1.000; Smart Turn threshold 0.260, action_delay 0.200, timeout 1.000.

## English

| Model | FC@300ms | FC@600ms | Latency @ 5% cutoff | Latency @ 10% cutoff |
|---|---:|---:|---:|---:|
| LiveKit v1-mini | **27.8%** | **12.1%** | 1070 ms | **698 ms** |
| Smart Turn v3.2 | 35.2% | 14.8% | **1051 ms** | 739 ms |
| VAD baseline | 55.6% | 21.7% | 1600 ms | 1000 ms |
| NAMO multilingual | 70.4% | — | — | — |

## How to read this

- **v1-mini wins pause-EOT** on this public set. We cannot ship it without LiveKit Agents 1.6.x.
- **Smart Turn is the shippable audio pause head.** ~15 pp worse than v1-mini on Arabic, ~16 pp better than VAD, ~25 pp better than NAMO.
- **NAMO’s 84.9% standalone accuracy is offline, full-transcript.** The 64.6% is causal with 0.5 s transcript lag — the setting that matches streaming STT. The gap is the “NAMO inherits STT lag” claim, quantified.
- **VAP with a silent agent channel is not a pause detector.** It matches VAD. That is expected: projection of “who speaks next” with no agent audio is mostly silence duration, which the harness already sweeps.

## Fusion (2026-09-03)

We fused Smart Turn `p_eot` with silent-ch1 VAP `p_eot` four ways (mean, max, min, product), rules fixed before looking.

- Arabic: **every rule worse** than Smart Turn 39.2% (mean 41.6%, max 40.9%, prod 43.1%, min 47.1%). Conversation bootstrap: mean / prod / min significantly worse.
- English: all four within noise of 35.2%. The one apparent win (prod −1.6 pp) has CI that includes zero, and that same rule is significantly worse in Arabic.

**Do not blend the heads.**
