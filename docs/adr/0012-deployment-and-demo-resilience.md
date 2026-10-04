# ADR 0012: Deployment: Docker Compose on a laptop, with a demo-resilience plan

**Status:** Proposed (2026-10-05; revised 2026-10-05 for the zero-budget Q4 answer). Not yet approved. It includes a proposed default for Q18 (local laptop demo).
**Source:** `docs/PHASE0_DISCOVERY.md` §6.11; Q2, Q4, Q8 answers

## Context

Q4 (revised): **zero budget**, no local GPU, free tiers and open-source models only. Kaggle Notebooks (free, about 30 GPU hours/week) may run GPU-heavy steps in batch (ADR 0019). Several models run **on the laptop's CPU** (faster-whisper, IndicTrans2, MMS-TTS or Indic Parler-TTS, possibly IndicF5), so the laptop's RAM and CPU are now a real constraint. The team has little DevOps experience (Q2). The final evaluation includes a **live demo** (Q8), which depends on internet access and on third-party API availability, and that is the biggest live-demo risk.

## Options Considered

| Criterion | **Docker Compose on a laptop** | Single cloud VM with Docker Compose | Managed platform (PaaS) |
|---|---|---|---|
| Effort | **Low** | Medium (SSH, firewall, TLS) | Medium |
| Cost | ₹0 | Ongoing VM cost (not allowed: zero budget) | Ongoing (not allowed) |
| Exposure of sensitive media to the internet | **None** | Needs hardening | Needs configuration |
| Works without venue Wi-Fi | Only for already-generated content | No | No |

## Decision

- **Docker Compose** with three services: `web` (Django), `worker` (`manage.py run_worker`, which also hosts the local inference subprocess), and `db` (PostgreSQL). Model weights are stored in a named volume, downloaded once with a Hugging Face token for the gated models; they are never committed to git. Media is in a named volume. Secrets come from a `.env` file, which is git-ignored, with a committed `.env.example`.
- One-command start, documented in the README.
- The demo runs on a team laptop **[PROPOSED default for Q18]**. A cloud VM is future scope.
- **Demo-resilience plan:**
  1. A `check_providers` management command checks reachability, API keys and the remaining budget before the demo.
  2. A completed "golden" project with all artefacts is prepared in advance, so review, approval, export, audit and evidence can be shown without calling any API.
  3. A screen recording of the full live run, including mid-job revocation, made in the week before.
  4. A mobile-hotspot fallback for internet access.
  5. **Demo plan for slow CPU synthesis** (the spike decides, `docs/SPIKE_PLAN.md` §6):
     - **Plan A:** IndicF5 on CPU is fast enough for live single-scene regeneration.
     - **Plan B:** all cloned-voice previews for the demo project are produced **in advance on Kaggle** (and imported through the consent checks). Live regeneration uses the fast **stock voice** on CPU. A cloned-voice regeneration is shown being **dispatched** to Kaggle, with its result shown later if it arrives within the demo, and it is announced as such. The **revocation demo always uses a local CPU cloned-voice job**, because slow is fine for that, and killing the subprocess shows the stop within seconds.
  6. **Check free quotas before the demo:** `check_providers` reports the remaining free-tier and Kaggle GPU quota, and the team switches chains to the free alternatives the day before if any quota is low.
  7. **If a fallback is used, it is announced.** Pre-generated content is never presented as live, and mocks are never presented as real (CLAUDE.md §2).

## Consequences

- **+** Minimal operations work; nothing sensitive is exposed to the internet.
- **+** The demo survives a provider or network outage, honestly.
- **−** No remote access for evaluators between reviews. Acceptable.
- **−** Not production deployment. It is described as a demo deployment only.
- **Viva in 2 minutes:** "Three containers on a laptop. Because our AI is hosted, the live demo's risk is the network, so we have a provider check, a completed golden project, a recorded run, and we say openly when we use them."
