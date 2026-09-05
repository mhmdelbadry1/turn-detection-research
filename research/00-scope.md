# Scope of this study

The question was: **which pause-EOT model**, at what threshold, at what CPU cost, with what Arabic quality — and how overlap (barge-in vs backchannel) should be treated separately. Work ran in September 2026. This folder is the write-up: tables, clips, and a small VAP runtime. The working notebook is not copied here.

Every number in this folder was measured or read from a cited source. Unpublished papers and invented scores are not used.

| # | Question | Status | Where |
|---|---|---|---|
| 1 | Reproduce public eot-bench (Smart Turn + v1-mini, Arabic + English) | Done — exact match to published FC@300ms | [02-eot-bench-numbers.md](02-eot-bench-numbers.md) |
| 2 | NAMO on the same harness | Done — first public-harness number; worse than VAD | same + [FINDINGS.md](../FINDINGS.md) |
| 3 | Pause-head CPU (p50/p95, CPU% at ~15 pauses/min, machine spec) | Done on Apple M5, not production Linux | [05-cpu-cost.md](05-cpu-cost.md) |
| 4 | In-domain Arabic set, 300–500 turns, all three models | **Open** — needs a call-recording export. Not pulled from production here | n=1 51Talk listen: [04-vap-listen-on-one-call.md](04-vap-listen-on-one-call.md) |
| 5 | What would a Smart Turn retrain cost (data, GPU hours, expected gain)? | Scoped 2026-09-05. **Not trained** | [09-smart-turn-finetune-scope.md](09-smart-turn-finetune-scope.md) |
| 6 | What breaks on livekit-agents 1.4.5 → 1.6.x with a forked `AudioRecognition`? | Scoped 2026-09-05. Upgrade not started. Breez fork file was not on this machine | [10-livekit-1.6-upgrade-scope.md](10-livekit-1.6-upgrade-scope.md) |
| 7 | One-page conclusion: model, thresholds, FC/latency, CPU, risks | [FINDINGS.md](../FINDINGS.md) — final on what was measurable; interim on in-domain Arabic until (4) exists | |

Work **outside** that list, included because the 51Talk call’s problem is overlap, which eot-bench cannot score:

- Last-token text gates on lagged STT: **negative** (same structural issue as NAMO).
- Score-fusion of VAP + Smart Turn on pause-EOT: **negative** for Arabic.
- VAP as overlap head, CPU, quantization (rejected), streaming CPC, 5 s window: `vap-runtime/` and [03-architecture-two-heads.md](03-architecture-two-heads.md).

## Still open

1. **Gulf/Levantine eval set** (hundreds of turns). The only gap that can reorder the pause-head ranking.
2. **Training** a Gulf Smart Turn mix-in — waits on a train slice **disjoint** from that eval set. Scope is done.
3. Hunk-by-hunk diff of Breez `breez_audio_recognition_v2.py` — needs a read-only agent-service checkout. The upstream diff and the effort call do not.
4. CPU table on production Linux, if it will be used for capacity.
