# CPU cost (pause heads)

**Fact.** Apple M5, arm64, 10 cores, 16 GB, macOS, Python 3.12. **Does not transfer to prod EKS.** Re-run on the agent-service box before a capacity plan.

We have not done that from this research machine: no `kubectl`, no cluster credentials, and the original brief kept the benches off prod. Pause-head latency (7–25 ms) does not need EKS to unstub Smart Turn. EKS matters for **VAP packing** (cores per concurrent call) and for re-checking the Feb 2026 CPU-stub on Linux nodes.

Pause classifiers fire once per VAD silence (~10–20/min). Method: warmup 10, then N=200 single inferences; sustained 15 inferences/min for 90 s; 100% = one full core.

Accuracy numbers in this package used eot-bench’s default `smart-turn-v3.2-gpu.onnx` (**30.9 MB**), executed on **CPU** (no CUDA). The brief’s “8 MB” is a **different file** (`smart-turn-v3.2-cpu.onnx`, 8.3 MB). We timed both. We have **not** re-scored eot-bench on the 8.3 MB file.

| Model | Weights | p50 | p95 | CPU% @ 15/min | Disk |
|---|---|---:|---:|---:|---:|
| NAMO v1 Multilingual | `model_quant.onnx` | **7.05 ms** | 8.75 ms | 3.8% | **294.7 MB** |
| Smart Turn v3.2 | `gpu.onnx` on CPU | **22.3 ms** | 27.44 ms | 4.3% | 30.9 MB |
| Smart Turn v3.2 | `cpu.onnx` | 24.5 ms | 30.4 ms | 3.7% | **8.3 MB** |
| LiveKit v1-mini | bundled | **7.85 ms** | 8.08 ms | 1.0% | (not a single ONNX we sized) |

None of these is slow versus a **300 ms** conversational budget. Dead air is the wait policy, not these milliseconds. At 15 pauses/min every row is idle (~1–4% of one core). **CPU is not a reason to keep NAMO.**

v1-mini is the tightest (p50 ≈ p95 ≈ 8 ms). Smart Turn had rare spikes (~85 ms gpu-named, ~72 ms cpu-named).

## VAP is a different unit

VAP runs **continuously**, not once per pause. Naive 5 s window: **2.0 cores per concurrent call**. Streaming 5 s (this package): **0.187 cores/call** at 10 Hz. See `vap-runtime/BEFORE_AFTER.md`.
