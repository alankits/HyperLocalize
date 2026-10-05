# ADR 0012: Deployment: Docker Compose on a laptop, with a demo-resilience plan

**Status:** Accepted (approved by the user 2026-10-05). History: proposed 2026-10-05; revised 2026-10-05 for the zero-budget Q4 answer. The Q18 default (local laptop demo) was accepted with it.
**Source:** `docs/PHASE0_DISCOVERY.md` §6.11; Q2, Q4, Q8 answers

## Context

Q4 (revised): **zero budget**, no local GPU, free tiers and open-source models only. Kaggle Notebooks (free, about 30 GPU hours/week) may run GPU-heavy steps in batch (ADR 0019). Several models run **on the laptop's CPU** (faster-whisper, IndicTrans2, MMS-TTS or Indic Parler-TTS, possibly IndicF5), so the laptop's RAM and CPU are now a real constraint. The team has little DevOps experience (Q2). The final evaluation includes a **live demo** (Q8), which depends on internet access and on third-party API availability, and that is the biggest live-demo risk.

## Options Considered

| Criterion | **Docker Compose on a laptop** | Single cloud VM with Docker Compose | Managed platform (PaaS) |
|---|---|---|---|
| Effort | **Low** | Medium (SSH, firewall, TLS) | Medium |
| Cost | ₹0 | Ongoing VM cost (not allowed: zero budget) | Ongoing (not allowed) |
| Exposure of sensitive media to the internet | **None** | Needs hardening | Needs configuration |
| Works without venue Wi-Fi | **Yes, with the all-local chain** (context-free translation) | No | No |

## Decision

- **Docker Compose** with four services: `web` (Django), `worker-synthesis` and `worker-default` (`manage.py run_worker --lane …`, ADR 0003; the synthesis worker hosts the local inference subprocess), and `db` (PostgreSQL). Docker's memory limit must be set high enough for the largest local model; that limit is measured **inside this stack** in spike M6. Model weights are stored in a named volume, downloaded once with a Hugging Face token for the gated models; they are never committed to git. Media is in a named volume. Secrets come from a `.env` file, which is git-ignored, with a committed `.env.example`.
- One-command start, documented in the README.
- The demo runs on a team laptop **[CONFIRMED, Q18]**. A cloud VM is future scope.
- **Demo-resilience plan:**
  1. A `check_providers` management command checks reachability, API keys, remaining **free quotas** (including Kaggle GPU hours) and the local model cache before the demo.
  2. A completed "golden" project with all artefacts is prepared in advance, so review, approval, export, audit and evidence can be shown without calling any API.
  3. A screen recording of the full live run, including mid-job revocation, made in the week before.
  4. A mobile-hotspot fallback for internet access.
  5. **Demo plan for slow CPU synthesis.** **`docs/SPIKE_PLAN.md` §6 is the authoritative definition**, and spike rule 6 picks the plan:
     - **Plan A:** everything live on the laptop.
     - **Plan B:** cloned-voice previews are pre-rendered on Kaggle (only if ADR 0019 is adopted); live regeneration uses the stock voice.
     - **Plan C:** cloned-voice previews are rendered overnight on CPU.
     - **Plan D:** cloned voice only for the one short revocation scene; stock voice everywhere else.
     - **Stock-only:** if cloned voice fails rule 4.

     In every plan, revocation is demonstrated mid-job (ADR 0006 §9 gives the main path and the agreed fallback).
  6. **Offline all-local fallback** *(added after review)*: faster-whisper → IndicTrans2 → MMS-TTS runs with **no internet at all**. The pipeline can be shown live even if venue Wi-Fi fails; the translation is context-free, and the UI marks it as such.
  7. **Demo reset fixture:** purge deletes the reference clip, so every rehearsal consumes the demo state. `manage.py demo_reset` restores a database and media snapshot of the prepared project (team-only data) before each rehearsal and the final demo.
  8. **Re-review step in the script:** after revocation, the fallback scene needs a Reviewer's acceptance before the Manager approves. The revoked speaker is confined to **one short scene**, so this takes about a minute.
  9. **Check free quotas before the demo:** `check_providers` reports the remaining free-tier and Kaggle GPU quota, and the team switches chains to the free alternatives the day before if any quota is low.
  10. **If a fallback is used, it is announced.** Pre-generated content is never presented as live, and mocks are never presented as real (CLAUDE.md §2).

## Consequences

- **+** Minimal operations work; nothing sensitive is exposed to the internet.
- **+** The demo survives a provider or network outage, honestly.
- **−** No remote access for evaluators between reviews. Acceptable.
- **−** Not production deployment. It is described as a demo deployment only.
- **Viva in 2 minutes:** "Four containers on a laptop, using free hosted AI where allowed and local open-source models otherwise. If the network fails we switch to the all-local chain. We have a provider and quota check, a reset fixture, a completed golden project and a recorded run, and we say openly when we use any of them."
