# ADR 0015: Identity definition: consent-governed voice identity with fallback

**Status:** Pending spike results (provisional decision recorded 2026-10-05; revised the same day for zero budget). Not approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §3; Q4 (revised), Q5, Q6 answers; `docs/THIRD_PARTY_TERMS.md`; `docs/SPIKE_PLAN.md`

## Context

"Identity" was [UNKNOWN] (CLAUDE.md §5). Answers:
- Q5: no lip-sync; faces are future scope.
- Q6: external processing allowed for the team's own voices.
- Q3: Tamil.
- Q4 (revised): **zero budget**, so every paid cloning service is excluded.

The only free Tamil voice-cloning model in scope is **IndicF5** (AI4Bharat). It is a prompt-based model: it takes a reference clip **and its transcript** and speaks new Tamil text in that voice. It runs on CPU (slow, speed unmeasured) or on Kaggle GPU in batch (ADR 0019). Licence: the model card says MIT, but **we treat it as non-commercial** (`THIRD_PARTY_TERMS.md` §2). Its model card requires explicit permission from the voice owner.

## Options Considered

| Criterion | Consent records only | **Consent-governed IndicF5 cloned voice with automatic fallback** | Voice + face | Subtitles only |
|---|---|---|---|---|
| Matches "identity-preserving" | Weak | **Strong for voice** | Strongest | None |
| Zero-budget feasible | Yes | **Yes** (local CPU or Kaggle) | No (out of scope, Q5) | Yes |
| Where identity data lives | — | **Laptop + temporary private Kaggle dataset** (no third-party clone object) | — | — |
| Viva | Weak | **The identity owner controls how they are rendered** | — | Contradicts the project name |

## Decision (provisional)

"Identity" means:
- an **IdentityOwner**;
- a **VoiceProfile**, which is our stored, consented **reference clip + transcript** (no provider-side clone);
- a versioned **Consent** listing uses, project, languages, expiry and named processors (Kaggle; Groq for transcription audio).

Rendering mode per speaker, resolved by the backend:

| State | Mode |
|---|---|
| Active consent for `voice_synthesis`, this project, `ta-IN`; cloning allowed by policy | `CLONED_VOICE` (IndicF5) |
| No consent, expired or revoked; **or both IndicF5 runtimes unavailable** | `STOCK_VOICE` (labelled synthetic: MMS-TTS / Indic Parler-TTS) |
| Policy forbids synthesis | `SUBTITLES_ONLY` |

**Future scope (Q5):** lip-sync, faces, on-screen text replacement.

**Non-commercial scope:** because of IndicF5 (conservative reading) and MMS-TTS (CC-BY-NC-4.0), the cloned- and stock-voice outputs are for **academic, non-commercial** demonstration only. The export manifest says so.

**The spike decides** (rule 4) whether IndicF5's Tamil quality is good enough for `CLONED_VOICE` in the MVP. If not, the MVP ships with stock voice and subtitles, the identity claim is narrowed, and you are told first.

## Consequences

- **+** Identity data never sits with a voice-cloning company. Deletion is ours to do, except the temporary Kaggle copy (ADR 0006).
- **−** Cross-lingual prompting (an English reference clip driving Tamil speech) may preserve timbre poorly. The spike also tests a **Tamil** reference clip read by the same speaker.
- **−** Licensing ambiguity means a strictly non-commercial scope.
- **Viva in 2 minutes:** "Identity is the speaker's voice, reproduced by an open-source Tamil model from a clip they consented to, only while that consent is active. Revoke it and we kill the job, refuse any late output, delete the clip, and fall back to a labelled stock voice that needs review again."
