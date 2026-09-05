# Silent-ch1 VAP on eot-bench (the 54.8%)

**54.8% is false-cutoff @ 300 ms, not accuracy.** Lower is better. It is **the same number as the VAD baseline** because, on Arabic, the harness **did not use VAP’s scores**.

## Setup

eot-bench audio is **user-only**. VAP wants stereo. Adapter `eot-bench/eot_harness/vap_adapter.py`:

1. User wav → **channel 0**
2. Zeros → **channel 1** (KTH `add_zero_channel`)
3. Run the English Switchboard checkpoint
4. `p_eot` = mean of `p_now` **channel 1** over the last 200 ms  
   (“would the imaginary other speaker start in the next ~0.4 s?”)

Transcripts unused. Score point 0.2 s. Prefix ≤ 20 s.

That is a **pause-EOT hack**. On 51Talk we fed **real** agent audio on ch1. Different experiment.

## Why 54.8%

eot-bench sweeps threshold × silence delay × timeout, then picks the point with mean latency ≤ 300 ms and the fewest false cutoffs.

Arabic VAP operating point from the report:

- threshold **0.000** (every score “fires”)
- action_delay **0.300 s**
- detect **100%**

That is “wait 300 ms of silence, always cut” — the **VAD timer**. VAD baseline Arabic FC@300ms is also **54.8%**.

English: threshold 0.19, FC **50.2%** vs VAD **55.6%** — scores did a little; still near a silence timer, far behind Smart Turn.

## What it means

With no agent channel, “will the other speaker start?” is mostly **how long the user has been quiet**. The timer already knows that. This does **not** measure barge-in.
