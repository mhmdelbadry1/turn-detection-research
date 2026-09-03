# VAP: before vs after optimization

## Before (do not ship) — `breez_vap/naive.py`

Every 100 ms we concatenated the new audio onto a rolling buffer of the last **N seconds** and ran the **entire** `VapGPT` forward: CPC convs + LSTM + downsample + both transformers + heads.

At N = 5 s and 10 Hz that is **2.0 CPU cores per concurrent call** on an M5 (1 thread). At 20 s: 9.2 cores. Only 5 s at **2 Hz** stayed cheap (0.40 cores) — and 500 ms to notice a barge-in is useless.

Why it is expensive: **5.79M params is small.** The work is recomputing a 250-frame window plus a CPC stack at audio resolution. Profile:

- CPC encoder **~90%** of the forward
- both transformers **~9.4%**

A perfect transformer KV cache is therefore capped at ~10% (2.00 → ~1.80 cores). That is why we did not build KV cache.

### Quantization (rejected)

| Method | Size | Fidelity | Speed |
|---|---|---|---|
| fp32 | 22.1 MB | — | baseline |
| Torch int8 (qnnpack, Linear only) | 11.9 MB | r 0.9999, 99.8% decision agree | **0.76× slower** |
| ONNX int8 | −3.4% | r 0.58, 77% agree on real audio | **broken** |
| ONNX fp32 | same | bit-exact | viable export later |

On Apple Silicon, torch int8 needs `torch.backends.quantized.engine = "qnnpack"` or you get `NoQEngine`. Still not worth it: the workload is not weight-bound. int8 never touches the CPC conv stack that dominates time.

### Naive truncation of the window

Just passing the last 1 s of **waveform** into the model does **not** match a 20 s forward (agreement ~70–77%, flat from 10 s down to 0.5 s). That implicates **lost CPC LSTM state**, not transformer length. You cannot “make it cheaper” by shortening the wav you feed.

The KTH IWSDS 2024 paper (Inoue et al.) does the correct split: **all audio through CPC**, transformers on ~1 s of features. Their 1 s result was **silence shift/hold** on a Japanese model (76.16% vs 74.20% at 20 s). It is not a claim about talk-over-TTS.

## After (ship this) — `breez_vap/streaming.py`

We implemented that split on this checkpoint. `EncoderCPC` in KTH’s repo has **no** streaming path, so the wrapper does it:

1. **Overlap-save `gEncoder` (the strided convs are not causal).** Look back 4 hops (640 samples). Hold back the last 2 hops (20 ms) until the next chunk supplies right-context. Leftover-only chunking was tried first and mismatched offline by mean abs ~0.4. Overlap-save matches to **~1e-6**.
2. **LSTM hidden per channel.** The two stereo channels **share one** `EncoderCPC`. We never set `keepHidden=True` on that shared module — that would leak channel 0 into channel 1. Hidden state is stored on `_ChannelState` and passed into `gAR.baseNet`.
3. **Causal downsample tail** (`DS_CTX=4`) so 100 Hz → 50 Hz matches the offline conv.
4. **Transformers see only the last `transformer_ctx_sec` of 50 Hz features.** Default in this package: **5.0 s** (250 frames). Research scratch still had 1.0 because that was the paper; listen tests changed it.

### Fidelity

- Encoder features vs offline full forward: max abs **3e-6**
- `p_now` vs the **same transformer window** after aligning the 20 ms holdback: **bit-exact** (r=1, 100% agree)
- 1 s vs 20 s transformer still disagrees ~18% of frames — they are not the same model. That disagreement showed up as missed barge-in on 51Talk at 1 s.

### Cost after

| Window | p50 / 100 ms step | Cores/call | Keep 10 Hz? |
|---|---:|---:|---|
| 1 s | 8.0 ms | 0.080 | yes |
| **5 s** | **18.7 ms** | **0.187** | **yes** |
| 20 s | 124.5 ms | 1.245 | **no** |

~10× vs naive 5 s (2.00 → 0.187). Still ~4× Smart Turn, with ~5× headroom on a 100 ms deadline.

### Listen (why default is 5 s, not 1 s)

Liannah vap-only sticky mute on the 51Talk clip:

- 1 s streaming: **0.10 s** (what sounded worse)
- 5 s streaming: **0.76 s** (matches offline 0.74 s)
- 20 s streaming: misses the deadline; mute number is also smeared by stride-2 decode

If 5 s starts clipping «eh» backchannels on more calls, fall back to 2 s (0.28 s liannah mute — better than 1 s, not as good as 5 s). n=1.

## Diff in one list

| | Before | After |
|---|---|---|
| CPC | recompute last N seconds of wav every step | persist LSTM + overlap-save convs |
| Transformers | same N seconds | last 5 s of features (configurable) |
| `keepHidden` | N/A (full reset every call) | **forbidden** on shared encoder; per-channel state instead |
| Holdback | none | 20 ms (do not flush live) |
| Default window | 20 s offline / 5 s naive bench | **5 s** |
| Cores/call @10 Hz | 2.0 (5 s) | 0.187 (5 s) |
| Quantization | hoped it would save us | rejected |
| KV cache | hoped it would save us | skipped; wrong 10% of the graph |

## Files

- After: `breez_vap/streaming.py` (`StreamingVap`)
- Before: `breez_vap/naive.py` (`NaiveVap`) — kept so you can A/B
- Policy unchanged: `breez_vap/policy.py`
