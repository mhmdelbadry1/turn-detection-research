# Recommendation

**2026-09-05.** Opinion where stated; numbers are measured unless marked. Public eot-bench Arabic is not Gulf telephony, so the ranking below is **interim on in-domain traffic**. Coverage of the study: [research/00-scope.md](research/00-scope.md).

---

Turn-taking splits into two jobs. **Pause-EOT** (the user went quiet; may the agent start TTS?) is what eot-bench scores. **Overlap** (TTS is already playing; is the user taking the floor, or backchannelling?) is a different clock, and eot-bench cannot score it.

On pause-EOT, **Smart Turn v3.2** is the model the measurements support using on the LiveKit SDK already in production (`livekit-agents==1.4.5`). **NAMO** is weaker than a silence timer. **v1-mini** is more accurate, but only becomes available after a 1.6.x upgrade that drops the `AudioRecognition` fork. Fine-tuning Smart Turn was scoped, not run. **VAP** is an overlap model, not a pause detector.

| Question | Finding | Evidence |
|---|---|---|
| Pause classifier, given 1.4.5 | **Smart Turn v3.2** (currently stubbed) | Arabic FC@300ms **39.2%** vs NAMO **64.6%** |
| Keep NAMO? | No, on this harness | Worse than VAD-only **54.8%**. CPU is not the reason to keep it |
| Keep Krisp VAD? | Yes | Pause models fire *after* VAD silence. They do not replace VAD |
| LiveKit v1-mini | Best pause number; blocked by SDK + fork | Arabic **24.4%**; needs `1.6.x` and a stock `TurnDetector` |
| Fine-tune Smart Turn | Second step, not the first | Needs a Gulf train set **disjoint** from eval. Gain is a hypothesis |
| VAP | Overlap head, later | English checkpoint, n=1 Gulf call. Not a turn detector |

**Operating point on eot-bench Arabic** (300 ms latency budget): Smart Turn threshold **0.260**, action_delay **0.200 s**, timeout **1.000 s**. v1-mini, if used later: threshold **0.270**, same delay and timeout.

**Accuracy** — eot-bench validation, false-cutoff @ 300 ms, lower is better. v1-mini and Smart Turn match the published leaderboard **exactly**. NAMO is measured here; it had no public-harness number before.

| | Arabic | English |
|---|---:|---:|
| LiveKit v1-mini | **24.4%** | **27.8%** |
| Smart Turn v3.2 | 39.2% | 35.2% |
| VAD, silence only | 54.8% | 55.6% |
| VAP, silent agent channel | 54.8% | — |
| NAMO multilingual | **64.6%** | 70.4% |

**CPU is not the constraint for pause heads.** Per pause: Smart Turn p50 **22.3 ms**, NAMO **7.05 ms**, v1-mini **7.85 ms**. At ~15 pauses/min that is 1–4% of one core, all well under a 300 ms conversational budget. Machine: Apple M5. These figures do not transfer to Linux production nodes. ([research/05-cpu-cost.md](research/05-cpu-cost.md))

What follows from that, if someone were to act on it:

1. Restore Smart Turn on 1.4.5, keep Krisp, use the threshold above. Small change inside the existing fork.
2. Score the same three models on a held-out Gulf/Levantine set. That number should govern, not public Arabic.
3. If the gap to v1-mini still matters after that: either take `1.6.10` and drop the fork, or retrain Smart Turn on a separate Gulf slice. Both are scoped; neither was started.
4. Treat VAP as overlap, after it beats a duration heuristic, not as the pause head.

**Caveats.** (a) Public Arabic eot-bench is not HeyBreez traffic — an in-domain set could reorder the table. (b) Upgrading to 1.6.x without passing a detector silently selects v1-mini, because the default changed. (c) All CPU figures are from a Mac. (d) Fine-tune gain is a hypothesis (0–10 pp) with no public precedent.

---

## Negative results

- **Averaging VAP and Smart Turn into one `p_eot` made Arabic pause-EOT worse** under four fusion rules fixed before looking. English was within noise. Two heads, two jobs, two clocks.
- **VAP with a silent agent channel is not a pause detector.** On eot-bench it lands on the VAD baseline (54.8%): the sweep set threshold = 0, so the model is ignored and the harness waits 300 ms. ([research/08-vap-silent-ch1.md](research/08-vap-silent-ch1.md))
- **NAMO’s CPU advantage is ~15 ms per pause.** It is the weakest option on this harness.
- **A 1 s streaming VAP transformer is the worse overlap window on the 51Talk clip.** KTH’s “1 s is enough” was silence shift/hold on a Japanese model. Here, 1 s muted **0.10 s** vs **0.76 s** at 5 s.
- **v1-mini outputs cannot be used as training labels** (LiveKit Model License).
- **The 300–500 in-domain turns, if collected, are an eval set.** Training on them would make a fine-tune uninterpretable.

## Two heads

| Head | When it acts | Model | Status in this work |
|---|---|---|---|
| **Pause** | User silent; may TTS start? | Smart Turn v3.2 on 1.4.5. v1-mini is more accurate if the fork is dropped on 1.6.10 | Stock v3.2 is the supported pause finding |
| **Overlap** | TTS playing; should the agent yield? | VAP, English checkpoint, streaming CPC, **5 s** transformer window | Later. Runtime is in `vap-runtime/` |

VAP should run for the whole call; gate the *action*, not the forward pass. The CPC encoder is unreliable for the first 1–2 s after a cold start, so starting it at TTS onset makes it worst when barge-ins happen.

Once VAP says yield inside a TTS island, stay muted until that island ends. On/off muting stutters.

Feed VAP the TTS reference **at playout**, not at generation. Generation-time audio leading the ear by hundreds of ms looks like overlap to the model.

## VAP

Voice Activity Projection (Ekstedt & Skantze, KTH). Stereo: ch0 = user, ch1 = agent. Every 20 ms it emits `p_now` = P(that speaker talks in the next ~0.4 s). Yield while TTS plays when `p_user > p_agent`. The streaming implementation in this package persists the CPC encoder (~90% of cost) and re-runs transformers only on the last 5 s: **0.187 cores per concurrent call** at 10 Hz on an M5, one thread, down from **2.0 cores** naive. Quantization was tried and rejected (int8 accurate but slower, or it breaks the model). On the 51Talk call, VAP alone does not skip an isolated «آه»; VAP plus a pause head does. [vap-runtime/README.md](vap-runtime/README.md), [vap-runtime/BEFORE_AFTER.md](vap-runtime/BEFORE_AFTER.md).

## Two paths past stock Smart Turn (scoped, not started)

**v1-mini on `livekit-agents==1.6.10`.** Weights ship in the core SDK from 1.6.1. The constraint is the forked `AudioRecognition`: upstream grew 752 → 1,960 lines and renamed `start` / `push_audio` / `update_options` to `_start` / `_push_audio` / `_update_options`, so a 1.4.5-style subclass silently no-ops. Dropping the fork and passing `inference.TurnDetector(version="v1-mini")` is the path that makes v1-mini real. Re-porting the fork keeps a text detector. [research/10-livekit-1.6-upgrade-scope.md](research/10-livekit-1.6-upgrade-scope.md).

**Retraining Smart Turn.** Upstream `train.py` is a **full retrain from `openai/whisper-tiny`** (4 epochs, batch 384, 270,946 public clips ≈ 2,540 steps), not a continue-from-v3.2 job — Pipecat publishes ONNX only. Bound **~3–12 L4-hours** (unverified) plus **~2–4 days** of slicing and listen-QC. Expected Arabic FC@300ms change is a **hypothesis** (0–10 pp), not guaranteed to catch v1-mini. [research/09-smart-turn-finetune-scope.md](research/09-smart-turn-finetune-scope.md).

## Open

1. Held-out Gulf/Levantine turns (hundreds). This is the measurement that could change the ranking.
2. CPU on production Linux nodes, before any capacity claim.
3. Duration-heuristic overlap baseline: ignore user speech shorter than ~300 ms while TTS plays. VAP has to beat that rule, not beat doing nothing.
4. Adaptive interruption in LiveKit 1.6.x (`InterruptionOptions.mode="adaptive"`) — a third model, unmeasured on Arabic. The SDK bump does not automatically supply an overlap head.
5. Other LiveKit patches in agent-service. Those, not EOU, dominate the real cost of 1.6.x. The service tree was not on the machine used for this work.
