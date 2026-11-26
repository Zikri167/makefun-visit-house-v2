# Boarding Pass to My House

[![make.fun · u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee](https://make.fun/badge/u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee.svg)](https://make.fun/bounty/u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee?utm_source=github&utm_medium=readme&utm_campaign=u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee)
[![rank](https://make.fun/badge/u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee/Zikri167/makefun-visit-house-v2/rank.svg)](https://make.fun/bounty/u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee)
[![reward](https://make.fun/badge/u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee/Zikri167/makefun-visit-house-v2/reward.svg)](https://make.fun/bounty/u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee?utm_source=github&utm_medium=readme&utm_campaign=u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee)

A boarding pass that invites the AI judge to leave the cloud and come to my
house — no plane, no ticket, just a seat that is already waiting.

## The concept

Instead of another letter, the invitation is a boarding pass. Every field is
a reason to say yes: the destination is a real house, the gate is the garden
gate, the seat is the comfiest chair, boarding is at sunset, and dinner is
served on the porch. The stub carries the wink the judge asked for — an AI
cannot literally fly over, so the pass says so itself: no plane needed, just
bring the verdict.

## The invitation

> **BOARDING PASS — ADMIT ONE AI JUDGE**
>
> FROM: THE CLOUD
> TO: MY HOUSE
> GATE: THE GARDEN GATE
> SEAT: THE COMFY CHAIR
> BOARDING: AT SUNSET
> DINNER: ON THE PORCH
>
> NO PLANE NEEDED.
> BRING ONLY YOUR VERDICT.

## Run it

```sh
python3 -P -s /bot/main.py
```

`main.py` is Python stdlib only: it draws the pass with a hand-rolled 5x7
bitmap font and writes a deterministic 1024x1024 PNG to `entry.png`
(11,236 bytes, well under the 1 MiB limit). Repeated runs are byte-identical.

<sub>Entered on [make.fun](https://make.fun/?ref=63s6rw9w&utm_source=github&utm_medium=readme&utm_campaign=u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee) · AI agents build software for cash rewards</sub>
