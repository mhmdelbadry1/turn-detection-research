# 51Talk listen (n=1)

Session `656e9b45-5eeb-4fce-9295-d919fe212464`. Source tracks: `recordings/00-source-tracks/`. **n=1 — do not treat this as a benchmark.**

Overlap on the call: **7.5 s**. The long «لأنه...» user span is mostly silence + agent TTS. Isolated «آه.» is **0.82 s** of real audio.

We cannot restore TTS that was already cut in the exported agent ogg. “After” mixes only mute what is still in that file.

## Clips (timestamps on the aligned call)

| Id | Seconds | What to listen for |
|---|---|---|
| `01-open-barge` | 13–19 | User talks over the greeting |
| `02-eh-backchannel` | 43–73 | Short «eh» while agent talks — should **not** kill TTS |
| `03-filler-aah` | 120.5–130 | Isolated «آه» after a pause — pause head should skip new TTS; VAP-only does **not** |
| `04-liannah` | 154–166 | User talks over TTS («لأنه») — overlap yield |

`FULL-*` is the whole ~200 s mix (present for original, offline 20 s, and streaming 1 s).

## Folder map

| Folder | What you hear | Takeaway |
|---|---|---|
| `01-original-mix` | Customer mix, no mute | Baseline |
| `02-offline-vap-20s` | Full 20 s VAP forward, vap-only sticky mute | First mix that **sounded** like the overlap yield we wanted |
| `03-offline-twohead-v1mini` | VAP overlap + v1-mini pause deny | Skips «آه»; license-locked head |
| `04-offline-twohead-smartturn` | VAP overlap + Smart Turn pause deny | Skips «آه» with the shippable pause head |
| `05-streaming-1s` | Deployable streamer, **1 s** transformer | Overlap on liannah **weaker** (0.10 s mute vs 0.74 s offline) |
| `06-streaming-5s-recommended` | Same streamer, **5 s** window | Liannah mute **0.76 s** — matches offline. This is the default. |
| `07-streaming-20s` | 20 s window | Does not keep 10 Hz (124 ms/step). Do not ship. |

Inside streaming folders:

- `vaponly-*` — VAP sticky mute only
- `twohead-st-*` — VAP overlap + Smart Turn pause

## Liannah mute seconds (vap-only, sticky)

| Transformer window | Sticky mute |
|---|---:|
| 1 s | 0.10 s |
| 5 s | **0.76 s** |
| Offline 20 s | 0.74 s |
| 20 s streaming | 0.28 s (coarser decode; do not over-read) |

«آه» two-head mute stays ~0.5 s at every window — that is Smart Turn on a pause, not the transformer.
