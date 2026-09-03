# Notices

## Voice Activity Projection (third_party/vap)

Copyright (c) Erik Ekstedt / KTH Speech, Music and Hearing.
Source: https://github.com/ErikEkstedt/VoiceActivityProjection

CPC encoder components are derived from Facebook Research CPC_audio:
https://github.com/facebookresearch/CPC_audio

The English stereo checkpoint `VAP_3mmz3t0u_50Hz_ad20s_134-epoch9-val_2.56.pt`
is the example weight from that project. First load may download
`60k_epoch4-d0f474de.pt` from Facebook’s public CPC URL.

## Recordings

`recordings/` includes a HeyBreez / 51Talk customer call used internally for
research. Not for public distribution.

## Breez wrapper

`breez_vap/` (streaming overlap-save CPC, policy, examples) is Breez research
code, 2026-09.
