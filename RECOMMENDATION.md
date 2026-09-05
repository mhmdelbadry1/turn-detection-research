# Recommendation — turn detection (2026-09-05)

Brief item 7. **Opinion**, backed by our own measurements. Numbers are **fact** unless marked. Item 4 (Gulf export) is still open, so this is final on everything we could measure and **interim on Arabic traffic**. Coverage: [research/00-status.md](research/00-status.md).

---

## The one page

**Replace NAMO with Smart Turn v3.2 as the pause head, on the LiveKit SDK we already run. Do not upgrade the SDK to get there. Do not fine-tune yet. Keep VAP behind a flag for overlap only.**

| Decision | Call | Why |
|---|---|---|
| Pause head today | **Smart Turn v3.2**, unstubbed on `livekit-agents==1.4.5` | Arabic false-cutoff **39.2%** vs NAMO **64.6%** — ~25 pp better, no SDK bump |
| Keep NAMO? | **No** | Worse than a plain silence timer (54.8%). Its only advantage, CPU, is irrelevant |
| Keep Krisp VAD? | **Yes** | These are pause classifiers, they run *after* VAD silence. They do not replace it |
| LiveKit v1-mini | **Real option, scheduled decision** | Best measured (Arabic **24.4%**) but needs `1.6.x` **and dropping the `AudioRecognition` fork** |
| Smart Turn fine-tune | **Not yet** | ~2–4 engineer days + ~3–12 L4-hours, but needs a Gulf train set **disjoint** from the eval export |
| VAP | **Later, flagged** | It is the overlap head, not a turn detector. English checkpoint, n=1 Gulf call |

**Operating point to ship** (eot-bench Arabic, 300 ms budget): Smart Turn threshold **0.260**, action_delay **0.200 s**, timeout **1.000 s**. (v1-mini, if ever: threshold 0.270, same delay and timeout.)

**Accuracy** — eot-bench validation, false-cutoff @ 300 ms, lower is better. v1-mini and Smart Turn reproduce the published leaderboard **exactly**; NAMO is our number, the first on a public harness.

| | Arabic | English |
|---|---:|---:|
| LiveKit v1-mini | **24.4%** | **27.8%** |
| Smart Turn v3.2 | 39.2% | 35.2% |
| VAD, silence only | 54.8% | 55.6% |
| VAP with silent agent channel | 54.8% | — |
| NAMO multilingual | **64.6%** | 70.4% |

**CPU is not a constraint.** Per pause: Smart Turn p50 **22.3 ms**, NAMO **7.05 ms**, v1-mini **7.85 ms**. At ~15 pauses/min that is 1–4% of one core. All ≪ the 300 ms conversational budget. Apple M5 — **re-measure on EKS before any capacity plan.** ([research/05-cpu-cost.md](research/05-cpu-cost.md))

**Sequence:**

1. **Now** — unstub Smart Turn on 1.4.5, keep Krisp, ship at the threshold above. Effort **S**, inside the existing fork.
2. **Blocked on Omar** — export 300–500 Gulf/Levantine turns, re-score all three models on real traffic. This is the number that should govern, not public Arabic.
3. **Then, if the gap to v1-mini still matters** — either schedule the `1.6.10` bump with the fork dropped, or fine-tune Smart Turn on a separate Gulf slice. Both are scoped; neither is started.
4. **Later, flagged** — VAP as the overlap head, after it beats the cheap duration rule.

**Top risks:** (a) public Arabic eot-bench is not HeyBreez traffic — item 4 could move every number; (b) bumping the SDK without passing a detector **silently** ships v1-mini, because the 1.6 default changed; (c) all CPU figures are from a Mac; (d) fine-tune gain is a hypothesis, 0–10 pp, with no public precedent.

---

## Do not do

- **Do not blend VAP and Smart Turn into one score.** Four fusion rules, fixed before looking: **every one made Arabic worse** than Smart Turn alone, English was noise. Two heads, two jobs, two clocks — not two `p_eot`s averaged.
- **Do not ship VAP as the turn detector.** With a silent agent channel on eot-bench it lands exactly on the VAD baseline (54.8%), because the sweep set threshold = 0. Its job is overlap while TTS plays. ([research/08-vap-silent-ch1.md](research/08-vap-silent-ch1.md))
- **Do not keep NAMO because it is cheap.** It is the weakest option we measured, and the cost it saves is ~15 ms per pause.
- **Do not default the streaming VAP transformer to 1 s.** KTH's "1 s is enough" was silence shift/hold on a Japanese model. On the 51Talk overlap clip, 1 s gave **0.10 s** of mute vs **0.76 s** at 5 s.
- **Do not train Smart Turn on v1-mini outputs.** The LiveKit Model License forbids it.
- **Do not train on the 300–500 eval turns.** Hold them out or the fine-tune result is meaningless.

## Target stack — two heads

| Head | When it *acts* | Model | Status |
|---|---|---|---|
| **Pause** | User went silent; may we start TTS? | **Smart Turn v3.2** now; v1-mini is more accurate and is a real 1.6.10 path **if** we drop the fork | Ship ST on 1.4.5 |
| **Overlap** | TTS is playing; should we yield? | **VAP**, English checkpoint, streaming CPC, **5 s** transformer window | Later, behind a flag |

**Run VAP continuously; gate the action, not the model.** The CPC encoder is unreliable for the first 1–2 s after a cold start, so starting it at TTS onset makes it worst exactly when barge-ins happen.

**Make the yield sticky** — once VAP says yield inside a TTS island, stay muted until that island ends, or the agent stutters on and off.

**Feed VAP the TTS reference at playout, not at generation.** Generation-time audio leads the ear by hundreds of ms and fabricates overlap.

## VAP in one paragraph

Voice Activity Projection (Ekstedt & Skantze, KTH). Stereo: ch0 = user, ch1 = agent. Every 20 ms it emits `p_now` = P(that speaker talks in the next ~0.4 s); we yield while TTS plays when `p_user > p_agent`. Our streaming implementation persists the CPC encoder (90% of the cost) and re-runs the transformers only on the last 5 s: **0.187 cores per concurrent call** at 10 Hz on an M5, single thread, down from **2.0 cores** naive. Quantization was tried and **rejected** (int8 is accurate but slower, or it breaks the model). On the 51Talk call, VAP alone does **not** skip an isolated «آه» — **VAP + Smart Turn** does. Details: [vap-runtime/README.md](vap-runtime/README.md), [vap-runtime/BEFORE_AFTER.md](vap-runtime/BEFORE_AFTER.md).

## The two paths past Smart Turn (both scoped, neither started)

**v1-mini on `livekit-agents==1.6.10`** — the weights ship in the core SDK from 1.6.1. The blocker is not the model, it is our forked `AudioRecognition`: upstream grew 752 → 1,960 lines and renamed the exact methods a fork would override (`start`/`push_audio`/`update_options` → `_start`/`_push_audio`/`_update_options`), so a 1.4.5-style subclass **silently no-ops**. Dropping the fork and passing `inference.TurnDetector(version="v1-mini")` is **S–M** on the turn wiring (**M–L** for the whole bump); re-porting the fork is **L** and leaves us on a text detector anyway. Full breakdown: [research/10-livekit-1.6-upgrade-scope.md](research/10-livekit-1.6-upgrade-scope.md).

**Fine-tuning Smart Turn** — their `train.py` is a **full retrain from `openai/whisper-tiny`** (4 epochs, batch 384, 270,946 public clips ≈ 2,540 steps), not "continue from v3.2," because Pipecat publishes ONNX only. Cost is **~3–12 L4-hours** (unverified) plus **~2–4 engineer days** of slicing and listen-QC; the money is trivial, the labelling is not. Expected Arabic gain is a **hypothesis** (0–10 pp) with no public precedent, and it is **not** guaranteed to catch v1-mini. Full breakdown: [research/09-smart-turn-finetune-scope.md](research/09-smart-turn-finetune-scope.md).

## Still open

1. **300–500 Gulf turn export** (brief item 4) — the only gap that could change the ranking above.
2. **Re-measure CPU on EKS** before any capacity claim.
3. **Duration-heuristic overlap baseline** — "ignore user speech shorter than ~300 ms while TTS plays" is still unmeasured. VAP must beat that cheap rule, not beat doing nothing.
4. **Adaptive interruption in 1.6.x** (`InterruptionOptions.mode="adaptive"`) is a *third* model, unmeasured on Arabic. Do not assume the SDK bump hands us an overlap head for free.
5. **Other LiveKit monkey-patches in agent-service** — unknown from this machine, and they dominate the real cost of a 1.6.x bump.
