# Status vs the original brief (2026-09-01)

The brief asked for a recommendation backed by **our** numbers: which model, at what thresholds, at what CPU cost, with what Arabic quality. Seven acceptance items. This package is the distilled report — not a dump of the working notebook.

| # | Asked | Done? | In this package? |
|---|---|---|---|
| 1 | Reproduce eot-bench (Smart Turn + v1-mini, ar + en) | **Yes** — exact match to published FC@300ms | [02-eot-bench-numbers.md](02-eot-bench-numbers.md) |
| 2 | NAMO adapter on the same harness | **Yes** — first apples-to-apples number; worse than VAD | same + [RECOMMENDATION.md](../RECOMMENDATION.md) |
| 3 | CPU cost table (p50/p95, CPU% @ ~15 pauses/min, machine spec) | **Yes** (Apple M5 — not EKS) | [05-cpu-cost.md](05-cpu-cost.md) |
| 4 | HeyBreez Arabic test set, 300–500 turns, all three models scored | **No** — blocked on a call-recording export. Do not pull prod data. | n=1 51Talk listen only: [04-vap-listen-on-one-call.md](04-vap-listen-on-one-call.md) |
| 5 | Scope Smart Turn fine-tune (effort, GPU hours, expected gain) — do not train | **Yes (2026-09-05)** — no training. ~3–12 L4-hours unverified; 2–4 days data prep; gain hypothesis | [09-smart-turn-finetune-scope.md](09-smart-turn-finetune-scope.md) |
| 6 | Scope livekit-agents 1.4.5 → 1.6.x (AudioRecognition fork re-port) | **Yes (2026-09-05)** — upstream 1.4.5 vs 1.6.10; Breez file not on this machine. Drop-fork is the v1-mini path | [10-livekit-1.6-upgrade-scope.md](10-livekit-1.6-upgrade-scope.md) |
| 7 | One-page recommendation: model, thresholds, FC/latency, CPU, rollout risks | **Yes** — final on everything measurable, interim on Arabic traffic until 4 lands | [RECOMMENDATION.md](../RECOMMENDATION.md) |

Extra work **not** in the original six tasks, included because the 51Talk call’s pain is overlap, which eot-bench cannot score:

- Last-token text gates on lagged STT: **negative** (same structural issue as NAMO).
- Score-fusion of VAP + Smart Turn on pause-EOT: **negative** for Arabic.
- VAP as overlap head, CPU, quantization (rejected), streaming CPC, 5 s window: in `vap-runtime/` and [03-architecture-two-heads.md](03-architecture-two-heads.md).

## What “full research” means here

This folder has the **conclusions, tables, listen clips, and runnable VAP**. It does **not** contain the working notebook (`notes/`, eot-bench venv, raw parquets). Those stay in the research workspace. Every number in this package was measured; we did not invent papers or scores.

## Still needed before the original brief is complete

1. **300–500 Gulf/Levantine turn export** (schema in the 2026-09-01 brief §5.5) — item 4, the only open item.
2. Fine-tune **training** still waits on a Gulf train slice **disjoint** from that export. Scope is done.
3. Hunk-by-hunk diff of Breez's `breez_audio_recognition_v2.py` needs a read-only `agent-service` checkout. The upstream diff and the resulting effort call are done without it.
4. Re-run the CPU table on EKS if it will be used for capacity.
