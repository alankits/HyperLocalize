# ADR 0018: Tamil speech synthesis and voice-profile provider

**Status:** Pending spike results (provisional decision recorded 2026-10-05). Not approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §6.7; ADRs 0005, 0006, 0015; `docs/SPIKE_PLAN.md` M3–M6

## Context

The pipeline needs Tamil (`ta-IN`) speech: a **stock voice** (`STOCK_VOICE`) and, if the spike passes, a **cloned voice** (`CLONED_VOICE`) made from an English reference recording. Hosted only, ₹2,000/month. ADR 0005 requires a deletion API for voice profiles and no training on identity data. Facts below were checked on 2026-10-05; sources are in `docs/SPIKE_PLAN.md` §3.

## Options Considered

| Candidate | Tamil | Cloning | Deletion | Price | Data / terms |
|---|---|---|---|---|---|
| **Sarvam Bulbul v3** (stock) + **Sarvam voice cloning** | Yes (`ta-IN`) | Yes. `ta-IN` is in the cloning language list, and the docs say a reference clip in any supported language can be used (an English reference is OK). Reference clip 10–30 s. | Delete Voice endpoint is listed in the API reference | TTS ₹3 per 1,000 chars. Cloning ₹30 per 10K chars (from a search result on Sarvam's pages; **confirm on the dashboard**). ₹100 free credits. Cloning limit 10 requests/min on Starter. | A consent acknowledgement is mandatory when saving a clone. Training-use statements **conflict** between the privacy policy and the Trust Center: opt out and confirm. |
| **ElevenLabs** Instant Voice Cloning | Yes in Multilingual v2, Flash v2.5, Eleven v4. **Not listed for Eleven v3.** | IVC included from the **Starter** plan (not Free) | `DELETE /v1/voices/{voice_id}` | Starter is listed at **$6/month** (a $1 first-month figure also appears; confirm on purchase), 30,000 credits/month. API list prices: v2 $0.08 per 1K chars; v4 shown at $0.022 per 1K chars as a temporary discount. | The prohibited-use policy forbids cloning without consent or legal right. A data-use opt-out toggle exists. Zero Retention Mode is enterprise-only. |
| **Google Chirp 3 HD** (stock) | `ta-IN`, GA. Pace 0.25×–2×. | Instant Custom Voice supports `ta-IN` but is **allowlist-only** (contact sales) and requires a recorded consent statement | — | 1M chars/month free, then $30 per 1M | **Cloning excluded** (access restricted); stock voice OK |
| Azure Speech | Tamil TTS voices not confirmed in the page fetched **[UNVERIFIED]**. Personal Voice is limited access. | Excluded (limited access) | — | F0: 0.5M chars/month free | Not pursued |

## Decision (provisional)

- **Stock voice:** Google Chirp 3 HD `ta-IN` (generous free tier, GA, pace control) vs. Sarvam Bulbul v3, decided by spike M3 and M4.
- **Cloned voice:** Sarvam voice cloning (Tamil-focused provider, cheapest, delete endpoint, mandatory consent acknowledgement) vs. ElevenLabs IVC on Starter. Decided by spike M3 and decision rule 4, **after** the training-use opt-out is confirmed for whichever is chosen.
- Saved voice IDs are used (not sending the reference audio with every request), so revocation has exactly one provider-side object to delete.

## Consequences

- **+** At least two documented Tamil cloning options and two stock options; none needs a GPU.
- **−** The rate limit on Sarvam cloning (10 requests/min on Starter) means a 30-segment scene takes at least about 3 minutes to synthesise. That's acceptable for previews (and it makes the mid-job revocation demo easy), but it is a UX cost to measure.
- **−** Provider deletion can be shown at the API level only; what the provider actually keeps can't be verified by us.
- **Viva in 2 minutes:** "We compared Tamil voices from providers whose docs confirm Tamil, deletion APIs and consent rules. We excluded those with restricted access, then let measured intelligibility, pronunciation of numbers and terms, and similarity decide."
