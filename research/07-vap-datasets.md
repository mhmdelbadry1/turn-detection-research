# Which dataset to test VAP on

None of Switchboard / Fisher / Candor is the Breez product test (Gulf user vs **TTS**). They are human–human, almost all English. Pick by *goal*:

| Goal | Dataset |
|---|---|
| Reproduce the VAP paper (S/H, S/L, S-pred, BC-pred) | **Switchboard** — this *is* the official test set |
| Overlap / interruption, clean stereo | **Candor** — best of the three |
| Train a bigger English VAP | Switchboard + **Fisher English** (SIGDIAL 2022). Not needed to *test*. |
| Decide if VAP helps Breez | **Our dual-track calls** |

**Switchboard:** LDC, English telephone, ~260 h, two channels. Our checkpoint was trained in this world. Paid license.

**Fisher:** larger English telephone (LDC). Training hours, not the canonical test. **Fisher Levantine Arabic is a different corpus** — not what VAP papers used.

**Candor:** 1,656 English Zoom calls, ~850 h, 32 kHz stereo (one speaker per channel), ~48% of transitions overlap. CC BY-NC + application. VAP papers in 2025 do use it (audio-only S/H ~79% balanced acc vs ~65% on Switchboard in the same study). Closer to WebRTC; still two humans.

**Implication:** Fisher is extra English hours, not a required test set. Switchboard only if a paper-comparable number is needed. Candor if a public overlap stress test is needed. The in-domain measurement is still dual-track `human.ogg` + `agent.ogg`.
