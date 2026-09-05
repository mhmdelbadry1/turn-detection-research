# Turn detection research

A note on **when a voice agent should start speaking**, and **when it should yield**. Measurements, listen clips, and a small runtime for the overlap head. Not a product ticket.

The listen set in `recordings/` is a real telephony call. Keep this repository private.

Start with **[FINDINGS.md](FINDINGS.md)** (the one-page conclusion). Code for the overlap head: **[vap-runtime/](vap-runtime/)**. Clips: **[recordings/](recordings/)**.

| Note | Contents |
|---|---|
| [FINDINGS.md](FINDINGS.md) | Pause head vs overlap head. What the numbers support. |
| [research/00-scope.md](research/00-scope.md) | Questions asked, what was measured, what is still open. |
| [research/01-from-the-beginning.md](research/01-from-the-beginning.md) | Production baseline, then the experiments in order. |
| [research/02-eot-bench-numbers.md](research/02-eot-bench-numbers.md) | Public eot-bench, plus NAMO on the same harness. |
| [research/08-vap-silent-ch1.md](research/08-vap-silent-ch1.md) | Why silent-agent VAP matches a silence timer on eot-bench. |
| [research/05-cpu-cost.md](research/05-cpu-cost.md) | Pause-head latency and CPU% (Apple M5). |
| [research/03-architecture-two-heads.md](research/03-architecture-two-heads.md) | Two jobs, two clocks. Why score fusion failed. |
| [research/04-vap-listen-on-one-call.md](research/04-vap-listen-on-one-call.md) | One 51Talk call: what each clip folder is. |
| [research/06-vap-benchmarks.md](research/06-vap-benchmarks.md) | VAP’s own protocol (S/H, S/L, S-pred, BC-pred). Not eot-bench. |
| [research/07-vap-datasets.md](research/07-vap-datasets.md) | Switchboard vs Fisher vs Candor. |
| [research/09-smart-turn-finetune-scope.md](research/09-smart-turn-finetune-scope.md) | What a Smart Turn retrain would cost. Not trained. |
| [research/10-livekit-1.6-upgrade-scope.md](research/10-livekit-1.6-upgrade-scope.md) | What 1.4.5 → 1.6.x does to `AudioRecognition`, and how v1-mini becomes available. |
| [vap-runtime/README.md](vap-runtime/README.md) | Streaming VAP: defaults and how to run. |
| [vap-runtime/BEFORE_AFTER.md](vap-runtime/BEFORE_AFTER.md) | Naive rolling window vs streaming CPC. |
| [recordings/README.md](recordings/README.md) | How to listen. One folder per mix. |

## What is still open

1. A held-out Gulf/Levantine eval set (hundreds of real turns). Public eot-bench Arabic is not this traffic.
2. Whether LiveKit Agents 1.6.x is worth taking for v1-mini — that path means dropping the `AudioRecognition` fork, not re-porting it.
3. VAP as an overlap head, behind a flag, after it is compared to a duration heuristic. English checkpoint, n=1 Gulf call so far.

## Layout

```
turn-detection-research/
  FINDINGS.md
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
  vap-runtime/
```
