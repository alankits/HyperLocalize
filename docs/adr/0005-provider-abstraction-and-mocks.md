# ADR 0005: AI provider abstraction, mock providers, usage ledger and budget cap

**Status:** Proposed (2026-10-04; revised 2026-10-05 after the ADR review). Not yet approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §6.7, CLAUDE.md §2 and §4

## Context

Each AI stage may change provider after the spike (ADRs 0015–0018, pending). Q4 sets a hard limit: free tiers plus at most **₹2,000 per month** for all AI APIs, no GPU, and hosted APIs only. Q6 allows external APIs for voice and video, but only the team's own voices are used. Free tiers carry rate limits, and some free tiers allow the provider to use submitted content for training (verified for the Gemini API free tier; see `docs/SPIKE_PLAN.md` §3). Tests must run without network access or cost. CLAUDE.md §2 requires mocks to be clearly named and listed as stubs.

**This ADR decides only the abstraction and its safeguards.** Which providers to use is decided by the pending ADRs 0015–0018.

## Options Considered

| Criterion | Call provider SDKs directly | One interface per stage + adapters + mocks + usage ledger | Generic third-party abstraction library only |
|---|---|---|---|
| Swap providers | Hard | Easy | Depends on its coverage of Tamil TTS and voice cloning |
| Testable offline | No | Yes | Partly |
| Consent enforced at the call site | No | Yes (a `ConsentCheck` parameter is required, ADR 0006) | No |
| Prevents an accidental budget overrun | No | **Yes (hard cap)** | No |
| Explainability | High | High | Medium |

## Decision

**Interfaces.** One interface per stage, each with a deliberately small set of methods:

| Interface | Methods |
|---|---|
| `TranscriptionProvider` | `transcribe(audio) → segments with word timestamps` |
| `TranslationProvider` | `translate(segment, context) → draft + rationale + adaptation type` |
| `MeaningCheckProvider` | `check(source, target) → flags` (AI flags, ADR 0008) |
| `SpeechSynthesisProvider` | `synthesise(text, voice, pace, consent_check=None) → audio`. `consent_check` is **required** when `voice` is a cloned voice. |
| `VoiceProfileProvider` | `create(reference_audio, consent_check)`, `delete(voice_id)` |

**Eligibility rules for real adapters:**
- A `VoiceProfileProvider` **must** support deletion through its API. Otherwise it is ineligible.
- Content containing identity data (reference audio, cloned speech) is sent only to providers whose terms, **as configured for our account**, do not allow training on it. That means paid tier, opt-out applied, or a contractual no-training term. Whatever setting was used is recorded in the provider configuration and the evidence manifest.
- Transcripts and translations are sent only on terms that are disclosed in the consent form.

**Recorded on every call:** provider, model identifier and version (where exposed), prompt or template version, parameters, timestamps, **usage units** (audio seconds, tokens, characters) and an estimated cost in ₹.

**Usage ledger and hard budget cap.** Every call writes a `ProviderUsage` row. Before each call, the adapter checks this month's estimated spend against an admin-set **monthly cap** (default ₹1,800 [PROPOSED], which leaves headroom under ₹2,000). Over the cap, the call is refused and the job fails with a clear `BUDGET_CAP_REACHED` error. This is a Policy under UC8.

**Rate limits and errors.** Each adapter applies the provider's documented rate limit, retries transient errors with back-off, enforces a per-call timeout, and maps errors to one small set of types (`Transient`, `RateLimited`, `InvalidInput`, `ProviderRefused`, `BudgetCapReached`).

**Mocks.** Every interface has a `Mock…Provider` (e.g. `MockSpeechSynthesisProvider`), marked in a code comment as a test stub and listed under stubs in `docs/STATUS.md`. Mocks are deterministic and cost nothing. `MockSpeechSynthesisProvider` also has a test-only **barrier hook**, which lets a test pause a job at a checkpoint (ADR 0006).

**Demo mode.** Mocks are never used silently in a live demo. If a real provider is down during the demo, the fallback is a previously completed project or a recorded run (ADR 0012), and it is introduced as such.

## Consequences

- **+** Spike results are acted on by adding adapters, without redesign.
- **+** The ₹2,000 limit is enforced in code, so a bug loop cannot overspend.
- **+** The full pipeline, including revocation, can be tested offline.
- **−** Cost estimates in the ledger use published prices, which can drift. The ledger is compared with the provider dashboards monthly.
- **−** End-to-end vendor dubbing pipelines can't be used, by design, because they would bypass review, verification and consent.
- **Viva in 2 minutes:** "Each AI stage is an interface with a real adapter and a mock. Identity-using calls need a consent token. Every call is metered, and a hard monthly cap stops spending."
