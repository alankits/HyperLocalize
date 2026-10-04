# ADR 0015: Identity definition: consent-governed voice identity with fallback

**Status:** Pending spike results (provisional decision recorded 2026-10-05). Not approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §3; Q5 and Q6 answers; `docs/SPIKE_PLAN.md` M3 and decision rule 4

## Context

"Identity" was [UNKNOWN] (CLAUDE.md §5). Answers:
- Q5: lip-sync is not expected; faces stay out of scope.
- Q6: external APIs may process voice; only team members' voices are used.
- Q3: the target language is Tamil.

Hosted voice cloning with documented Tamil support exists from at least two providers (`docs/SPIKE_PLAN.md` §3), but **quality in Tamil is unmeasured**.

## Options Considered

| Criterion | Consent records only (no cloned voice) | **Consent-governed cloned voice with automatic fallback** | Voice + face / lip-sync | Subtitles only |
|---|---|---|---|---|
| Matches "identity-preserving" | Weak | **Strong for voice** | Strongest | None |
| Ethical risk | Low | Medium, governed by ADR 0006 | High | Very low |
| Feasible with no GPU, ₹2,000/month | Yes | **Yes, if spike M3 passes** | No (and out of scope per Q5) | Yes |
| Viva | "Where is the identity?" | **The identity owner controls how they are rendered** | — | Contradicts the project name |

## Decision (provisional)

"Identity" means three things:
- an **IdentityOwner** (a real person);
- a **VoiceProfile** created from consented reference audio at a hosted provider;
- a versioned **Consent** that lists uses, project, languages, expiry and named processors.

For each speaker, the backend resolves a rendering mode at render time:

| Consent / policy state | Mode |
|---|---|
| Active consent for `voice_synthesis`, this project, `ta-IN`; cloning allowed by policy | `CLONED_VOICE` |
| No consent, expired or revoked | `STOCK_VOICE` (labelled as synthetic, not the speaker) |
| Policy forbids synthesis | `SUBTITLES_ONLY` |

**Future scope (Q5):** lip-sync, face processing, on-screen text replacement.

**The spike decides whether `CLONED_VOICE` is in the MVP** (`docs/SPIKE_PLAN.md` decision rule 4). If no cloning candidate passes:
- the MVP ships `STOCK_VOICE` + `SUBTITLES_ONLY`;
- consent governance is still built, because it also covers the use of the speaker's recorded voice;
- the identity claim in the docs and viva is narrowed;
- you are told before this ADR is finalised.

## Consequences

- **+** Identity becomes a governed, revocable capability rather than a fixed feature.
- **−** Cross-lingual cloning (English reference → Tamil speech) may preserve timbre poorly. That's exactly what M3 measures.
- **−** Mixing cloned and stock voices in one video can sound uneven; the UI labels each speaker's mode.
- **Viva in 2 minutes:** "Identity here means the speaker's voice, used only under a current consent version. If consent goes, the system switches that speaker to a labelled stock voice or subtitles and requires review again. We don't touch faces."
