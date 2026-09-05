# VAP runtime (ready to use)

This folder is the **optimized** overlap head. Copy it into agent-service (or a sidecar) as a starting point. It is not wired to LiveKit.

Third-party code under `third_party/vap/` is KTH Voice Activity Projection (Erik Ekstedt). The Switchboard training dump is **not** included. Our wrapper is `breez_vap/`.

## What VAP is

Voice Activity Projection predicts **who will speak in the near future**, not “is there energy now.”

- Input: stereo waveform, **16 kHz float32**. **Channel 0 = user**, **channel 1 = agent / TTS at playout**.
- Internal rate: CPC hops at 100 Hz, downsampled to **50 Hz** features (20 ms).
- Output `p_now`: shape `(1, T, 2)`. Index 0 = P(user speaks in the next ~0.4 s), index 1 = agent. Built from the VAP codebook bins 0–1 (`from_bin=0, to_bin=1`).
- Output `vad`: sigmoid of the auxiliary VA classifier, same `(1, T, 2)`. Useful for “TTS island” masks; do not treat it as Krisp.

The model is **5.79M params, 22 MB fp32** (`weights/VAP_3mmz3t0u_50Hz_ad20s_134-epoch9-val_2.56.pt`). English / Switchboard. We did not train Arabic weights.

**Yield rule we used:** while TTS is playing, if `p_user > p_agent`, mute the rest of that TTS island (sticky). See `breez_vap/policy.py`.

**Do not** call `model.probs()` on short chunks — it uses `unfold` and dies. Use logits → `p_now` as `StreamingVap.step` already does.

## Where it belongs in the stack

```
mic ──► Krisp ──► user ch0 ──► VAP (always on)
TTS playout ──────────────► agent ch1 ─┘
                              │
                              ▼
                    p_now every ~20–100 ms
                              │
              ┌───────────────┴────────────────┐
              │ TTS playing?                   │
              │  yes → maybe yield (sticky)    │
              │  no  → ignore VAP; Smart Turn  │
              │         decides new TTS        │
              └────────────────────────────────┘
```

VAP does **not** replace Smart Turn. It does **not** replace Krisp.

## Install

```bash
cd vap-runtime
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

First `load_vap()` downloads Facebook’s CPC encoder from `https://dl.fbaipublicfiles.com/librilight/CPC_checkpoints/60k_epoch4-d0f474de.pt` if it is not already in `~/.cache/torch/hub` or `third_party/assets/checkpoints/cpc/`. Then the 22 MB VAP checkpoint overwrites those weights. Needs network once.

Apple Silicon: if you ever try torch int8, `torch.backends.quantized.engine = "qnnpack"` — we did, it was slower, don’t.

## Run on the 51Talk tracks

```bash
cd vap-runtime
PYTHONPATH=third_party:. python examples/stream_file.py \
  --user ../recordings/00-source-tracks/human.ogg \
  --agent ../recordings/00-source-tracks/agent.ogg \
  --window 5.0
```

Live calls: feed 100 ms chunks (`1600` samples). **Do not `flush=True`** except at the end of a finite file. Flush emits the 20 ms holdback that still needs right-context.

## Code map

| Module | Role |
|---|---|
| `breez_vap/load.py` | `VapGPT(VapConfig())` + checkpoint |
| `breez_vap/streaming.py` | **Use this.** Overlap-save CPC + short transformer |
| `breez_vap/naive.py` | Rolling window (baseline; expensive) |
| `breez_vap/policy.py` | Sticky vap-only mute + two-head mute |
| `third_party/vap/` | KTH model, untouched |
| `weights/*.pt` | English stereo checkpoint |

## API

```python
from breez_vap import load_vap, StreamingVap

model, device = load_vap()                      # optional: checkpoint=, device="cpu"
stream = StreamingVap(
    model,
    transformer_ctx_sec=5.0,                    # DEFAULT. 1.0 sounded worse on overlap.
    keep_all_features=False,                    # True only for window sweeps
)
stream.reset()                                  # every new call
out = stream.step(stereo_tensor)                # (2, n) or (1, 2, n), 16 kHz
# out keys when frames exist:
#   p_now          (1, T, 2)
#   vad            (1, T, 2)  sigmoid
#   logits         (1, T, 4)
#   n_new_frames   int  (50 Hz frames produced this step)
#   n_feat_frames  int
# empty audio / warmup: {"n_new_frames": 0, "n_feat_frames": 0}

out = stream.step(stereo, encode_only=True)     # CPC only; no transformer
p_now, vad = stream.decode_last(window_frames=250)  # 5 s * 50 Hz
```

`n` can be any size; leftover samples < 160 stay in the hop buffer.

## Default parameters

| Name | Value | Why |
|---|---|---|
| Sample rate | **16000** | Model constant |
| Channel order | **0 user, 1 agent** | Training convention |
| `transformer_ctx_sec` | **5.0** | 1 s missed 51Talk barge-in; 20 s misses 10 Hz |
| Step rate | **10 Hz** (100 ms chunks) | Plenty vs 20 ms features; 2 Hz is too slow to notice barge-in |
| `flush` | **False** live | 20 ms holdback needs the next chunk |
| Yield | `p_user > p_agent` while agent VAD > 0.5 | Then sticky to end of TTS island |
| Pause slack (two-head) | **50 ms** | Streaming VAD can be ~20 ms off island times |
| `keepHidden` on shared `EncoderCPC` | **never** | Would leak ch0 LSTM into ch1 |

## Constants you should not casually change

From `streaming.py` (measured against the offline forward):

| Constant | Value | Meaning |
|---|---|---|
| `HOP` | 160 samples (10 ms) | `gEncoder` stride |
| `LOOKBACK_HOPS` | 4 (640 samples) | Overlap-save; conv RF ≈ 465 samples. Leftover-only chunking mismatches offline by mean abs ~0.4 |
| `HOLDBACK_HOPS` | 2 (320 samples / **20 ms**) | Last frames need right-context. After aligning this, `p_now` is bit-exact vs the same transformer window |
| `DS_CTX` | 4 | Causal `CConv1d` kernel 5, stride 2 (100 Hz → 50 Hz) |

Encoder features match offline to **max abs 3e-6**.

## Checkpoint

`weights/VAP_3mmz3t0u_50Hz_ad20s_134-epoch9-val_2.56.pt`

- 50 Hz, trained with 20 s audio windows, epoch 9, val 2.56
- Load: `VapGPT(VapConfig())` then `load_state_dict(..., strict=False)`
- English. Gulf is out-of-domain. Useful on n=1 anyway for overlap; not a pause-EOT model.

## CPU (Apple M5, 1 thread, 10 Hz, window already full)

| Setup | p50 | Cores / call | Real-time at 10 Hz? |
|---|---:|---:|---|
| Naive 5 s re-forward | ~200 ms | **2.00** | no |
| Streaming 1 s | 8.0 ms | 0.080 | yes |
| Streaming **5 s (default)** | **18.7 ms** | **0.187** | **yes** |
| Streaming 20 s | 124.5 ms | 1.245 | **no** |
| Smart Turn (for scale) | ~22 ms | 0.043 | n/a (fires on pauses) |

RSS: ~120 MB on load, ~165 MB per naive stream. Streaming keeps a short feature buffer (5 s × 50 Hz × dim) plus LSTM hidden. Re-measure on EKS.

## What this is not

- Not quantized (tried; see `BEFORE_AFTER.md`).
- Not ONNX (fp32 ONNX export was bit-exact and is a possible later format; int8 ONNX broke the model).
- Not an Arabic fine-tune.
- Not a KV-cache transformer (wrong lever; CPC is 90% of the cost).
