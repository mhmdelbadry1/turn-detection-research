# Smart Turn fine-tune — scope (2026-09-05)

Brief item 5: **estimate** data effort, GPU hours, expected gain. **Do not train.** We did not train. No GPU job, no prod audio, no 41 GB download.

Read from source: [pipecat-ai/smart-turn](https://github.com/pipecat-ai/smart-turn) `train.py`, `train_modal.py`, and the data-contribution guide (clone 2026-09-05).

## Verdict (opinion)

Fine-tune is the **second** ship, not the first. Unstub stock v3.2 now — it already beats NAMO on Arabic by ~25 pp. Fine-tune when a **Gulf train set** exists that is **disjoint** from the 300–500 eval turns.

Do **not** use v1-mini scores as labels. Its Model License forbids training other models on its outputs.

## What their training script actually is (fact)

| Knob | Value |
|---|---|
| Start weights | **`openai/whisper-tiny`** — *not* the published v3.2 ONNX |
| Head | New attention-pool + MLP, random init |
| Train set | `smart-turn-data-v3.2-train` — **270,946** clips, **41.4 GB** |
| Test set | `smart-turn-data-v3.2-test` — **31,527** clips |
| Epochs / batch | **4** / **384** train, 128 eval, no grad accumulation |
| LR | 5e-5, cosine, warmup 0.2, weight decay 0.01 |
| Input | last **8 s** of 16 kHz mono → Whisper log-mel `(80, 800)` |
| Label | `endpoint_bool` (complete = 1 / incomplete = 0) |
| Export | FP32 ONNX → **static int8** (1,024 calibration clips) |
| Cloud recipe | `train_modal.py`: **NVIDIA L4**, 32 GB RAM, 8 CPU, 24 h timeout |
| Gotcha | `do_training_run` **raises without `WANDB_API_KEY`** |

**This is a full retrain from Whisper Tiny, not "continue from v3.2."** Pipecat publishes ONNX only. A true continued fine-tune needs their unpublished `Trainer` checkpoint, or our own first export of `final_model/`.

Optimizer steps on the public set: `270,946 × 0.9 / 384 × 4 ≈ **2,540**`.

## GPU hours (unverified — we did not run it)

| Job | Bound |
|---|---|
| Full public retrain, match CONFIG, L4 | **~3–12 GPU-hours** |
| Same on a T4 16 GB | longer; batch 384 may OOM (community used 32 × grad-accum 12) |
| Mix 2–5k Gulf clips into the public set, 4 epochs | **same ~3–12 h** — dataset size barely moves |
| Continue 1 epoch, Gulf-only ~2k clips | **≪ 1 GPU-hour** — blocked on the missing checkpoint |
| 400-clip overfit | minutes. **Do not.** |

Wall clock is dominated by the 41 GB download and on-demand FLAC decode, not by the 8M-param forward. Their own 24 h Modal timeout is the tell.

**Money is not the constraint.** An L4-hour is single-digit USD. **Labelling time is the cost.**

## Data prep (opinion, effort after Omar's export)

Format is fixed by the guide: mono **FLAC**, 16-bit, 16 kHz, **one speaker**, **≤ 16 s**, target **50:50** complete/incomplete, each clip ending in **~200 ms silence** (because ST only runs after VAD stop). Incomplete must end on a filler / connective / hanging prosody — **never mid-word**.

Same audio as the eval set, **different cut**:

| From one user turn | Clip | Label |
|---|---|---|
| Up to each **non-final** silence ≥ 100 ms | incomplete | speaker continues |
| Up to the **final** silence | complete | finished thought |

| Step | Effort |
|---|---|
| Silence spans | shared with the eot-bench eval set |
| Slice FLACs + JSONL metadata | ~1 engineer day |
| Listen-QC ~20% + every Arabic filler edge case | ~1 day |
| Legal / consent for **training** use (stricter than private eval) | **unknown — Omar** |
| **Total once export exists** | **~2–4 engineer days** + legal |

Two hard rules: **300–500 turns is an eval set** (≈1k clips — tiny next to 271k), and Breez customer audio **stays private** — BSD-2 covers weights we train, not a right to publish callers on Pipecat's public HF.

Target for a real train slice (**hypothesis**): ≥2k complete + ≥2k incomplete Gulf telephony clips, 50:50, held out from eval.

## Expected gain (hypothesis, not fact)

No public number exists for "Arabic telephony fine-tune → Δ FC@300ms." Anyone quoting one is guessing.

Pipecat's own [v3.2 clip benchmark](https://huggingface.co/pipecat-ai/smart-turn-v3/blob/main/benchmarks/smart-turn-v3.2-gpu.md) (n=31,527): overall **93.71%**, English 94.71%, **Arabic 89.12%** (n=947, FPR 7.07%) — 4th-worst of 23 languages.

**That 89% is not our 39.2%.** Theirs is isolated complete/incomplete clips; ours is streaming false-cutoff at a 300 ms budget. Do not put them in the same column.

Arabic is ~3% of their **test** set. If train is similar, public Arabic is on the order of ~8k clips — **unverified**, we did not count the parquet.

| Outcome for a 2–5k Gulf mix-in | Why |
|---|---|
| **0–3 pp** better | public Arabic + cafe noise already near our domain |
| **5–10 pp** better | real gap is telephony, Gulf fillers, Krisp-gated zeros |
| **Worse** | trained on the eval set, overfit a few hundred clips, or drowned by the TTS-heavy public mix |

On present evidence a fine-tune is **not** guaranteed to catch v1-mini (24.4%). It is how we try to close that gap **without** the 1.6.x upgrade.

Success metric if we ever train: **FC@300ms on the held-out Gulf set** vs stock v3.2 on the same set. Not clip accuracy.

## Recipe when it is scheduled (opinion, do not run now)

1. Unstub stock v3.2 on 1.4.5. Keep Krisp.
2. Export **eval** (300–500) and a **larger disjoint train** split.
3. Slice FLACs, 50:50, listen-QC.
4. Either get Pipecat's v3.2 `Trainer` checkpoint, or retrain from `whisper-tiny` with `datasets_training = [public v3.2-train, private Gulf]`.
5. Export ONNX the same way (`do_quantization_run`); re-bench CPU — expect ~22 ms still.
6. Score the Gulf eval **and** public eot-bench `ar`, so we do not wreck general Arabic.

## Not done

No `trainer.train()`. No Modal job. No language histogram of the train set. No legal review of training on Breez calls.
