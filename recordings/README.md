# Recordings

**Internal.** 51Talk caller audio. Do not publish.

All “after” files are the **customer mix with TTS muted** where the policy says yield. They are not stereo VAP input. Stereo input is folder `00`.

Play **before** from `01`, then the matching **after** from the folder you care about. Same clip names (`01-open-barge`, …).

## Folders

| Folder | Contents |
|---|---|
| `00-source-tracks/` | `human.ogg`, `agent.ogg`, `audio-align.json` — feed these to VAP |
| `01-original-mix/` | Mixed as heard. `*-before.wav` + `FULL-before.wav` |
| `02-offline-vap-20s/` | First good-sounding overlap yield (full 20 s VAP, vap-only) |
| `03-offline-twohead-v1mini/` | VAP overlap + v1-mini pause (skips «آه»; license-locked) |
| `04-offline-twohead-smartturn/` | VAP overlap + Smart Turn pause (skips «آه»; shippable pause head) |
| `05-streaming-1s/` | Optimized runtime, 1 s window — **weaker overlap** |
| `06-streaming-5s-recommended/` | Same runtime, 5 s — **use this** |
| `07-streaming-20s/` | 20 s window — too slow for 10 Hz |

Streaming folders have `vaponly-*` (VAP mute only) and `twohead-st-*` (VAP + Smart Turn). No `FULL` mix at 5 s / 20 s (we only rendered the four clips).

## Clips

| File prefix | Call time | Listen for |
|---|---|---|
| `01-open-barge` | 13–19 s | Talk-over on the greeting |
| `02-eh-backchannel` | 43–73 s | Short «eh» — should keep TTS |
| `03-filler-aah` | 120.5–130 s | Isolated «آه» — two-head should not start new TTS; vap-only still does |
| `04-liannah` | 154–166 s | Talk-over. Compare `05` vs `06` vs `02` |

A/B that matters most:  
`02-offline-vap-20s/04-liannah-after.wav`  
vs `05-streaming-1s/vaponly-04-liannah-after.wav`  
vs `06-streaming-5s-recommended/vaponly-04-liannah-after.wav`
