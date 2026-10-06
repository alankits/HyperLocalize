# Solo execution plan for the spike [PROPOSED, 2026-10-06]

**Context (user-reported 2026-10-06):** one developer, who understands spoken Tamil but cannot read or write it. The approved spike plan (`SPIKE_PLAN.md`) assumes a team. This plan keeps every safeguard, never invents a second rater, speaker or reviewer, and lists the **minimum outside help** each task needs. Items marked **NEEDS APPROVAL** would change an approved spike rule, and must be decided **before any results exist**.

| Spike role | Solo adaptation | Minimum outside help |
|---|---|---|
| Speaker A | You. You read the English script and the English reference and held-out sentences. **No Tamil reference clip** (you can't read it), so rule 4 uses the English reference only. No threshold changes. | The faculty guide explains the form (the explainer must not be the speaker), countersigns it, and the 24 h wait still applies |
| Speaker B (the different-speaker control in rule 4) | **Option A, recommended:** one volunteer, matched in gender and age, about 1 hour (consent, 24 h wait, 15 min recording). **Option B, NEEDS APPROVAL:** an impostor set of real recordings from an openly licensed dataset, compared with your held-out clip by ECAPA, with no cloning of anyone else. This changes rule 4 and the Q6 data policy ("team's own voices only"). **Without either**, the approved rule already says condition 3 is not met, so **the MVP ships with stock voice only** | 1 volunteer (Option A) |
| R1 (Tamil-literate rater) | **Cannot be you.** Needed for: the reference translation, MQM labels, the glossary, unit and number-word forms, and pronunciation marking | 1 Tamil-literate person, about 7–8 h [ESTIMATE from SPIKE_PLAN] |
| R2 (second rater) | If no second Tamil reader is found, report **single-rater results**: κ and agreement are **NOT COMPUTABLE**, and this is stated as a limitation. The seeded errors are then written by R1 after the rules are frozen; the developer (you) never writes them | Ideally a 2nd Tamil reader for about 6 h |
| Tamil naturalness listeners (M4) | You **can** rate by ear (you understand spoken Tamil), plus up to 4 named listeners | 0–4 listeners |
| "Same person?" listeners who know Speaker A | Friends or family who know your voice; no Tamil reading needed | 2–4 people, about 15 min each |
| Two independent fact-checkers (TEST_SCRIPT §4) | You, plus the faculty guide or another person, each recording page numbers | 1 person |
| Demo separation of duties | You operate separate accounts (reviewer, manager2). Say so openly: the system enforces the rule, but one person plays both roles | None |

## Order
1. Push the repo to a private GitHub remote; install Docker.
2. Meet the faculty guide: the ethics question, explaining the form, the countersignature, and the fact check.
3. Recruit R1 (essential), and Speaker B or decide Option B.
4. Fact check → timed read-through → freeze the script → R1's texts → sign → record.

Until then the MVP runs end to end on clearly labelled MOCK providers, human transcripts and human edits.
