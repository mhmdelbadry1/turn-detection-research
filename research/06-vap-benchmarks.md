# VAP-specific benchmarks

**eot-bench is not a VAP benchmark.** There is no hosted public leaderboard for VAP (nothing like LiveKit’s FC@300ms site). The field uses a **zero-shot event protocol** defined with the model.

We have **not** re-run these. Numbers below are from the papers.

## Official protocol — Interspeech 2022

Ekstedt & Skantze, [arxiv 2205.09812](https://arxiv.org/abs/2205.09812). Labels from **per-channel VAD**, not human EOT. Code: [vap_turn_taking](https://github.com/ErikEkstedt/vap_turn_taking). Same events live in this package: `vap-runtime/third_party/vap/events.py`, `evaluation.py`.

| Task | When | Meaning |
|---|---|---|
| **S/H** Shift vs Hold | Mutual silence | Who speaks next |
| **S/L** Short vs Long | Other-speaker onset | Backchannel vs a real turn |
| **S-pred** | Current speaker still talking | Upcoming turn grab |
| **BC-pred** | Current speaker still talking | Upcoming short listener response |

Dataset: **Switchboard** (LDC). 135 dialog test / 11-fold on the rest. Metric: weighted F1. S/H is hold-heavy (majority already .843).

| Model | S/H (SHIFT F1) | S/L | S-pred | BC-pred |
|---|---:|---:|---:|---:|
| Discrete VAP (paper) | **.899** (.510) | .786 | **.733** | **.723** |
| Majority class | .843 (0) | .565 | .333 | .333 |

## Other VAP evals (same idea, different data)

**IWSDS 2024** ([arxiv 2401.04868](https://arxiv.org/html/2401.04868v1)) — Japanese Travel Agency dialogs. Balanced accuracy of next-speaker in silences > 0.25 s. This is the “1 s transformer is enough” table (**silence S/H, not talk-over-TTS**): 1 s = **76.16%**, 20 s = 74.20%.

**DualTurn** (Anyreach, [arxiv 2603.08216](https://arxiv.org/abs/2603.08216)) — re-runs VAP’s 1 s protocol on a **fixed 138-session Switchboard split**. Their VAP re-eval S/H **.843** (paper’s 11-fold was .899). DualTurn LoRA: S/H .985. Unverified here. Code: [anyreachai/dualturn](https://github.com/anyreachai/dualturn) `eval_table2`.

**OV-pred** (overlap prediction) appears in a multimodal VAP paper (IEICE 2024). Closest published metric to barge-in. Not run.

## What we measured

Silent-ch1 VAP on **eot-bench** (pause-EOT): Arabic FC@300ms **54.8%** = VAD. That does not score VAP’s job.

51Talk n=1 listen mixes are qualitative, not this protocol.

To get a real VAP number we would need Switchboard (or our own stereo + VAD) and `vap.evaluation` — not another eot-bench pass.
