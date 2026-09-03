# From the beginning

How we got here. Dates are 2026. Claims marked **fact** were measured or read from source; **as reported** came from Omar’s handoff and were not re-checked against the cluster in this work; **opinion** is a recommendation.

## What production does today (as reported, 2026-09-01)

Turn detection in agent-service is **NAMO alone**, not a NAMO + Smart Turn hybrid. Smart Turn was stubbed in Feb 2026 (`b860211b`) to save CPU. The inference server hardcodes `{"eou_probability": 0.5}`. Override logic in agent-service is dead.

NAMO v1 Multilingual is **text-only**: it scores the STT transcript, never hears audio. Published standalone accuracy: 84.9% Arabic (weakest of 23 languages except Bengali), 90.9% English. The Arabic-only NAMO variant is worse (79.7%). Because it never hears audio, every Arabic STT error becomes a turn-taking error.

Krisp VAD stays in any design. Min-silence in prod is 0.45 s. Pause classifiers fire **after** VAD reports silence.

Provider mode (the STT vendor decides end-of-turn) already works and was out of scope.

## Why look at all (as reported + then measured)

Customers barge in, fill, and hold. NAMO cuts them off or waits too long. The strategic replacement on the table was **Smart Turn v3.2** (audio, BSD-2, 8 MB ONNX, fine-tunable). The accuracy winner in public numbers was **LiveKit v1-mini**, license-locked to LiveKit Agents 1.6.x (we are on 1.4.5).

Public bench of record: **eot-bench** (LiveKit, Apache-2.0). Metric: false-cutoff rate at a 300 ms latency budget. We reproduced it.

## What we ran, in order

1. **2026-09-02 — Reproduce eot-bench** (Smart Turn + v1-mini, Arabic + English). Matched the published leaderboard exactly. See `02-eot-bench-numbers.md`.
2. **NAMO on the same harness** (first number). Worse than doing nothing (VAD baseline).
3. **Last-token text gates** on lagged STT. Same structural problem as NAMO; they did not beat audio-only.
4. **One Breez 51Talk call** with separate human / agent tracks (n=1). Overlap 7.5 s. Isolated «آه.» is 0.82 s of real audio. Public eot-bench does not score overlap — it only scores user-silence EOT. This call’s pain is different.
5. **VAP (Voice Activity Projection)** offline on that stereo pair. First listen mixes (folder `02-offline-vap-20s`) sounded like the overlap yield we wanted. VAP-only still started TTS after «آه»; adding a pause head (Smart Turn or v1-mini) skipped it.
6. **Score-fusion of VAP + Smart Turn on eot-bench.** Hurt Arabic. Do not blend.
7. **CPU of naive VAP.** 1–2 cores per concurrent call. Quantization does not fix it. Cost is the CPC encoder (~90%), not the transformers.
8. **Streaming VAP** (this package’s `vap-runtime`). ~10× cheaper. 1 s transformer sounded worse on overlap; **5 s recovers it** and still holds 10 Hz.

## What we did not do

- No Smart Turn or VAP training.
- No 300–500 Gulf export (blocked).
- No EKS CPU re-measure.
- No duration-heuristic baseline for overlap (ignore short user bursts during TTS).

## Papers / products (pointers, not copies)

- eot-bench: https://github.com/livekit/eot-bench
- Smart Turn v3.2: Pipecat / LiveKit ONNX pause classifier
- NAMO: https://huggingface.co/videosdk-live/Namo-Turn-Detector-v1-Multilingual
- VAP: Ekstedt & Skantze, Interspeech 2022, https://arxiv.org/abs/2205.09812 — code https://github.com/ErikEkstedt/VoiceActivityProjection
- Real-time VAP: Inoue et al., IWSDS 2024, https://arxiv.org/html/2401.04868v1
