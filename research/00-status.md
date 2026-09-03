# Status vs the original brief (2026-09-01)

The brief asked for a recommendation backed by **our** numbers: which model, at what thresholds, at what CPU cost, with what Arabic quality. Seven acceptance items. This package is the distilled report — not a dump of the working notebook.

| # | Asked | Done? | In this package? |
|---|---|---|---|
| 1 | Reproduce eot-bench (Smart Turn + v1-mini, ar + en) | **Yes** — exact match to published FC@300ms | [02-eot-bench-numbers.md](02-eot-bench-numbers.md) |
| 2 | NAMO adapter on the same harness | **Yes** — first apples-to-apples number; worse than VAD | same + [RECOMMENDATION.md](../RECOMMENDATION.md) |
| 3 | CPU cost table (p50/p95, CPU% @ ~15 pauses/min, machine spec) | **Yes** (Apple M5 — not EKS) | [05-cpu-cost.md](05-cpu-cost.md) |
| 4 | HeyBreez Arabic test set, 300–500 turns, all three models scored | **No** — blocked on a call-recording export. Do not pull prod data. | n=1 51Talk listen only: [04-vap-listen-on-one-call.md](04-vap-listen-on-one-call.md) |
| 5 | Scope Smart Turn fine-tune (effort, GPU hours, expected gain) — do not train | **No** — waiting on step 4 audio | — |
| 6 | Scope livekit-agents 1.4.5 → 1.6.x (AudioRecognition fork re-port) | **No** — needs a read-only checkout of agent-service | — |
| 7 | One-page recommendation: model, thresholds, FC/latency, CPU, rollout risks | **Yes, interim** — still waiting on 4–6 | [RECOMMENDATION.md](../RECOMMENDATION.md) |

Extra work **not** in the original six tasks, included because the 51Talk call’s pain is overlap, which eot-bench cannot score:

- Last-token text gates on lagged STT: **negative** (same structural issue as NAMO).
- Score-fusion of VAP + Smart Turn on pause-EOT: **negative** for Arabic.
- VAP as overlap head, CPU, quantization (rejected), streaming CPC, 5 s window: in `vap-runtime/` and [03-architecture-two-heads.md](03-architecture-two-heads.md).

## What “full research” means here

This folder has the **conclusions, tables, listen clips, and runnable VAP**. It does **not** contain the working notebook (`notes/`, eot-bench venv, raw parquets). Those stay in the research workspace. Every number in this package was measured; we did not invent papers or scores.

## Still needed before the original brief is complete

1. 300–500 Gulf/Levantine turn export (schema in the 2026-09-01 brief §5.5).
2. Fine-tune scope write-up after that export exists.
3. Read-only diff of `AudioRecognition` (livekit-agents 1.4.5 vs 1.6.x vs Breez fork).
4. Re-run the CPU table on EKS if it will be used for capacity.
