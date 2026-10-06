# Viva notes

## The 2-minute explanation

"HyperLocalize is a general, controlled video localization workflow.

You create a project and upload a video. The system analyzes it into scenes and segments, then drafts a localization for each segment using context: the neighbouring lines, the speaker, the target-audience profile, a glossary and the timing budget.

The draft is never trusted. Numbers, units and key terms are rule-checked, and a failure blocks approval. An AI meaning check flags possible reversals, such as a dropped 'not', for a human to look at. A reviewer edits, overrides with a written reason, or regenerates just one scene. A manager approves a frozen snapshot, and any later change invalidates it.

A speaker's voice is used only while their own consent is valid. The server decides the voice mode, and revoking consent stops a running job within seconds, deletes the cloned audio, and falls back to a stock voice that must be reviewed again.

Every action goes into a hash-chained audit log, and the export carries the chain head as evidence. We say tamper-evident, not tamper-proof.

The AI providers sit behind interfaces. Today they are labelled mocks, plus candidate adapters, until the spike measures which real models are good enough."

## Likely questions and honest answers

| Question | Answer |
|---|---|
| Isn't this just ASR → MT → TTS? | No. That pipeline is commodity and swappable. The contribution is the controlled workflow: context-aware drafts, rule-checked critical content, a review gate that cannot be bypassed, scene-level regeneration, enforced consent, and an export that carries evidence. The *combination* is [PROPOSED NOVELTY]; no product or literature check has been done yet. |
| How do you know context helps? | We don't yet. The ablation (context on, context off, plain MT) is planned in the spike and **not measured**. |
| What is "identity" here? | In the MVP: a consented reference voice clip, plus versioned consent records. No faces. Whether identity covers more at product level is open. |
| Can an admin enable someone's voice? | No. Only the owner grants consent. A demo reset only makes narrower copies of the owner's own grant. Tests prove an Administrator's grant is refused. |
| What happens if consent is revoked mid-job? | The worker polls every second, kills the inference subprocess, and ends the job CANCELLED. Artefacts are quarantined and purged, the scene falls back to a stock voice, and the approval is invalidated. A test does this with a real subprocess. |
| Can you recall exports? | Not copies that were already downloaded. The system blocks and deletes its own package, and says so honestly. |
| Is the audit log tamper-proof? | No. It is tamper-evident: database triggers block edits, and the verifier detects changes. Someone with database rights could rebuild the whole chain, which is why the chain head goes into every export. |
| Why is everything MOCK? | Real models are chosen by measured spike results, and the spike needs consented recordings and a Tamil-literate rater. Mocks are labelled everywhere and can never be exported. |
| How did you make sure the consent code is right? | Negative-first tests, plus an independent review that found 1 blocker and 6 major issues, all fixed with regression tests (`docs/CODE_REVIEW.md`). |
| Why a monolith and not microservices? | One developer, a laptop demo and a zero budget. Module boundaries come from service functions, and the database gives the locking that consent needs (ADR 0001). |
| Is it secure or GDPR compliant? | We make no such claim. We do apply sensible practices: role checks in services, consent enforced in the backend, media outside the web root, secrets in env, no raw content in logs. |
