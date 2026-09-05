# livekit-agents 1.4.5 → 1.6.x — scope (2026-09-05)

Question: what breaks if production upgrades with a forked `AudioRecognition`? Read-only. The upgrade was not started. agent-service was not copied into this tree.

Diffed upstream `github.com/livekit/agents` at `livekit-agents@1.4.5` (reported production pin) vs `livekit-agents@1.6.10`.

## Verdict (opinion)

**v1-mini is available as a pause head** if agent-service **drops the fork**. Re-porting `breez_audio_recognition_v2.py` onto 1.6 and keeping NAMO is a large change, and it fights the model the upgrade would be for.

| Path | What we do | Effort | v1-mini real? |
|---|---|---|---|
| **A. Drop fork** | Bump SDK, pass `inference.TurnDetector(version="v1-mini")`, delete NAMO + proportional delay + ST stub from the EOU path | Turn wiring **S–M**; whole SDK bump **M–L** | **Yes** |
| **B. Re-port the fork** | Replay NAMO / proportional / ST override onto the new class | **L** on top of the bump | No — still a text detector |
| **C. Stay on 1.4.5** | Unstub Smart Turn only | **S** | No |

Path C is the pause-head finding in [RECOMMENDATION.md](../RECOMMENDATION.md). This note exists so Path A is a known cost, not an unknown.

## Scale of the change (fact)

| | 1.4.5 | 1.6.10 |
|---|---:|---:|
| `AudioRecognition` | 752 lines | **1,960 lines** |
| Commits touching that file | — | **39** |
| `AgentSession` | 1,484 lines | 2,130 lines |

v1-mini first ships in **1.6.1**; 1.6.10 adds ~176 more lines of `audio_recognition.py` fixes — **do not pin the first v1-mini tag.** The weights live in the **core SDK** (`livekit.agents.inference.TurnDetector`), not in `livekit-plugins-turn-detector` (that plugin is still the deprecated **text** model).

## What breaks

**1. The methods a fork would override are gone.** 1.4.5 callers used `start()` / `push_audio()` / `update_options()`. 1.6.10 calls `_start(stt_pipeline=..., turn_detector_stream=...)` / `_push_audio()` / `_update_options()`. A 1.4.5-style subclass **silently no-ops** after the bump — no import error, no crash, just dead turn detection.

**2. Constructor and delay API.** 1.4.5 took `min_endpointing_delay` / `max_endpointing_delay` floats. 1.6.10 takes `endpointing: BaseEndpointing` plus `interruption_detection`, `using_default_vad`, STT labels. Delays moved into `EndpointingOptions` (`min_delay` / `max_delay`). Upstream `_run_eou_detection` is still a **binary** choice (below threshold → `max_delay`, else `min_delay`); Breez's **proportional 0.2–2.0 s curve is not upstream** and would have to be re-injected.

**3. Two detector protocols now** (`voice/turn.py`): `_TurnDetector` (text, `predict_end_of_turn(chat_ctx)` — that is NAMO, still supported) and `_StreamingTurnDetector` (`stream().push_audio()` + `predict()` future — that is v1 / v1-mini). Plugging a text detector no longer needs a fork at all.

**4. The default flipped.**

| | 1.4.5 | 1.6.10 |
|---|---|---|
| Default `turn_detection` | auto: realtime_llm → vad → stt → manual | **`inference.TurnDetector()`** |
| Endpointing default | 0.5 / 3.0 s | same, or **0.3 / 2.5 s** when the detector streams |
| Default VAD if omitted | none | bundled **Silero** |

Self-hosted `start` (the EKS case) auto-selects **v1-mini**. Cloud or `dev` with LiveKit creds selects full **v1** — not a self-hosted daily path. **Trap:** bump the SDK, forget to pass a detector, and the process silently runs v1-mini. That is Path A; it is a surprise if NAMO was intended to stay.

**5. `RecognitionHooks` grew** — added `on_interruption`, `on_backchannel_confirmed`, `on_transcription_timeout`, `on_eot_prediction`, `on_agent_backchannel_opportunity`, `on_user_turn_exceeded`, and `speech_start_time` on `on_start_of_speech`. Any Breez hook object that is not a full `AgentActivity` is now incomplete.

**6. Adaptive interruption is a third, separate model.** 1.6.x `InterruptionOptions.mode = "adaptive"` classifies barge-in vs backchannel. It is **not** v1-mini and **not** VAP. Unmeasured on Arabic. The bump does not automatically provide an overlap head — **hypothesis**, not a finding.

**7. Krisp is compatible.** The streaming detector requires `vad.min_silence_duration ≥ 0.25 s`; prod Krisp is 0.45 s (as reported), so it clears. Keep passing Krisp explicitly so 1.6 does not substitute Silero. Arabic is among the 14 supported languages, with per-language thresholds overridable via `unlikely_threshold={"ar": ...}` after Gulf eval.

## License (unchanged)

[LiveKit Model License](https://github.com/livekit/agents/blob/main/MODEL_LICENSE): usable **only inside LiveKit Agents**, cannot be extracted, **cannot be used to train other models**. We already qualify at 1.4.5; 1.6.1 is when the weights ship. Local mini weights are ~108 MB resident. Our CPU bench: p50 **7.85 ms**, ~1% of a core at 15 pauses/min (M5, not EKS).

## Path A shape (opinion — not started)

```python
from livekit.agents import AgentSession, inference
from livekit.agents.voice.turn import TurnHandlingOptions

session = AgentSession(
    vad=krisp_vad,                      # keep; min_silence >= 0.25
    turn_handling=TurnHandlingOptions(
        turn_detection=inference.TurnDetector(version="v1-mini"),
        endpointing={"min_delay": 0.3, "max_delay": 2.5},   # retune after Gulf eval
        # interruption: pin mode="vad" until Arabic barge-in is measured
    ),
    # stt, llm, tts ...
)
```

Pin `1.6.10`. Stop monkey-patching `AudioRecognition`. Keep provider-mode workflows on `turn_detection="stt"` so Flux / Soniox / Inworld still own EOT. Delete NAMO, `ProportionalTurnDetector`, and the ST stub from the EOU path.

Path B, for contrast: re-apply a custom `_run_eou_detection` onto a 1,960-line class that now has a streaming detector, an STT pipeline object, adaptive interruption, transcription timeouts, and user-turn limits — **~1–2 extra engineering weeks** after the bump compiles, with real regression risk on barge-in and provider mode.

## Still unknown without an agent-service checkout

1. Is the patch `AudioRecognition = BreezAudioRecognition`, or a subclass — and which methods are overridden? (`agent-service` was not on the research machine.)
2. **Every other** LiveKit monkey-patch in agent-service. That, not EOU, decides how hard 1.6.x really is.
3. Does `AgentSession(...)` already pass `turn_detection=` (NAMO), or rely on the 1.4.5 VAD default?
