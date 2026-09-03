# Recommendation (2026-09-03)

**Opinion**, with the Gulf export (brief item 4) and fine-tune / LiveKit-upgrade scopes (items 5–6) still open. Numbers below are **fact** unless marked otherwise. Coverage of the original brief: [research/00-status.md](research/00-status.md).

## Ship now

**Replace NAMO with Smart Turn v3.2** for pause-EOT (user went quiet; should the agent start TTS?).

- Unstub the dead Smart Turn server (it has returned `{"eou_probability": 0.5}` since Feb 2026, commit `b860211b` as reported).
- Keep **Krisp VAD**. These models are pause classifiers; they run *after* silence, they do not replace VAD.
- CPU is **not** a reason to keep NAMO. Smart Turn p50 **22.3 ms** vs NAMO **7.05 ms**; both ≪ 300 ms. Full table: [research/05-cpu-cost.md](research/05-cpu-cost.md).
- NAMO on eot-bench Arabic **64.6%** false-cutoff @ 300 ms — **worse than a silence timer** (VAD baseline **54.8%**). Smart Turn **39.2%**. We reproduced the published leaderboard exactly.
- eot-bench operating point used here (Arabic, 300 ms): Smart Turn threshold **0.260**, action_delay **0.200**, timeout **1.000**. (v1-mini: threshold 0.270, same delay/timeout.)

Provider mode (Soniox / Deepgram Flux / Inworld decide EOT) stays out of scope.

## Do not do

- **Do not blend VAP and Smart Turn into one score.** We tried four fusion rules on eot-bench. Every rule made **Arabic worse** than Smart Turn alone. English was noise. Two heads = two jobs on two clocks, not two `p_eot`s averaged.
- **Do not ship VAP as the only turn detector.** Silent agent channel on eot-bench = VAD baseline. VAP’s job is overlap while TTS plays.
- **Do not keep NAMO** because it is “cheap.” It is the weakest option we measured.
- **Do not default the streaming transformer to 1 s.** KTH’s “1 s is enough” was silence shift/hold on a Japanese model. On this 51Talk overlap clip, 1 s mute was **0.10 s** vs **0.76 s** at 5 s (offline 20 s was 0.74 s).

## Target stack (two heads)

| Head | When it *acts* | Model | Status |
|---|---|---|---|
| **Pause** | User silent, decide whether to start TTS | **Smart Turn v3.2** now. v1-mini is more accurate (Arabic 24.4% vs 39.2%) but **license-locked to LiveKit Agents 1.6.x** | Ship ST. v1-mini only if you accept the upgrade. |
| **Overlap** | TTS is playing, decide whether to yield | **VAP**, English checkpoint, streaming CPC, **5 s transformer window** | Later, behind a flag. Runtime is in `vap-runtime/`. n=1 Gulf call. |

**Run VAP continuously; gate the action, not the model.** Cold-start the first 1–2 s is unreliable. Starting the encoder at TTS onset makes it worst exactly when barge-ins happen.

**Make the yield sticky.** Once VAP says yield during a TTS island, stay muted until that TTS ends, or the agent stutters on/off.

Feed VAP **user + TTS at playout time** (stereo). Generation-time TTS that leads the ear by hundreds of ms fabricates overlap.

## VAP, one paragraph

Voice Activity Projection (Ekstedt & Skantze, KTH). Stereo: ch0 = user, ch1 = agent. Every 20 ms it outputs `p_now` = P(that speaker talks in the next ~0.4 s). We yield while TTS plays if `p_user > p_agent`. The **optimized** code (`vap-runtime/breez_vap/streaming.py`) persists the CPC encoder (90% of cost) and only re-runs transformers on the last **5 s**. Naive 5 s window was **2.0 cores/call**; streaming 5 s is **0.187 cores/call** at 10 Hz on an M5, 1 thread. Quantization was tried and rejected (int8 accurate but slower, or it breaks the model). Details: `vap-runtime/README.md` and `BEFORE_AFTER.md`.

On the 51Talk call: VAP-only does **not** skip isolated «آه»; **VAP + Smart Turn** did. Overlap yield on «لأنه» recovers at 5 s, not at 1 s.

## Still open (original brief items 4–6, plus EKS)

1. **300–500 Gulf turn export** — public eot-bench Arabic is not our traffic.
2. **Smart Turn fine-tune scope only** — do not start training until the export exists.
3. **livekit-agents 1.4.5 → 1.6.x** scoped (fork re-port) — not started.
4. Re-measure CPU on **EKS** before capacity claims (all numbers here are Apple M5).
5. Duration-heuristic baseline for overlap (“ignore user speech shorter than ~300 ms during TTS”) is **still unmeasured**. VAP has to beat that cheap rule, not beat “do nothing.”

## Accuracy snapshot (fact, eot-bench validation, FC@300ms, lower is better)

| | Arabic | English |
|---|---:|---:|
| LiveKit v1-mini | **24.4%** | **27.8%** |
| Smart Turn v3.2 | 39.2% | 35.2% |
| VAD (silence only) | 54.8% | 55.6% |
| VAP silent-ch1 | 54.8% | — |
| NAMO multilingual | **64.6%** | 70.4% |

v1-mini / Smart Turn match the published leaderboard **exactly**. NAMO is ours (first public-harness number).
