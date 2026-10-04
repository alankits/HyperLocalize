# ADR 0012: Deployment: Docker Compose on a laptop, with a demo-resilience plan

**Status:** Proposed (2026-10-05). Not yet approved. It includes a proposed default for Q18 (local laptop demo).
**Source:** `docs/PHASE0_DISCOVERY.md` §6.11; Q2, Q4, Q8 answers

## Context

There is no GPU, and all models are hosted APIs (Q4), so the app itself is light. The team has little DevOps experience (Q2). The final evaluation includes a **live demo** (Q8), which depends on internet access and on third-party API availability, and that is the biggest live-demo risk.

## Options Considered

| Criterion | **Docker Compose on a laptop** | Single cloud VM with Docker Compose | Managed platform (PaaS) |
|---|---|---|---|
| Effort | **Low** | Medium (SSH, firewall, TLS) | Medium |
| Cost | ₹0 | Ongoing VM cost | Ongoing |
| Exposure of sensitive media to the internet | **None** | Needs hardening | Needs configuration |
| Works without venue Wi-Fi | Only for already-generated content | No | No |

## Decision

- **Docker Compose** with three services: `web` (Django), `worker` (`manage.py run_worker`), and `db` (PostgreSQL). Media is in a named volume. Secrets come from a `.env` file, which is git-ignored, with a committed `.env.example`.
- One-command start, documented in the README.
- The demo runs on a team laptop **[PROPOSED default for Q18]**. A cloud VM is future scope.
- **Demo-resilience plan:**
  1. A `check_providers` management command checks reachability, API keys and the remaining budget before the demo.
  2. A completed "golden" project with all artefacts is prepared in advance, so review, approval, export, audit and evidence can be shown without calling any API.
  3. A screen recording of the full live run, including mid-job revocation, made in the week before.
  4. A mobile-hotspot fallback for internet access.
  5. **If a fallback is used, it is announced.** Pre-generated content is never presented as live, and mocks are never presented as real (CLAUDE.md §2).

## Consequences

- **+** Minimal operations work; nothing sensitive is exposed to the internet.
- **+** The demo survives a provider or network outage, honestly.
- **−** No remote access for evaluators between reviews. Acceptable.
- **−** Not production deployment. It is described as a demo deployment only.
- **Viva in 2 minutes:** "Three containers on a laptop. Because our AI is hosted, the live demo's risk is the network, so we have a provider check, a completed golden project, a recorded run, and we say openly when we use them."
