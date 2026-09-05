# What it would take to improve VAP and rely on it (2026-09-05)

**Status:** scoped from papers + trainer docs. **No training run.**

VAP can be improved, and a domain-adapted VAP can become the overlap head. It should **not** replace Smart Turn until pause-EOT is measured on stereo (user + TTS), which eot-bench cannot do. The 300–500 Gulf turns planned for Smart Turn are the **wrong grain** for VAP training.

## What “rely on VAP” actually means

VAP does not output “turn complete.” It outputs who will be voiced in the next ~0.2–2 s. Two uses:

| Use | Rule | Needs fine-tune? |
|---|---|---|
| **Overlap** (TTS playing) | yield if `p_user > p_agent`, sticky | Domain gap is user-vs-**TTS**, not two humans. Yes, if we want Gulf barge-in / «آه» |
| **Pause / S/H** (both quiet) | next speaker from `p_now` | **Hypothesis.** Silent-ch1 VAP = VAD on eot-bench. Stereo VAP with a real agent history is unmeasured |

Fact from [Inoue et al., LREC-COLING 2024](https://aclanthology.org/2024.lrec-main.1036/): a VAP trained on one language **does not transfer** to another. A **single model trained on all languages together** matches the monolingual models. So “multilingual” means **mix the hours in one training run**, not train English and hope Arabic works.

## What you fine-tune (fact, trainer + paper)

Architecture: frozen **CPC** encoder (English Libri-light / Librispeech pretrain) → per-channel self-attention → **cross-attention** → two heads (256-way VAP state + 2-way VAD).

Inoue’s `train.py` flag: `--vap_freeze_encoder 1`. CPC stays frozen. You train transformers + heads.

Loss: `L = L_vap + L_vad`. Labels are **per-channel VAD**, not complete/incomplete text. The 256-way target is discretized future VA over 2 s (bins 0–200 / 200–600 / 600–1200 / 1200–2000 ms × two speakers).

Do **not** freeze the transformers if the domain is Gulf telephony vs Switchboard. Do **not** channel-flip 50/50 the way human–human VAP does: user and TTS are not interchangeable. Keep **ch0 = user, ch1 = TTS at playout**.

Optional **second** fine-tune (Inoue BC models): same encoder, replace `p_now`/`p_future` with `p_bc_react` / `p_bc_emo`. Needs backchannel tags ~500 ms ahead. That is how you might teach «آه» without Smart Turn. Japanese ERICA WoZ only so far. **Hypothesis** for Arabic.

They also tried swapping CPC for multilingual wav2vec 2.0 (MMS). Fact that they compared it; we have not rerun it. CPC-English frozen was their default and already worked in a JP/EN/ZH mix.

## How much data (fact from the multilingual paper, then a hypothesis)

They balanced each language to the smallest set:

| Language | Corpus | Hours used in the mix |
|---|---|---|
| English | Switchboard (subset of ~259 h) | **92.5 h** train / 11.5 h val |
| Mandarin | HKUST telephone | **92.5 h** / 11.5 h |
| Japanese | Travel-agency Zoom | **92.5 h** / 11.5 h |

Training recipe they published: 20 epochs, batch 8, AdamW, lr 3.63e-4, weight decay 0.001. GPU-hours **unverified** here.

**Hypothesis (not a published number):**

- **Eval:** tens of dual-track **sessions** (minutes each), held out. Not 400 isolated turns.
- **Train, first try:** on the order of **10–30 h** of Gulf user+TTS stereo, mixed with public hours (Switchboard and/or JP/ZH if licensed) so the multilingual finding applies.
- **Train, paper-scale:** ~**90 h** in-domain if matching their per-language budget.
- The Smart Turn export of **300–500 turns** is clips, not 90 h of stereo. Use it to **score** overlap/S/H, not to train VAP.

Public Arabic that is *not* user-vs-TTS: Fisher Levantine (`LDC2007S02`) is human–human telephone. Useful as extra Arabic hours in a mix (**hypothesis**); it will not teach TTS-on-ch1.

## Data preparation

Fact: [Ekstedt VAP data README](https://github.com/ErikEkstedt/VAP/blob/main/vap/data/README.md) and [Inoue train README](https://github.com/inokoj/VAP-Realtime/blob/main/train/README.md).

### 1. Sessions, not clips

Each call is one stereo file covering the **whole** session:

- 16 kHz, 16-bit WAV (not mp3)
- **ch0** = Krisp-cleaned user
- **ch1** = agent TTS **as played to the user** (playout), not as generated

If ch1 leads the ear by hundreds of ms, the model learns fake overlap. Same constraint as inference.

### 2. Per-channel VAD lists (the only required labels)

One JSON per session:

```python
[
  [[t0, t1], [t2, t3], ...],  # user voiced intervals, seconds
  [[t0, t1], ...],            # agent/TTS voiced intervals
]
```

Source: energy/VAD on each track independently (Krisp already gates the user track to zeros — those zeros **are** usable VAD). Do **not** label from STT “complete/incomplete.”

Optional listen-QC: mark backchannels («آه», «eh») on the user track as short VA segments. They stay in the VAD list; S/L evaluation uses duration, not a separate tag, unless you do a BC-head fine-tune.

### 3. Sliding CSV (what `train.py` reads)

Columns: `audio_path, start, end, vad_list, session, dataset`

- Each row = **20 s** of audio (`start`/`end` on the session file)
- Typical stride: 20 s contiguous, or 15 s with 5 s overlap (`create_sliding_window.py --duration 20 --overlap 5 --horizon 2`)
- `vad_list` is **relative to that window** and must cover **22 s** (20 s audio + **2 s horizon**). If you omit the extra 2 s, the last 2 s of every chunk have no target.

Example row shape (from Inoue):

```text
calls/abc.wav  0  20  [[[3.77,4.51],...],[[13.16,13.4],...,[20.73,22.0]]]  abc  gulf
```

Splits: **by session**, not by row (8:1:1 in their Switchboard split). Never put two windows from the same call in train and test.

### 4. Legal

Customer audio stays private. Public Switchboard/HKUST/Fisher are LDC. Candor is CC BY-NC. Inoue’s shipped `asset/` weights are **academic-only**. Fine-tuning those weights into a production checkpoint needs a license path; starting from KTH’s research dump has the same question. **Unknown — legal.**

## If this is ever scheduled (opinion, not started)

1. Keep Smart Turn as the pause head. Run VAP only while TTS plays until stereo pause-EOT is measured.
2. Export dual-track sessions (hours), disjoint from any eot-bench eval turns.
3. Build VAD JSON + sliding CSV as above. No channel flip.
4. Freeze CPC. Continue from an English (or multilingual, if licensed) VAP checkpoint. Mix Gulf hours with public EN/JA/ZH if the goal is one multilingual model.
5. Success metrics: **S/H balanced accuracy** on held-out Gulf silences; **false-yield on backchannels** vs a 300 ms duration heuristic; overlap mute time on listen clips. Not Pipecat clip accuracy, not eot-bench FC@300ms with silent ch1.
6. Only then consider a BC-head fine-tune for «آه».

## Already ruled out

- Train on 400 turns. Too small; wrong label type.
- Silent agent channel. That is VAD.
- 1 s transformer as the overlap default (51Talk).
- Expect an English checkpoint to “just work” on Arabic (LREC Table 1: cross-lingual loss jumps).
