# Turn detection research

**Internal.** Contains a 51Talk caller recording. Do not publish.

Start here, then read **[RECOMMENDATION.md](RECOMMENDATION.md)**. Runnable overlap-head code: **[vap-runtime/](vap-runtime/)**. Listen clips by type: **[recordings/](recordings/)**.

This is the distilled report (tables, decision, clips, VAP runtime). The working notebook stays in the research workspace; it was not copied here.

| Read this | What it is |
|---|---|
| [research/00-status.md](research/00-status.md) | Original brief vs what is done. Gaps called out. |
| [RECOMMENDATION.md](RECOMMENDATION.md) | **Ship this.** Pause head vs overlap head. |
| [research/01-from-the-beginning.md](research/01-from-the-beginning.md) | Prod today (NAMO), what we ran, in order. |
| [research/02-eot-bench-numbers.md](research/02-eot-bench-numbers.md) | Reproduced leaderboard + NAMO on the same harness. |
| [research/08-vap-silent-ch1.md](research/08-vap-silent-ch1.md) | How VAP got 54.8% on eot-bench (silent agent channel). |
| [research/05-cpu-cost.md](research/05-cpu-cost.md) | Pause-head p50/p95 and CPU% (Apple M5). |
| [research/03-architecture-two-heads.md](research/03-architecture-two-heads.md) | Two jobs, two clocks. Why score fusion failed. |
| [research/04-vap-listen-on-one-call.md](research/04-vap-listen-on-one-call.md) | 51Talk A/B: what each clip folder is. |
| [research/06-vap-benchmarks.md](research/06-vap-benchmarks.md) | The actual VAP protocol (S/H, S/L, S-pred, BC-pred). Not eot-bench. |
| [research/07-vap-datasets.md](research/07-vap-datasets.md) | Switchboard vs Fisher vs Candor — which to test on. |
| [research/09-smart-turn-finetune-scope.md](research/09-smart-turn-finetune-scope.md) | Brief item 5. Data effort, GPU hours, expected gain. Not trained. |
| [research/10-livekit-1.6-upgrade-scope.md](research/10-livekit-1.6-upgrade-scope.md) | Brief item 6. What breaks on 1.6.x, and how v1-mini becomes real. |
| [vap-runtime/README.md](vap-runtime/README.md) | How VAP works, defaults, how to run. |
| [vap-runtime/BEFORE_AFTER.md](vap-runtime/BEFORE_AFTER.md) | Naive rolling window vs streaming CPC. |
| [recordings/README.md](recordings/README.md) | How to listen. One folder per mix type. |

## Open on the product side

1. **Unstub Smart Turn** in agent-service (replace NAMO for pause-EOT). CPU is not a reason to keep NAMO.
2. **Export 300–500 Gulf turns** (eval). Fine-tune is **scoped** — still do not train until a **disjoint** train slice exists.
3. Decide whether **LiveKit Agents 1.6.x** is acceptable (v1-mini path = drop the `AudioRecognition` fork).
4. **VAP is later**, behind a flag. Runtime is ready to try. English checkpoint, n=1 Gulf call.

## Layout

```
turn-detection-research/
  RECOMMENDATION.md
  research/
  recordings/
    00-source-tracks/              human.ogg + agent.ogg (VAP input)
    01-original-mix/
    02-offline-vap-20s/
    03-offline-twohead-v1mini/
    04-offline-twohead-smartturn/
    05-streaming-1s/               weaker overlap
    06-streaming-5s-recommended/   default
    07-streaming-20s/              misses 10 Hz
  vap-runtime/                     ready to use
```
