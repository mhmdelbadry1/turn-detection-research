# Turn detection — package for Omar

**Internal.** Contains a 51Talk caller recording. Do not publish.

This folder is the handoff. Start here, then read **[RECOMMENDATION.md](RECOMMENDATION.md)** (the decision). VAP code you can actually run is in **[vap-runtime/](vap-runtime/)**. Listen clips are grouped by type in **[recordings/](recordings/)**.

The research notebook (`notes/`) was **not** moved into this package. This is the distilled end-to-end writeup plus the optimized runtime.

| Read this | What it is |
|---|---|
| [RECOMMENDATION.md](RECOMMENDATION.md) | **Ship this.** Pause head vs overlap head. What not to do. What is still blocked on you. |
| [research/01-from-the-beginning.md](research/01-from-the-beginning.md) | Prod today (NAMO), why we looked, what we tried, in order. |
| [research/02-eot-bench-numbers.md](research/02-eot-bench-numbers.md) | Reproduced leaderboard + NAMO first-ever eot-bench number. |
| [research/03-architecture-two-heads.md](research/03-architecture-two-heads.md) | Two jobs, two clocks. Why score fusion failed. |
| [research/04-vap-listen-on-one-call.md](research/04-vap-listen-on-one-call.md) | 51Talk A/B: what each clip folder is. |
| [vap-runtime/README.md](vap-runtime/README.md) | How VAP works, defaults, how to run. |
| [vap-runtime/BEFORE_AFTER.md](vap-runtime/BEFORE_AFTER.md) | Naive rolling window vs streaming CPC. What changed. |
| [recordings/README.md](recordings/README.md) | How to listen. One folder per mix type. |

## What we want from you

1. **Unstub Smart Turn** in agent-service (replace NAMO for pause-EOT). CPU is not a reason to keep NAMO.
2. **Export 300–500 Gulf turns** (step 4) so we can scope a Smart Turn fine-tune — not start training yet.
3. Decide whether **LiveKit Agents 1.6.x** is acceptable (v1-mini is the best pause number we have, but license-locked).
4. **VAP is later**, not this week's ship. Runtime is ready to try behind a flag. English checkpoint, n=1 Gulf call.

## Layout

```
omar-handoff/
  RECOMMENDATION.md          ← the last thing
  research/                  ← story + numbers
  recordings/
    00-source-tracks/        ← human.ogg + agent.ogg (VAP input)
    01-original-mix/         ← as the customer heard it
    02-offline-vap-20s/      ← first listen that sounded great
    03-offline-twohead-v1mini/
    04-offline-twohead-smartturn/
    05-streaming-1s/         ← sounded worse on overlap
    06-streaming-5s-recommended/  ← recovered; this is the default
    07-streaming-20s/        ← misses 10 Hz in production
  vap-runtime/               ← ready to use
    breez_vap/               ← StreamingVap + policy
    third_party/vap/         ← KTH package (not Switchboard dumps)
    weights/                 ← 22 MB English checkpoint
    examples/stream_file.py
```
