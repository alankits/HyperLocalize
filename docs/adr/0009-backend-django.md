# ADR 0009: Backend framework: Django

**Status:** Proposed (2026-10-05). Not yet approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §6.2; Q2 answer

## Context

Up to 4 students with **intermediate Python**, basic JavaScript/React and little DevOps experience; about 5 months; periodic faculty reviews (Q2). The project needs authentication, per-project roles, an admin interface for users, providers and policies (UC8), relational models with migrations, and row locking (ADR 0006). The ML/media ecosystem is Python-first (ffmpeg wrappers, provider SDKs, evaluation libraries).

## Options Considered

| Criterion | Django | FastAPI + SQLAlchemy + Alembic | Node.js (NestJS) |
|---|---|---|---|
| Fit with team skills | **Good** (Python; conventions are well documented) | Good (Python), but more pieces to assemble | Poor (basic JS only) |
| Auth, sessions, CSRF, admin, ORM, migrations | **Built in** | Assemble yourself | Partly |
| Server-rendered UI (ADR 0010) | **Built in** (templates) | Possible (Jinja2) | Possible |
| Row locking (`select_for_update`, `skip_locked`) | Yes (verified in the Django 6.1 docs: no `FOR SHARE`, so ADR 0006 uses `FOR UPDATE`) | Yes | Yes |
| Non-differentiating work | **Lowest** | Higher | Higher |
| Viva | "Batteries included, so we spent our time on consent and verification" | "Why rebuild auth?" | — |

## Decision

Django (the current supported release; the docs consulted were version 6.1), with server-rendered templates (ADR 0010). **No Django REST Framework in the MVP.** The few JSON endpoints needed for job polling and the review player are plain Django views. DRF is added only if a real API consumer appears.

The Django admin is used for Administrator tasks (users, provider configuration, policies such as provider chain order, quota warnings and retention), **with restricted permissions**:
- Consent records can't be created or edited in the admin; consent changes only through the `identity` services.
- Audit records are read-only in the admin.
- **Artefact `status` and `consent_*` fields** (SynthesisedSegment, RenderedScene, Export, VoiceProfile, RemoteCopy) and **Job state** are **read-only** in the admin, so the admin can't un-quarantine anything or bypass checkpoint CP10. *(Added after independent review.)*
- Changes to the provider chain and policies made through the admin are **audited** (a custom `save_model`).
- A test checks that an admin user **cannot** change a quarantined artefact back to ACTIVE.

## Consequences

- **+** The team spends its 5 months on pipeline, consent and verification, not on authentication plumbing.
- **+** Django's documentation and conventions are easy to defend in a viva.
- **−** Django's "magic" (ORM laziness, signals) can hide behaviour. Rule: no signals for consent or audit (ADR 0001); explicit service functions only.
- **−** The admin must be locked down so it can't bypass consent or audit. This needs a test.
- **Viva in 2 minutes:** "Our team knows Python. Django gives us auth, admin, ORM, migrations and row locks out of the box, so our effort went into the parts that make HyperLocalize different."
