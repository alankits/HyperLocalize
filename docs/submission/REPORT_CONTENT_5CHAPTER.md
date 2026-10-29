# HyperLocalize — Project Report Content (5-Chapter College Format)

**Purpose:** submission-ready text for the micro-project report, following the college table of contents
(Cover Page → Abstract → TOC → List of Figures and Tables → Chapter 1–5 → References).
**Facts as of:** 2026-10-30, from `docs/STATUS.md`, `docs/ARCHITECTURE.md`, `docs/EVALUATION.md`,
`docs/uml/`, `docs/adr/` and the measured test runs.
**Honesty rules used:** every number is a MEASURED RESULT (with date) or a TARGET. Rows marked
**NOT MEASURED** are reported as such. MOCK providers are named as mocks. No claim of being
"secure", "production-ready", "tamper-proof" or "novel" is made.

Everything in `[SQUARE BRACKETS]` is a placeholder for you to fill in. Text after a `>` line is an
instruction to you (figure to insert, formatting note) and must be deleted before submission.

---

# 1. Cover Page

> Format this page as your college template requires (normally centred, Times New Roman 14–16 pt,
> college logo at the top).

**A MICRO PROJECT REPORT**

**on**

## HYPERLOCALIZE: CONTEXT-AWARE IDENTITY-PRESERVING VIDEO LOCALIZATION

*Submitted by*

**[STUDENT NAME]** — **[REGISTER NUMBER]**

*in partial fulfilment of the requirements for the award of the degree of*

**[BACHELOR OF ENGINEERING / BACHELOR OF TECHNOLOGY]**

*in*

**COMPUTER SCIENCE AND ENGINEERING**

**[SEMESTER / YEAR]**

*Under the guidance of*

**[GUIDE NAME], [DESIGNATION]**

**[DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING]**

**[COLLEGE NAME], [PLACE]**

**[UNIVERSITY NAME]**

**[MONTH, YEAR]**

> If the template asks for it, add the bonafide certificate, declaration and acknowledgement pages
> before the Abstract. The declaration should mention, in whatever form your college permits,
> that an AI coding assistant was used for implementation and that all design decisions were
> reviewed and approved by you. Do not claim the assistant performed human review or approval —
> it does not.

---

# 2. Abstract

Important public video information — health guidance, food and water safety, energy advisories,
training material — often fails to reach the people who need it because it is produced in a language
and cultural framing they do not share. Modern AI makes automatic dubbing look easy: a speech
recogniser writes a transcript, a translation model or large language model produces the target text,
and a speech synthesiser (sometimes a voice-cloning model) produces the new audio. Such a pipeline is
fast, but it treats its own output as final. A dropped "not", a changed dosage number, a term the
audience does not use, or an unconsented copy of a speaker's voice can reach the audience unnoticed,
and the exported file carries no record of who checked what.

HyperLocalize is a **context-aware, identity-preserving video localization system** built as a
controlled workflow rather than an autonomous pipeline. A Localization Manager creates a project with
a target-audience profile and glossary. The source video is validated and analysed into timed scenes
and segments. Each segment is localized **with its context** — the neighbouring lines, the speaker,
the audience profile, the glossary, the available time slot and any reviewer instruction — and every
draft records exactly which context inputs were used. A preview is rendered, and a human reviewer
edits the text, overrides a check with a written reason, or regenerates a single scene. Rule-based
checks on critical content (numbers, units, glossary terms, structure and speech overrun) block
approval until the text is fixed or deliberately overridden. A speaker's identity is used only while
that person's own versioned consent is valid; revocation stops running jobs, quarantines and deletes
derived audio, invalidates affected approvals, and falls back to a stock voice. Approval freezes an
immutable snapshot of exact versions with separation of duties, export refuses any placeholder (MOCK)
artefact, and every governance action is written to an append-only, SHA-256 hash-chained audit log
whose head is embedded in the exported evidence manifest.

The system is implemented as a **Django modular monolith** (nine apps) on **PostgreSQL 17**, with a
hand-written database job queue, server-rendered pages using htmx, and all AI stages behind swappable
provider interfaces. Candidate real providers are faster-whisper (English transcription on CPU),
Gemini (context-aware translation), and MMS-TTS Tamil (stock voice on CPU); voice cloning remains a
clearly labelled mock. The current demonstration scenario is English health information localized
into Tamil.

**Measured results:** the full automated suite passed **210 tests with 2 optional real-model tests
skipped** (2026-10-22, 125 s); a separate black-box suite passed **11 of 11**; and an end-to-end HTTP
check passed **15 of 15 steps** (2026-10-06). On a single 58-second public video, a real pipeline run
produced real Tamil speech and subtitles: the intelligibility proxy (Whisper back-transcription
character error rate) was **0.16**, but only **2 of 14 lines** fitted their time slot, which led to a
length-budgeted prompt and a blocking overrun check. Translation quality, speaker similarity, speed
and the benefit of context are **not yet measured**; a formal evaluation with consented speakers and a
Tamil-literate rater is planned.

**Keywords:** video localization, dubbing, context-aware machine translation, human-in-the-loop
review, consent management, hash-chained audit trail, evidence manifest, Tamil, Django.

---

# 3. Table of Contents

> Insert the auto-generated Word table of contents here (References → Table of Contents), or copy the
> outline below and add page numbers after final formatting.

1. Cover Page
2. Abstract
3. Table of Contents
4. List of Figures and Tables

**Chapter 1: Introduction**
- 1.1 Background of the Project
- 1.2 Problem Statement
- 1.3 Objectives
- 1.4 Scope of the Project

**Chapter 2: Literature Survey**
- 2.1 Review of Existing Research or Related Projects
- 2.2 Summary of Existing Approaches
- 2.3 Research Gap or Limitations of Existing Systems

**Chapter 3: Methodology and System Design**
- 3.1 Proposed Methodology
- 3.2 System Architecture or Block Diagram
- 3.3 UML Diagrams
- 3.4 Tools and Technologies Used
- 3.5 Module Description

**Chapter 4: Implementation and Results**
- 4.1 Implementation Details
- 4.2 Screenshots of the Application
- 4.3 Sample Inputs and Outputs
- 4.4 Unit Testing and Results

**Chapter 5: Conclusion and Future Enhancement**
- 5.1 Summary of the Work
- 5.2 Conclusion
- 5.3 Future Enhancements

References

---

# 4. List of Figures and Tables

## List of Figures

| Figure | Title | Source to insert |
|---|---|---|
| 1.1 | HyperLocalize workflow (Create → Upload/Analyse → Localize → Preview → Review → Regenerate → Approve → Export) | Redraw from the flow in §1.4 |
| 3.1 | System architecture / block diagram | Redraw from `docs/uml/README.md` §2 (component diagram) |
| 3.2 | Use case diagram (UC1–UC9 and «include» Record Consent) | `docs/uml/README.md` §1 |
| 3.3 | Sequence diagram: main localization workflow | `docs/uml/README.md` §3 |
| 3.4 | Sequence diagram: consent revoked during a running voice job | `docs/uml/README.md` §4 |
| 3.5 | State diagram: Scene | `docs/uml/README.md` §5 |
| 3.6 | State diagram: Job | `docs/uml/README.md` §5 |
| 3.7 | State diagram: Consent version (append-only) | `docs/uml/README.md` §5 |
| 3.8 | Core entity-relationship diagram | `docs/submission/source/er_core.mmd` |
| 3.9 | Class diagram (generated from the Django models) | `docs/uml/class_diagram.md` |
| 4.1 | Localization Manager: project list | `docs/screenshots/02-manager-project-list.png` |
| 4.2 | Localization Manager: project detail with the approval gate | `docs/screenshots/03-manager-project-detail.png` |
| 4.3 | Reviewer: scene review with preview, checks and override fields | `docs/screenshots/05-reviewer-scene-review.png` |
| 4.4 | Speaker / Identity Owner: consent page | `docs/screenshots/06-identity-owner-consent.png` |
| 4.5 | Auditor: audit trail and hash-chain verification | `docs/screenshots/07-auditor-audit-trail.png` |
| 4.6 | Administrator: policies, provider chains and free-quota warnings | `docs/screenshots/08-admin-policies-and-quota.png` |
| 4.7 | Media Operator: job queue and states | `docs/screenshots/04-operator-jobs.png` |
| 4.8 | Clip 01 timing: Tamil speech length ÷ slot length per line | Regenerate with `docs/submission/source/chart.js`, or plot the 14 ratios in §4.3 |

> The Mermaid sources are plain text in `docs/uml/README.md`; paste each block into mermaid.live
> (or run mermaid-cli) and export a PNG at 200 dpi for the report.

## List of Tables

| Table | Title |
|---|---|
| 2.1 | Comparison of existing approaches and HyperLocalize |
| 2.2 | Honest novelty classification of the project's features |
| 3.1 | Actors and their responsibilities |
| 3.2 | Tools and technologies used |
| 3.3 | Modules (Django apps) and their responsibilities |
| 3.4 | Consent checkpoints CP0–CP10 |
| 4.1 | Critical-content checks and their effects |
| 4.2 | Provider chains and labelled mocks |
| 4.3 | Test areas covered by the automated suite |
| 4.4 | Sample unit and integration test cases |
| 4.5 | Measured test results |
| 4.6 | Evaluation metrics: TARGET versus MEASURED RESULT |
| 4.7 | Problems found in the first real run and the design changes made |

---

# Chapter 1: Introduction

## 1.1 Background of the Project

Video has become one of the main ways public information is distributed. Health departments publish
hand-washing and oral-rehydration videos, civic agencies publish water-safety and energy guidance,
and organisations publish training material. Most of this material is produced in a small number of
languages. For a viewer who does not understand the language, or for whom the examples, units and
cultural references are unfamiliar, the information is effectively inaccessible even when the video
itself is freely available.

Localization is broader than translation. It adapts content for a target audience: the language, the
level of formality and reading level, cultural references, units of measure, and the timing of speech
against the picture. When the content carries critical facts — a quantity, a duration, a warning, a
negation — an error introduced during localization can change the meaning of the message. A dubbing
pipeline that turns "do not give the child water" into a positive instruction is worse than no
localization at all.

Recent speech and language models make automated dubbing technically easy. An automatic speech
recognition (ASR) model produces a transcript; a machine translation (MT) model or a large language
model (LLM) produces the target text; a text-to-speech (TTS) model, in some products a voice-cloning
model, produces the new audio; and a media tool muxes it back onto the picture. This raises three
practical problems that this project addresses directly:

1. **Trust.** Machine output for critical information is a draft, not a fact. It needs checks a
   reviewer can understand and a gate that cannot be bypassed by accident.
2. **Identity and consent.** A real speaker's voice is personal data. Reproducing it requires that
   person's informed, versioned consent, and revocation must actually stop the system.
3. **Accountability.** Someone must be able to answer who reviewed, who approved, which model
   produced which line, and which consent version applied at that moment.

HyperLocalize is positioned as an **information-access layer**. It can help critical video
information in domains such as health, food, water and energy cross language and cultural barriers.
It does not solve the underlying physical problems in those domains, and it is not a medical,
nutritional or engineering tool.

## 1.2 Problem Statement

Existing automatic dubbing approaches treat localization as a one-shot pipeline whose output is
assumed to be correct. In practice this creates four failures:

- **Output is treated as final.** Review, if it exists at all, is optional and unstructured. There is
  no mechanism that prevents an unchecked machine translation from being exported.
- **The errors that matter most are the ones least likely to be noticed.** A reviewer reading a
  translated script is unlikely to spot that "2 sachets" became "5 sachets", that a unit changed, or
  that a negation disappeared, especially in a language they read less fluently.
- **Consent is, at best, an upload-time attestation.** Revoking consent does not reliably stop work
  already in progress, and there is no defined behaviour for previews, approvals and exports that
  already contain the person's voice.
- **There is no verifiable record.** The exported file does not say which models produced it, which
  consent version was in force, or who approved it.

The problem addressed by this project is therefore: *how do we build a video localization system in
which AI output is only ever a draft, critical content is checked automatically, a human reviews and
approves every scene before release, a speaker's identity is used only while their own consent is
valid, and every governance action is recorded in a tamper-evident audit trail that travels with the
exported package — on a zero-rupee budget and a single laptop?*

## 1.3 Objectives

The objectives of the project are:

1. **Provide a complete project workflow:** Create Localization Project → Upload and Analyse Source
   Video → Context-Aware Localization → Generate Localized Preview → Human Review → Regenerate
   Scene/Output if Required → Approve → Export Localization Package.
2. **Localize each segment using its context** — neighbouring segments, speaker, audience profile,
   glossary, timing budget and reviewer instruction — and record which context inputs were used for
   every saved draft, so the decision is auditable rather than mysterious.
3. **Detect errors in critical content automatically** (numbers, units, glossary terms, structure and
   speech overrun), and block approval until a reviewer either fixes the text or overrides the check
   with a written, audited reason.
4. **Support scene-level regeneration**, so a reviewer can redo one problematic scene without
   disturbing the rest of an approved-in-progress project.
5. **Enforce consent in the backend** before any use of a speaker's identity, and make revocation stop
   new generation, cancel or kill running jobs, quarantine derived artefacts, and invalidate the
   approvals and exports that contained that identity.
6. **Gate approval and export:** freeze an immutable snapshot on approval, apply separation of duties,
   and refuse to export any placeholder (MOCK) output.
7. **Record every consent grant, revocation, approval, regeneration and export** in an append-only,
   SHA-256 hash-chained audit log, and include the chain head in an evidence manifest with every
   export.
8. **Keep AI stages behind provider interfaces**, so models can be swapped, mocked and administered,
   within a zero-rupee budget and without redesigning the workflow.

## 1.4 Scope of the Project

HyperLocalize is a general, controlled localization workflow — not a single-domain or single-language
tool. Health is a *demonstration* domain, not the product boundary. For the first demonstrable build
(the MVP), the scope was deliberately narrowed:

| Item | MVP decision |
|---|---|
| Language pair | One pair and one target locale per project; the MVP pair is **English → Tamil** |
| Upload limits | Up to **5 minutes and 500 MB** per video |
| Face processing / lip-sync | **Not included** (future scope only, and it would need its own consent design) |
| Identity in the MVP | A consented reference voice plus versioned consent records, with stock-voice or subtitles-only fallback (provisional) |
| Deployment | Demonstration on **one laptop**; Docker Compose files written but not yet run |
| Budget | **₹0**: open-source software and free tiers only |
| Demo scenario | English health information (oral rehydration salts, hand-washing) → Tamil. A test case, not the product's domain |

**Figure 1.1** — *HyperLocalize workflow.* Draw the eight stages of objective 1 as a horizontal
flow diagram with the governance layer (consent, review gate, audit) underneath.

**In scope for this report:** the full workflow above, the nine use cases, the consent and audit
mechanisms, the provider abstraction, the automated test suite, and the measured results from one
real public video plus one later end-to-end preview run.

**Out of scope:** lip-sync and face processing; multiple source languages per project; remote GPU
execution (designed only); C2PA signing; and any claim of production readiness, regulatory
compliance, or measured translation quality. These are stated as future work, not as delivered
features.

---

# Chapter 2: Literature Survey

> Scope note for the examiner: this chapter reviews the building blocks and the closest existing
> systems. It is **not** a systematic literature review; a formal product and literature check has not
> been completed, so the novelty claim in §2.3 is explicitly marked as *proposed*, not established.

## 2.1 Review of Existing Research or Related Projects

### 2.1.1 Automatic speech recognition

Whisper (Radford et al., 2022) is an encoder–decoder Transformer trained on roughly 680,000 hours of
weakly supervised multilingual audio. It is robust to accents and background noise and emits timed
segments, which makes it suitable as the first stage of a dubbing pipeline. faster-whisper
(SYSTRAN) re-implements Whisper inference on CTranslate2, which makes CPU inference practical on a
laptop. HyperLocalize uses faster-whisper `small` on CPU as its candidate English transcriber, and
also reuses it to transcribe its own Tamil output back as an intelligibility proxy. The known
weakness for this project is that Whisper is a *recogniser*, not a diarizer: without an additional
model it cannot say who spoke when, so the current implementation labels every segment "Speaker 1".

### 2.1.2 Machine translation for Indian languages

IndicTrans2 (Gala et al., 2023) is an open multilingual translation model covering the 22 scheduled
Indian languages, including Tamil. It translates essentially sentence by sentence. Large language
models such as Gemini can translate while receiving additional context in the prompt — neighbouring
sentences, a glossary, the audience profile, and a length constraint — and can state a rationale for
an adaptation. The trade-offs are equally real: LLMs may omit content or hallucinate, their free
tiers impose strict request quotas, and their output is non-deterministic. HyperLocalize therefore
treats both as interchangeable *candidates* behind one provider interface, and records which adapter,
model and prompt version produced each draft.

### 2.1.3 Text-to-speech and voice cloning

The Massively Multilingual Speech (MMS) project (Pratap et al., 2023) released TTS models for more
than 1,100 languages, built on the VITS architecture (Kim et al., 2021). The Tamil model
`facebook/mms-tts-tam` runs on CPU and is used here as the stock voice; its licence is CC-BY-NC-4.0,
so it is suitable for a non-commercial academic demonstration only. Zero-shot voice-cloning models
can imitate a speaker from a short reference clip, and Indian-language candidates such as IndicF5
exist, but cloning raises consent and misuse risks that are central to this project. In the current
build, cloning sits behind the consent gate but is still a labelled mock.

### 2.1.4 Translation quality assessment

The Multidimensional Quality Metrics (MQM) framework (Lommel et al., 2014) scores translations by
error category and severity and is the basis of the human evaluation planned for this project. chrF
(Popović, 2015) is a character n-gram F-score that behaves better than word-level metrics for
morphologically rich languages such as Tamil. Rule-based quality assurance for numbers, tags and
terminology is a standard feature of professional computer-assisted translation (CAT) tools — which
is exactly why the project treats such checks as *support for a reviewer*, not as proof of quality.

### 2.1.5 Provenance and audit

The C2PA specification defines signed provenance manifests for media. Hash chains, in which each
record stores the hash of its predecessor, are a long-established way to make a log tamper-evident.
HyperLocalize uses a hash-chained audit log and an evidence manifest; it does **not** implement C2PA
signing, and it describes its audit as tamper-evident, never tamper-proof.

### 2.1.6 Commercial dubbing tools

Commercial AI dubbing products (for example ElevenLabs Dubbing, HeyGen and Rask) and platform
features such as multi-language audio tracks already offer transcription → translation → voice
cloning, transcript editing, segment regeneration and in some cases lip-sync. Some require
attestation or verification of voice-cloning consent. These are capable products. HyperLocalize does
not compete with them on raw dubbing quality; it competes on the *control layer* around the same
commodity models. Product capabilities change frequently and should be re-verified before quoting.

## 2.2 Summary of Existing Approaches

**Table 2.1 — Comparison of existing approaches and HyperLocalize**

| Approach | How it works | Strengths | Limitations for critical content |
|---|---|---|---|
| Manual localization studio | Human translator, voice artist and editor work from a script | Highest quality; human judgement throughout | Slow and expensive; not viable for large volumes of public information |
| Subtitles only | Human or machine transcript is translated and overlaid | Cheap; leaves the original voice intact; low consent risk | Requires literacy in the target script; no audio access for low-literacy audiences |
| ASR → MT → TTS dubbing pipeline | Fully automatic, one pass | Fast, cheap, scalable | Output treated as final; critical numbers and negations can drift; no review gate; no consent enforcement mid-job |
| Commercial AI dubbing products | Managed pipeline with an editing UI, sometimes voice cloning | Good voice quality, polished UX, some consent attestation | Closed and vendor-dependent; governance evidence is not usually portable; cost per minute |
| MT quality-estimation tooling | Automatic scores (BLEU, chrF, COMET) on translated text | Cheap signal for ranking | Scores do not identify *which* number or negation changed; not usable as an approval gate |
| **HyperLocalize (this project)** | Commodity models inside a governed workflow: context-aware drafts, rule-checked critical content, human review gate, consent gate, audit chain, evidence-carrying export | Errors that matter are made visible and block release; identity use is consented and revocable; every action is traceable | Slower than a pure pipeline because of review; quality of the underlying models is not yet measured; voice cloning still mocked |

The comparison makes the project's position clear: it is not a better dubbing model, it is a
*control layer* around dubbing models.

## 2.3 Research Gap or Limitations of Existing Systems

The gap this project targets is not a missing model. Each component — ASR, MT, TTS, QA checks, audit
logging — exists and is mature. The gap is the **combination and its enforcement**:

1. **No unbypassable review gate in commodity pipelines.** Open-source dubbing scripts produce a file
   at the end; nothing structurally prevents an unchecked output from being released.
2. **Quality checks are not error-targeted.** Automatic metrics score a whole sentence. They do not
   answer the reviewer's real question: *did a number, unit, negation or required term change?*
3. **Consent is not enforced across stage boundaries.** Attestation at upload does not stop a job that
   is already running, nor does it define what happens to derived audio, previews and approvals.
4. **Evidence is not portable.** Exported media rarely carries a verifiable record of the models used,
   the consent version applied, and the human who approved it.
5. **Cost and vendor lock-in.** Managed tools assume a budget and a connection. A zero-budget
   academic build needs local, swappable models with an honest fallback path.

**Where HyperLocalize is genuinely new, stated carefully.** No individual feature is novel. The
*combination* — critical-content checks that block approval + a human review gate that cannot be
bypassed + backend-enforced, revocable consent + an evidence-carrying export — is a **proposed
novelty** within the project's own honest classification (Table 2.2). It has not been validated
against the literature or against existing products, and this report does not claim otherwise.

**Table 2.2 — Honest novelty classification of the project's features**

| Feature | Classification | Reason |
|---|---|---|
| ASR → MT → TTS pipeline; voice cloning | Existing / Common | Commodity, and swappable by design |
| Transcript editing, per-segment regeneration, human review | Existing / Common | Expected in professional localization |
| Provider abstraction, labelled mocks, database job queue, modular monolith | Implementation choice | Good engineering, not novelty |
| LLM translation with audience profile, glossary, timing budget and stated rationale | Enhancement | Context-aware MT is an active research area |
| Rule-based hard checks used as an approval-blocking gate | Enhancement | Similar QA exists in CAT tools; using it as a release gate is the difference |
| AI meaning-reversal flags requiring acknowledgement | Enhancement | An aid to review, never verification |
| Versioned, backend-enforced consent with revocation cascade and fallback | Enhancement | A required safeguard, implemented carefully |
| Evidence-carrying export with audit chain head | Enhancement | Provenance manifests (C2PA) already exist |
| The **combination** above as one workflow | Proposed novelty | Needs a literature and product check before it can be called novel |

---

# Chapter 3: Methodology and System Design

## 3.1 Proposed Methodology

The project followed a **design-first, evidence-first** methodology in two phases.

**Phase 0 — discovery and design.** Requirements, actors and use cases were analysed, and every major
decision was compared against two to four realistic alternatives on quality, performance,
scalability, reliability, privacy, cost, implementation difficulty and how easily it could be defended
in a viva. Each decision was recorded as an **Architecture Decision Record (ADR)**; 22 ADRs exist, of
which 17 are accepted and 5 (the AI provider and identity choices) are pending measurement.

**Phase 1 — MVP build.** The system was built in vertical slices: one thin path end to end (upload →
analysis → localization → preview → review → approval → export) before widening. Three working rules
shaped the build:

- **AI is optional at every boundary.** Every AI stage is a provider interface with an ordered chain;
  a clearly labelled mock exists for tests and development, and mock output can never be exported.
- **Governance is enforced in the backend.** Role checks and the consent gate live in service
  functions, not in templates, so a UI shortcut cannot bypass them.
- **Claims are labelled.** Every metric is a TARGET or a MEASURED RESULT; every mock is named as a
  mock; limitations are reported rather than hidden.

**The localization method itself.** For each segment, the system builds a request that contains:

- the segment's source text and its **time budget**;
- **two neighbouring segments on each side**, for discourse context;
- the **speaker** (who is being localized);
- the **audience profile** (locale, formality, reading level, cultural notes, declared unit
  conversions);
- the **project glossary** of required terms;
- any **reviewer instruction** (for a regeneration, for example "use simpler words").

The response is a subtitle text, a fully speakable speech text, an adaptation type (literal,
adapted, or expanded) and a stated rationale. A length budget derived from the voice's measured
speaking rate constrains the speech text so it can fit the slot. Each saved draft records the context
inputs, the adapter, the model and the prompt version — so a reviewer can see *why* a phrase was
adapted rather than translated literally. Visual context (keyframes, on-screen text) is **not**
implemented; the method is therefore context-aware in the textual and audience sense only.

**Development process.** Requirements → ADR with alternatives → implementation in a slice →
tests (negative cases first) → independent review for consent, audit and data-model changes →
documentation update. Findings from review are recorded with their fixes; the code review of the
consent and audit modules found 1 blocker and 6 major issues, all of which were fixed with regression
tests.

## 3.2 System Architecture or Block Diagram

HyperLocalize is a **modular monolith** (ADR 0001): one Django codebase and one PostgreSQL database.
This was chosen over microservices because the project has one developer, a laptop demonstration and a
zero budget, and because database transactions and row locks provide exactly the strong guarantees
that consent enforcement needs.

The architecture has four kinds of process:

1. **Web process.** Serves server-rendered pages with htmx partial updates. It never blocks on long
   work; it validates uploads, writes database rows and enqueues jobs.
2. **Worker processes.** Claim jobs from a hand-written PostgreSQL queue
   (`run_worker --lane default|synthesis|all`). Separate lanes stop slow speech synthesis from blocking
   analysis and localization.
3. **Inference subprocess.** Heavy model inference runs in a separate, killable process, so a consent
   revocation can terminate work in progress instead of waiting for it.
4. **PostgreSQL + media storage.** The database holds all state, including the job queue and the audit
   chain. Media lives outside the web root behind a storage interface.

AI stages sit behind provider interfaces with ordered fallback chains per stage; the Administrator can
reorder the chains and set free-quota limits.

**Figure 3.1** — *System architecture / block diagram.* Show the web process, the worker lanes, the
inference subprocess, PostgreSQL, media storage, and the provider adapters (real candidates and
labelled mocks). Source: `docs/uml/README.md` §2.

**Request path for one project (as implemented):**

```
Upload (ffprobe validation → Video row → audit VIDEO_UPLOADED → analyze_video job)
  → Worker: extract audio, transcribe (human SRT/VTT, else faster-whisper, else mock),
            detect shot cuts, plan scenes and segments
  → localize job (context per segment → translation drafts → rule checks + AI flags)
  → render_scene job per scene (resolve voice mode from consent → synthesise → fit timing
            → mix → RenderedScene → scene IN_REVIEW)
  → Reviewer: edit / override with reason / acknowledge / regenerate one scene / accept
  → Manager: approve (gate → immutable snapshot → audit APPROVED)
  → Export (CP9 consent under lock → package + evidence manifest → audit EXPORT_CREATED)
```

## 3.3 UML Diagrams

The diagrams below were drawn from the implemented code, not from an intended design. Each names the
module it describes. Insert the rendered figures at the points indicated.

**Use case diagram (Figure 3.2).** Six actors — Localization Manager, Reviewer/Linguist, Media
Operator, Speaker/Identity Owner, Administrator, Auditor/Faculty Evaluator — and nine use cases. UC1
includes UC2, UC3, UC4 and Record Consent; UC5 includes UC3 and UC4. UC1–UC9 and the actors are
confirmed project requirements (ADR 0013).

**Sequence diagram, main workflow (Figure 3.3).** Upload → validation → analyse job → transcript,
speakers, segments and scenes → localize job → translation versions, hard checks and AI flags →
per-scene render → reviewer actions → approval snapshot → export with CP9 under the owner lock and a
manifest carrying the chain head.

**Sequence diagram, revocation during a running job (Figure 3.4).** The identity owner revokes project
consent; the service locks the IdentityOwner row, inserts a REVOKED version, cancels queued jobs,
flags the running job, quarantines that owner's artefacts in that project, invalidates only the
affected approvals and exports, sets scenes to NEEDS_REGENERATION, queues a purge and stock-voice
fallback renders, and writes the audit record. The worker's one-second poll sees the change and kills
the inference subprocess. This flow is covered by a test that uses a real subprocess.

**State diagrams.** Three long-running objects have explicit state machines enforced in the service
layer:

- **Scene (Figure 3.5):** PENDING → TRANSLATED → IN_REVIEW → ACCEPTED, with CHANGES_REQUESTED and
  REGENERATING loops, and NEEDS_REGENERATION on revocation.
- **Job (Figure 3.6):** QUEUED → RUNNING → SUCCEEDED / FAILED, with CANCELLED on a cancel flag and a
  return to QUEUED on transient error or a stale heartbeat.
- **Consent version (Figure 3.7):** append-only rows: ACTIVE → REVOKED or EXPIRED, where narrowing
  inserts a new, narrower ACTIVE version rather than editing the old one.

**Entity-relationship diagram (Figure 3.8).** The core entities and their cardinalities: Project,
AudienceProfile, GlossaryTerm, Video, Scene, Segment, SegmentTranslation (versioned), CheckResult,
SynthesisedSegment, RenderedScene, Review, RegenerationRequest, Approval, IdentityOwner, Consent
(versioned), VoiceProfile, Export, AuditRecord, Job, ProviderConfig, ProviderUsage.

**Class diagram (Figure 3.9).** Generated from the actual Django models by `scripts/generate_uml.py`
(28 model classes across nine apps). Include it as a full-page figure; it is the ground truth for the
data model and is referenced by ADR 0014 (amended by ADR 0020).

**Design invariants worth stating in the viva:** translations, consent versions and audit records are
append-only; an Approval stores an immutable snapshot of exact version identifiers and is invalidated
by any later change; and every AI artefact records its adapter, model, prompt version and `is_mock`
flag.

## 3.4 Tools and Technologies Used

**Table 3.2 — Tools and technologies used**

| Layer | Tool / technology | Version (as used) | Why it was chosen |
|---|---|---|---|
| Language | Python | 3.x | Readable, strong media and ML ecosystem, explainable in a viva |
| Web framework | Django (no Django REST Framework) | 6.1.1 | Server-rendered pages, built-in auth and admin, fewer moving parts |
| Database | PostgreSQL | 17 | Transactions, row locks, `SKIP LOCKED`, triggers for the audit table |
| DB driver | psycopg | 3.3.6 | Current PostgreSQL driver |
| Frontend | Django templates + htmx | — | No separate SPA build; partial page refreshes (jobs panel every 2 s) |
| Job queue | Hand-written PostgreSQL queue | — | Needs its own cancel flag and consent checkpoint CP2; avoids extra infrastructure |
| Media processing | ffmpeg / ffprobe (static-ffmpeg in development) | — | Validation, audio extraction, shot-cut detection, tempo, mixing, muxing |
| Transcription (candidate) | faster-whisper `small` / `small-int8` on CPU | 1.2.1 | Accurate enough, runs without a GPU |
| Translation (candidate) | Google Gemini `gemini-3.5-flash` | free tier | Long context for neighbouring lines, glossary and length budget |
| Speech (candidate) | `facebook/mms-tts-tam` (MMS-TTS Tamil) on CPU | PyTorch 2.14.1 (CPU) | Real Tamil speech at zero cost; non-commercial licence |
| Voice cloning | Not implemented (mock only) | — | Needs ADR 0018 and a consented speaker first |
| Deployment | Docker Compose files + development script | — | Written but **not yet run**; development uses embedded PostgreSQL 17 binaries |
| Testing | Django test runner, pytest (black-box) | — | Unit, integration, web-layer and boundary-value tests |
| Diagrams | Mermaid (rendered with mermaid-cli 11.4.2) | — | Text-based diagrams kept in version control |

**Hardware used for development:** Intel Core i5-13450HX (10 cores / 16 threads), 14 GiB RAM, Ubuntu
26.04.1 LTS, no GPU. This is the machine on which all measured results in Chapter 4 were produced.

## 3.5 Module Description

The system is divided into nine Django apps. Apps call each other **only** through `services.py`
functions, and Django signals are not used, so every cross-module call is explicit and traceable.

**Table 3.3 — Modules (Django apps) and their responsibilities**

| Module | Owns (data) | Key code | Responsibility |
|---|---|---|---|
| `accounts` | User, ProjectMembership, Policy | `permissions.py` | Identity of users, project-scoped roles, policy values, rate-limited login. Role checks used by every service live here |
| `projects` | Project, AudienceProfile, GlossaryTerm, Video, SpeakerTrack | `services.upload_video`, `storage.LocalMediaStorage` | Project creation and configuration, upload validation with ffprobe before storage, media storage behind an interface |
| `localization` | Scene, Segment, Localization, SegmentTranslation, CheckResult | `services.localize_scene`, `checks.py` | Scene planning, context-aware localization, append-only translation versions, critical-content checks |
| `rendering` | SynthesisedSegment, RenderedScene | `services.render_scene` | Resolve the voice mode per speaker from consent and policy, synthesise, fit timing, mix, render a scene preview |
| `review` | Review, RegenerationRequest, Approval | `services.approve`, `request_changes` | Human review, overrides with reasons, scene acceptance, scene-only regeneration, the approval gate and snapshot |
| `identity` | IdentityOwner, Consent, VoiceProfile, OfflineCopy | `services.evaluate`, `demo.py` | Consent versions, the single consent decider, the revocation cascade, demo reset and withdrawal |
| `exports` | Export | `services.request_export`, `build_export` | Package building (MP4, SRT, VTT, script, quality report, evidence manifest) and export validation |
| `audit` | AuditRecord, AuditChainHead | `services.record`, `verify_chain` | The single audit writer, the hash chain, and chain verification |
| `pipeline` | Job, ProviderConfig, ProviderUsage | `jobs.py`, `handlers.py`, `inference.py`, `providers/` | Job queue and workers, provider chains, inference subprocess, usage ledger and quota warnings |

**Cross-cutting modules:** `media_tools.py` (ffprobe/ffmpeg wrappers), `pipeline/quota.py` (free-quota
warnings at 80% and 100%), and the management commands `run_worker`, `seed_demo`, `check_providers`,
`build_demo_seed`, `demo_reset`, `verify_audit_chain`, `download_models`.

**Table 3.4 — Consent checkpoints CP0–CP10 (ADR 0006)**

| Checkpoint | Where it is checked | Behaviour on failure |
|---|---|---|
| CP0 | Before source audio leaves the laptop (external ASR only) | Local ASR is used instead; audited |
| CP1 | Any API request that would use identity | Refused; `CONSENT_DENIED` recorded |
| CP2 | Job claim, in the same transaction | Job CANCELLED |
| CP3 | Before a reference clip is uploaded to a remote GPU | Cancelled; nothing uploaded |
| CP4 | Before synthesis of each segment | Stop; job CANCELLED |
| CP5 / CP7 | Saving synthesised audio / a rendered scene (row-locked) | Data discarded |
| CP6 | Before scene render and mix | Job CANCELLED |
| CP8 | Approval: every consent version in the snapshot is still latest and ACTIVE | Approval refused |
| CP9 | Before export build and when saving it (row-locked) | Export refused |
| CP10 | Serving previews and downloads | HTTP 410 Gone with an explanation |

CP0 and CP3 are designed but have no code path yet, because no provider that sends audio off the
machine is integrated. This is reported as a limitation, not hidden.

---

# Chapter 4: Implementation and Results

## 4.1 Implementation Details

### 4.1.1 Asynchronous job pipeline

Jobs are rows in a `Job` table with states QUEUED, RUNNING, SUCCEEDED, FAILED and CANCELLED
(DISPATCHED is reserved for a future remote runtime). A worker claims the next job with
`SELECT … FOR UPDATE SKIP LOCKED`, and the consent check CP2 executes in the same transaction, so a
job cannot be claimed on behalf of a speaker whose consent has just been revoked. Transient provider
errors are retried with back-off (5 s, 30 s, 120 s); a stale heartbeat returns a job to the queue; a
`cancel_requested` flag is checked at every checkpoint. Separate lanes (`default`, `synthesis`) keep
slow speech synthesis from starving analysis and localization work.

The web process never waits for a model: it writes rows and enqueues jobs, and the pages poll for
state with htmx. This is the implementation of the project rule "never block a web request on a long
process".

### 4.1.2 Upload validation and video analysis

On upload the file is validated with **ffprobe before it is stored**: it must be a readable container
with a video stream, supported codecs, duration ≤ 5 minutes and size ≤ 500 MB. Invalid files are
rejected without entering media storage. The analysis job then extracts the audio, obtains the
transcript (from a human-made SRT/VTT if supplied, otherwise from faster-whisper `small` on CPU,
otherwise from a labelled mock in test/development), detects shot cuts with ffmpeg's scene-change
score, and plans scenes.

**Scene planning** (`localization.services.plan_scenes`) places a boundary between two segments when
( a ) a shot cut falls in the gap, ( b ) the pause is at least 1.5 s, or ( c ) the scene would exceed
30 s. The boundary sits at the cut, or else in the middle of the pause; scenes are contiguous and
cover the whole video. These thresholds are implementation choices and have not been tuned.

### 4.1.3 Context-aware localization

For every segment the request contains the source text, two neighbouring segments on each side, the
speaker, the audience profile, the glossary, the timing budget and any reviewer instruction. The
budget is computed from the target voice's **measured speaking rate** — 11 characters per second for
MMS-TTS Tamil, derived from a measured median of 11.95 characters per second over 20 lines — so the
model is told how much speech can actually fit. The model must preserve every number, unit, negation,
warning and instruction, and must mark a line TOO_LONG if it cannot fit.

Quota-safe batching: the Gemini free tier allows roughly 20 requests per day per model (measured), so
a localize job sends the whole clip in one request when it fits (at most 80 segments and 12,000
characters) and the meaning check is one further request. If a real provider fails (quota, outage,
malformed output), the chain **does not** fall back to mock text: scenes stay PENDING, the page shows
"Translation pending … Nothing was machine-translated by a MOCK", and a Retry button is offered.
Gemini is permitted only for projects classified as scripted team content, or as published public
content with a recorded source URL and licence (ADR 0021).

### 4.1.4 Critical-content checks

`localization/checks.py` implements a language-neutral framework: a source-language number reader
plus a target language pack (Tamil). Numbers are read on both sides and compared as multisets; units
come from a lexicon with forms per language; glossary forms are matched by prefix so inflected Tamil
forms still match; structural checks catch empty, untranslated and mostly-Latin-script output; and a
speech-overrun check runs after real synthesis.

**Table 4.1 — Critical-content checks and their effects**

| Check | How it works | Result |
|---|---|---|
| Numbers | Digits, groupings, times and number words are read on both sides and compared as multisets; Tamil number words 0–100 are parsed (draft lexicon, pending a Tamil rater) | FAIL on mismatch; UNVERIFIABLE where words cannot be read safely |
| Units | Lexicon with forms per language; a declared unit conversion deliberately returns UNVERIFIABLE (fail-safe) | FAIL / UNVERIFIABLE / PASS |
| Glossary | Target forms matched by prefix, so inflected forms still match; a term with no target forms is never PASS | FAIL / UNVERIFIABLE |
| Structure | Empty, untranslated, mostly Latin script for a non-Latin target, or over the reading-time budget | FAIL |
| Speech overrun | After real synthesis, a line that still needs more time than its slot at 1.2× tempo (100 ms tolerance) | FAIL: "shorten the speech script" |
| AI meaning flag | `MeaningCheckProvider` flags possible meaning reversals, such as a dropped negation | Requires reviewer acknowledgement; never called verification |

A FAIL or UNVERIFIABLE result **blocks approval** until the text is fixed or a reviewer overrides it
with a written, audited reason. Known limitation, stated openly: the numbers check compares counts,
not positions, so turning "2 tablets 3 times" into "3 tablets 2 times" still passes and must be
caught by the reviewer.

### 4.1.5 Rendering, timing fit and intelligibility proxy

`rendering.services.resolve_mode` decides the voice **on the server, per speaker**:

1. SUBTITLES_ONLY if policy forbids synthesis;
2. otherwise CLONED_VOICE only if consent is valid, an active reference clip exists, policy allows
   cloning and a cloning adapter is available;
3. otherwise STOCK_VOICE.

The reason is shown to the reviewer, so the mode is explainable rather than implicit. The stock voice
is MMS-TTS Tamil on CPU; it refuses unspeakable text (digits or Latin letters) instead of silently
dropping content. If speech is longer than its slot the tempo is raised, at most to 1.2×. Every
synthesised line is transcribed back with faster-whisper and its character error rate is stored as a
**clearly labelled intelligibility proxy** — not a listening test, and pessimistic because it includes
Whisper's own errors. The scene preview is an MP4 with the original picture, the original audio ducked
under the new speech, and soft subtitles.

### 4.1.6 Consent gate, revocation cascade and mid-job stop

`identity.services.evaluate` is the only consent decider in the system. Identity use is allowed only
if all of the following hold:

- the owner has not withdrawn;
- the latest **project** consent is ACTIVE, unexpired, and includes the requested use and language;
- it has a parent **standing** consent;
- the latest standing consent is ACTIVE, unexpired, and permits the project's purpose (a rehearsal
  needs both STANDARD and DEMO_REHEARSAL);
- the project consent is still within the standing consent;
- the job is not flagged for cancellation.

Saving artefacts re-runs the gate under a row lock on the IdentityOwner, so a consent change cannot
race a write.

On revocation, **one transaction** sets affected scenes to NEEDS_REGENERATION, cancels render jobs,
quarantines that owner's artefacts in that project, marks reference clips DELETED, invalidates only
the approvals and exports that contain that owner's identity, and queues a purge. After commit,
stock-voice fallback renders are queued and must be reviewed again. A fixed lock order (IdentityOwner
→ Localization → Scene → Job → artefacts → Export → AuditChainHead) prevents deadlocks. While a
synthesis subprocess runs, the worker polls the cancel flag and the consent gate about once a second
and kills the subprocess on cancel; a test with a real subprocess passes inside an **8-second bound**
(the exact stop time was not recorded). Exports already downloaded cannot be recalled, and the system
documentation states that plainly.

### 4.1.7 Review, approval and export gates

A reviewer's edit creates a new HUMAN version and re-runs the checks and the preview; regeneration
targets one scene only — its script (with an instruction such as "use simpler words") or its preview.
A scene can be accepted only when it has no open checks and a current preview.

Approval (`review.services.approve`) is refused unless **all** of these hold:

- every scene is accepted;
- no blocking checks remain on the latest versions;
- every preview is current;
- consent checkpoint CP8 passes;
- separation of duties: the approver did not edit any segment in this version.

Approval freezes an immutable snapshot of the exact version identifiers; any later change invalidates
it. Export is refused if the approval is invalid, if **any artefact in the snapshot is MOCK**, if any
artefact is quarantined, or if CP9 fails. The exported package contains the localized MP4, SRT and VTT
subtitles tagged with the target language, `script.json`, `quality_report.json` and
`evidence_manifest.json` (hashes, providers, rendering modes, consent versions, reviews, provenance,
intelligibility proxy and the audit chain head).

### 4.1.8 Audit hash chain

Every governance action — consent grant, narrowing, revocation, approval, regeneration, export — is
written by one function (`audit.services.record`). Each record stores the previous record's hash, and
its own hash is `SHA-256(prev_hash + canonical_json(record))`. Appends are serialised by locking a
single chain-head row. PostgreSQL triggers reject UPDATE, DELETE and TRUNCATE on the audit table.
`verify_audit_chain` recomputes the entire chain, and every export manifest carries the current chain
head. The design is **tamper-evident, not tamper-proof**: someone with full database rights could
rebuild the whole chain, which is precisely why the head is also copied into each exported package.

### 4.1.9 Provider abstraction and labelled mocks

Each AI stage is an interface with an ordered chain of adapters that the Administrator can reorder.
Mocks exist only in development and test modes, are named as mocks, carry an `is_mock` flag, show a
MOCK badge in the interface, and can never be exported. A free-quota ledger warns the Administrator
at 80% and 100% of limits they enter; nothing is blocked by a warning.

**Table 4.2 — Provider chains and labelled mocks**

| Stage | Real / candidate adapter | Mock (development and tests only) | Status |
|---|---|---|---|
| Transcription | Human SRT/VTT; faster-whisper `small` on CPU | `MockTranscriptionProvider`: "[MOCK] Transcript segment N." every 4 s | Candidate run on real clips |
| Localization | Gemini `gemini-3.5-flash` (prompt with context and budget) | `MockTranslationProvider`: copies the source, applies glossary targets, prefixes "[MOCK]" | Candidate; quality not measured |
| Meaning check | Gemini batch check | `MockMeaningCheckProvider`: negation keyword rule (not AI) | Candidate |
| Stock voice | MMS-TTS Tamil on CPU | `MockStockVoiceProvider`: 440 Hz tone | Candidate, accepted in ADR 0021 |
| Cloned voice | None yet (ADR 0018 pending) | `MockClonedVoiceProvider`: 660 Hz tone; imitates no one | Mock only |

## 4.2 Screenshots of the Application

> Insert each screenshot at approximately half to two-thirds of a page, with the caption below it.
> The screenshots in `docs/screenshots/` were captured on 2026-10-12 from a throwaway seeded database
> and therefore show MOCK output — the purple banner and MOCK badges are part of the honest-labelling
> design. Say so in the caption or in the text; do not present them as real-model output.

**Figure 4.1 — Localization Manager: project list.**
Shows projects with their language pair, status and the "create project" action. The status column
distinguishes draft, in-review, approved and exported.

**Figure 4.2 — Localization Manager: project detail with the approval gate.**
Shows the scene list, the check summary, the consent state and the disabled/enabled Approve action
with the reason it is blocked. This is the visual form of the approval gate described in §4.1.7.

**Figure 4.3 — Reviewer: scene review.**
Shows the preview player, the source and target text, the per-segment check results, the override
reason field, the acknowledge controls for AI flags, and the accept/regenerate actions.

**Figure 4.4 — Speaker / Identity Owner: consent page.**
Shows standing and project consent versions with uses, purposes, languages, processors and expiry,
the revoke action, and the reference-clip status.

**Figure 4.5 — Auditor: audit trail.**
Shows the filterable audit records (who, what, when, project, scene, consent version) and the
on-demand chain verification result.

**Figure 4.6 — Administrator: policies, provider chains and quota warnings.**
Shows provider ordering per stage, policy values, and the 80% / 100% free-quota warnings. Users and
memberships are managed through the Django admin (the seeded `admin` is staff and superuser).

**Figure 4.7 — Media Operator: job queue.**
Shows job states (QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELLED), lanes, attempts and heartbeats.

**Figure 4.8 — Clip 01 timing chart.**
Bar chart of Tamil speech length ÷ slot length for the 14 lines of the trial in §4.3; a bar at 1.0
fits, a bar above 1.0 overruns. Regenerate from `docs/submission/source/chart.js`.

## 4.3 Sample Inputs and Outputs

### 4.3.1 Sample input

The demonstration input is a **public-domain / CC BY 3.0** English health-information video:
`test_datasets/01_handwashing_sf_health_dept_en` — 58.4 seconds, 1280×960, from San Francisco
Government Television, with its source URL, licence and attribution recorded in the project (required
by ADR 0021 for published public content). The project target audience profile is Tamil, formal
register, adult general audience, with a small glossary of required health terms. It is transcribed
into **14 segments across 2 scenes**.

A second, later run used the same clip and is the most recent verified end-to-end state (2026-10-29):
faster-whisper `small-int8` transcribed 14 segments in 2 scenes, Gemini `gemini-3.5-flash` localized
**14 of 14 segments**, and `facebook/mms-tts-tam` produced 14 real Tamil stock-voice clips.

### 4.3.2 Sample output

**Scene previews (real, non-mock), measured with ffprobe on 2026-10-29:**

| Property | Scene 1 | Scene 2 |
|---|---|---|
| Video codec | H.264 | H.264 |
| Audio codec | AAC | AAC |
| Dimensions | 1280 × 960 (source dimensions preserved) | 1280 × 960 |
| Actual duration | 28.120 s | 30.244 s |
| Expected duration | 28.120 s | 30.244 s |
| Subtitles | served as VTT | served as VTT |

Both scenes are `IN_REVIEW`. **No one accepted or approved them**, and the system correctly prevents
export at this point. The render path uses the source video stream and mixes the original audio at
25% under the target speech.

**Export package contents (built when a human approves and exports):**

| File | Contents |
|---|---|
| `localized.mp4` | Original picture, original audio ducked under target speech, soft subtitles, tracks tagged `tam` |
| `subtitles.srt`, `subtitles.vtt` | Target-language subtitles with source-aligned timings |
| `script.json` | Per-segment source and target text, origin (AI/HUMAN), adaptation type, rationale, context inputs |
| `quality_report.json` | Every check result, overrides, acknowledgements, intelligibility proxies |
| `evidence_manifest.json` | Hashes, providers and models, rendering modes, consent versions, reviews, provenance, audit chain head |

**Quality findings from the 2026-10-29 run (real output, unresolved):** six checks remained open —
three `speech_overrun` failures, two AI `omission` flags and one `numbers_speech` UNVERIFIABLE result.
The audit chain verified successfully afterwards (726 records). These findings are the intended
behaviour: the gate refused to let the project proceed to approval until a human resolves them.

### 4.3.3 Sample check behaviour (input → output pairs)

These are the actual behaviour of the check functions, and correspond to the test cases in §4.4:

| Input | Condition | Output |
|---|---|---|
| Source "Give 2 sachets", target with 5 | Numbers differ | FAIL (blocks approval) |
| Source "2 tablets 3 times", target "3 tablets 2 times" | Counts equal, positions swapped | PASS — a known limitation; the reviewer must catch it |
| Correct translation with all numbers preserved | Numbers match as multisets | PASS |
| Target left empty, or an untranslated copy of the source | Structural check | FAIL |
| Correct translation for a language pair with no verification pack | Unsupported pair | UNVERIFIABLE (fail-safe, blocks approval) |
| Reading-time budget for a 1-second line (28 characters) | 28 characters / 29 characters | PASS / FAIL (boundary) |
| Latin-script share exactly 50% / 60% for a Tamil target | Boundary values | PASS / FAIL |
| Gemini returns HTTP 429 daily quota | Provider failure | Scenes stay PENDING, no MOCK text, Retry shown |

### 4.3.4 First real-clip trial: measured observations (n = 1)

The first complete real run of the pipeline (2026-10-22, prior to the fixes in Table 4.7) produced
these numbers. They are directional evidence from one 58-second clip, **not** a quality evaluation.

| Observation | MEASURED RESULT |
|---|---|
| Lines translated by Gemini | 14 of 14, after two fallbacks on scene 2 (HTTP 429 per-minute, then HTTP 503) |
| Timing fit (±15% of slot) | **2 of 14 lines** |
| Total speech vs available slots | 79.1 s of Tamil speech against 58.0 s of slots (tempo cap was 1.15× at the time) |
| Intelligibility proxy (Whisper back-transcription CER) | **0.16** over 850 characters (pessimistic; includes Whisper's own errors) |
| MMS-TTS Tamil speaking rate | median **11.95 characters/s** over 20 lines (range 9.4–14.6) |
| Numbers and negation preserved | 1, 2, 3, 20 and 60% and "don't have soap" were kept; this reading is UNVERIFIED until a Tamil-literate rater checks it |

**Table 4.7 — Problems found in the first real run and the design changes made**

| Problem observed | Change made |
|---|---|
| One meaning-check call per line exhausted the free tier; on 429/503 the chain silently fell back to MOCK text | Batch the whole clip into one localization request and one meaning-check request (about 16 → 2 requests); never fall back to MOCK after a real provider fails; show "translation pending" with Retry |
| Only 2 of 14 lines fitted their slot | Length budget in the prompt (11 chars/s × time available); tempo cap raised to 1.2×; blocking speech-overrun check |
| Export tracks tagged `und` (undetermined) | Audio and subtitle tracks tagged with the target language (`tam`) |
| Tamil number words were unverifiable | Draft parser for Tamil number words 0–100; a wrong number word now FAILS |

## 4.4 Unit Testing and Results

### 4.4.1 Testing strategy

Testing follows the project rule that every important component is tested, and that consent
enforcement and state transitions have **explicit** tests written *negative-first*: every way the gate
must refuse is tested before the way it allows. The suite runs on real PostgreSQL 17 and real ffmpeg,
with MOCK AI providers and synthetic media; test mode is forced so that no test can reach the real
Gemini API (a real leak of quota through an earlier test suite was found and fixed).

- **Unit tests:** number parsing, units, glossary matching, structural checks, scene planning,
  provider chains, quota logic, audit hashing.
- **Integration tests:** full workflows through the service layer, identity workflows and revocation.
- **Web-layer tests:** pages per role, 403 for outsiders, wrong-role POSTs, previews only for members,
  HTTP 410 after revocation, login rate limiting, retention sweeps.
- **End-to-end test:** `scripts/e2e_check.py` drives a live server and worker over HTTP.
- **Black-box tests:** equivalence partitioning and boundary value analysis on the check functions,
  using only inputs and outputs.

### 4.4.2 Test areas

**Table 4.3 — Test areas covered by the automated suite**

| Area | File | What is proven |
|---|---|---|
| Audit chain | `audit/tests.py` | Chain links and verifies; UPDATE, DELETE and TRUNCATE rejected by the database; tampering detected with the trigger disabled; no raw content stored |
| Consent gate | `identity/tests.py` | No consent, no standing consent, Administrator grants, wider-than-standing, wrong use or language, revoked, expired, old version after revocation, narrowing, final withdrawal, expiry sweep |
| Workflow | `tests/test_workflow.py` | Scenes at shot cuts; context inputs recorded; checks block acceptance; overrides need a reason and the reviewer role; scene-only regeneration; approval gate; separation of duties; MOCK never exportable; an edit after approval invalidates it |
| Identity in workflow | `tests/test_identity_workflow.py` | Cloned mode with consent; stock fallback without; revocation cascade quarantines, purges and falls back; scope isolation; a real mid-job kill of the inference subprocess |
| Review regressions | `tests/test_review_fixes.py` | Regressions for the independent code review (1 blocker, 6 major): two-owner mid-job stop, withdraw vs reset in both orders, and more |
| Demo reset | `tests/test_demo_reset.py` | Administrator only; rebuild only appends; refusals for purpose, drift and withdrawal; offline-copy permission |
| Web layer | `tests/test_views.py` | Per-role pages, 403s, CP10 410 after revocation, admin-only policies, login rate limit, retention sweeps |
| Providers and quota | `pipeline/tests.py`, `tests/test_quota.py` | Mocks absent in demo mode; chain fallback and ordering; data-use rule; Gemini parsing against a fake HTTP layer; 80% / 100% quota boundaries |
| Checks | `localization/tests.py` | Numbers (digits, words, Tamil digits, Indian grouping), units, conversions, glossary, structure, scene planning |
| Published-content rules | `tests/test_published_public.py` | Provenance required for published content; MOCK meaning check visible in the quality report; export refusal rules |

### 4.4.3 Sample test cases

**Table 4.4 — Sample unit and integration test cases (all part of the passing suite)**

| ID | Test case | Input / condition | Expected result | Result |
|---|---|---|---|---|
| TC01 | Upload validation | Corrupt or unsupported file | Rejected before storage | Pass |
| TC02 | Number mismatch | Source "Give 2 sachets", target with 5 | Numbers check FAIL; approval blocked | Pass |
| TC03 | Override needs a reason | Override without a reason, or by a non-reviewer | Refused | Pass |
| TC04 | Scene acceptance | Accept a scene with open checks | Refused | Pass |
| TC05 | Separation of duties | The manager who edited a segment approves | Refused; another manager must approve | Pass |
| TC06 | MOCK export | Approved snapshot contains MOCK output | Export refused | Pass |
| TC07 | Administrator grants consent | Admin tries to grant on behalf of a speaker | Refused | Pass |
| TC08 | Revocation mid-job | Revoke while a cloned-voice subprocess runs | Subprocess killed; job CANCELLED within the 8 s bound | Pass |
| TC09 | Preview after revocation | Request a revoked preview | HTTP 410 Gone | Pass |
| TC10 | Audit tampering | UPDATE/DELETE an audit row; edit with the trigger disabled | Rejected; verifier detects the change | Pass |
| TC11 | Provider quota failure | Gemini returns 429 daily quota | Scenes PENDING, no MOCK text, Retry shown | Pass |
| TC12 | Edit after approval | Reviewer edits a segment after approval | Approval INVALIDATED | Pass |

The black-box suite additionally checks equivalence classes (valid translation; changed number;
missing number; empty target; untranslated copy; unsupported language pair) and boundary values
(28 vs 29 characters for a 1-second budget; 50% vs 60% Latin-script share; a single-character
translation).

### 4.4.4 Measured test results

**Table 4.5 — Measured test results**

| Suite | Date | MEASURED RESULT |
|---|---|---|
| Full application suite (`manage.py test hyperlocalize`) | 2026-10-22 | **210 passed, 2 skipped** (optional real-model tests), 125 s |
| Focused suite after provider and language changes | 2026-10-29 | **75 passed, 1 optional skip** |
| Black-box suite (`pytest blackbox_testing/`) | 2026-10-22 | **11 passed** |
| End-to-end over HTTP (`scripts/e2e_check.py`) | 2026-10-06 | **15 / 15 steps passed**: consent, cloned (MOCK) preview, review, approval, MOCK export refused, revocation (410, approval invalidated, fallback, clip deleted), subtitles-only export, auditor verifies the chain |
| Spike evaluation tooling (`spike/`) | 2026-10-05 | 75 passed, 1 skipped (synthetic inputs only) |
| UML render check | 2026-10-12 | All 10 Mermaid diagrams render |

**Honest note on the test numbers.** The 210-test full run is the latest *full-suite* measurement; it
predates the newest upload-first UI and dev mock-gating changes. Those later changes were checked with
`manage.py check`, template compilation and a 75-test focused run, not with a full database-backed
suite (the approval gate prevented creating a disposable test database). The report states this
rather than implying a single continuous green run.

**Table 4.6 — Evaluation metrics: TARGET versus MEASURED RESULT**

| Metric | Definition | TARGET | MEASURED RESULT |
|---|---|---|---|
| M1 Transcription accuracy | WER / critical-token errors on the test clip | Fixed in the spike plan | **NOT MEASURED** (no consented recording yet) |
| M2 Translation quality | MQM points per 100 words; pairwise preference; chrF | Fixed in the spike plan | **NOT MEASURED** (needs a Tamil-literate rater) |
| M3 Rule-check catch rate | Share of seeded errors caught | Fixed in the spike plan | **NOT MEASURED** (seeded set not written) |
| M4 Speech quality and similarity | Naturalness; pronunciation; speaker similarity | Fixed in the spike plan | **NOT MEASURED**; proxy only: CER **0.16** (clip 01, stock voice) |
| M5 Timing fit | Share of segments within ±15% of their slot | Assumed working threshold | Pre-spike clip 01: **2 / 14** lines |
| M6 Speed | Model load, per-segment time, peak RAM | Fixed in the spike plan | **NOT MEASURED** |
| Consent enforcement | Identity use refused in every denied state; revocation stops a running job | All denied states refused; stop within seconds | Every tested denied state refused; mid-job stop inside the 8 s test bound (exact time not recorded) |
| Review-gate integrity | No approval with open checks, unaccepted scenes, stale previews or invalid consent; no MOCK export | 0 bypasses | **0 bypasses** in the tested cases |
| Audit integrity | Edits rejected; tampering detected | Detected | Rejected and detected in the tested cases |
| Context ablation | Context on vs off vs plain MT | Show whether context helps | **NOT MEASURED** |

### 4.4.5 Not yet tested

- Any real AI model on real data *at evaluation scale* — only the single-clip trial and one
  end-to-end preview run exist.
- The Docker images (Docker is not installed on the development laptop; the Compose files are written
  but have never been run).
- Browser interaction beyond page loads (forms were not submitted by an automated browser test).
- Performance and load.

---

# Chapter 5: Conclusion and Future Enhancement

## 5.1 Summary of the Work

The project set out to build a controlled video localization workflow rather than another automatic
dubbing script, and that is what was delivered. All nine use cases are implemented on the MVP path
and covered by automated tests:

| Use case | State at the time of writing |
|---|---|
| UC1 Create and Generate a Localization Project | Implemented and tested |
| UC2 Upload and Analyze Source Video | Implemented and tested (ffprobe validation, limits, shot cuts, scenes; no speaker diarization) |
| UC3 Generate Context-Aware Localization Preview | Real English → Tamil preview verified; other pairs unverified; visual context not implemented |
| UC4 Generate Localized Preview | Real Tamil stock voice verified; cloned voice still a mock |
| UC5 Review and Regenerate a Scene | Implemented and tested |
| UC6 Approve and Export Localization Package | Implemented and tested (gate, snapshot, separation of duties, MOCK refused) |
| UC7 Revoke Consent and Stop Identity | Implemented and tested with mock voices (cascade, mid-job kill, purge, withdrawal, expiry) |
| UC8 Administer Users, Providers and Policies | Implemented and tested (policies, provider chains, quota warnings) |
| UC9 Inspect Quality, Audit and Evidence | Implemented and tested (filters, chain verification, overrides) |

The system is a Django modular monolith of nine apps on PostgreSQL 17, with a database job queue,
server-rendered pages with htmx, and every AI stage behind a provider interface. It has been exercised
end to end on a real public video with real transcription, real translation, real Tamil speech
synthesis and real MP4 scene previews. The governance mechanisms — consent gate with revocation
cascade, review and approval gates, and the hash-chained audit trail — are the parts backed by the
strongest evidence, because there are tests that specifically try to break them.

## 5.2 Conclusion

HyperLocalize demonstrates that video localization can be built as a **controlled, accountable
workflow around commodity AI models**, and that doing so changes what the system makes visible. In the
first real run, the workflow exposed problems a pure pipeline would have shipped silently: only 2 of
14 lines fitted their time slots, one meaning-check call per line exhausted the free tier, and the
exported tracks were tagged with an undetermined language. Each finding was turned into an explicit
design change and a test. In the later run, the real previews again stopped at Human Review with six
open checks — three speech overruns, two omission flags and one unverifiable number — which is the
intended behaviour of a system that refuses to release unchecked machine output.

The project therefore supports its governance claims more strongly than its quality claims. Consent
enforcement, the review gate, export refusal for placeholder output and audit integrity are
demonstrated by automated tests, including a real subprocess kill on revocation. Translation quality,
speaker similarity, speed and the benefit of context have **not** been measured; the only real-data
figures are directional results from one 58-second clip. These gaps are stated in the report rather
than hidden, because a localization system for critical information is only as trustworthy as its
willingness to admit what it has not verified.

## 5.3 Future Enhancements

1. **Run the planned evaluation.** With consented Speakers A and B and two Tamil-literate raters,
   measure WER, MQM, chrF, seeded-error catch rate, listening-test naturalness and speaker similarity,
   timing fit and speed, and record the results against the thresholds fixed in advance.
2. **Measure whether context actually helps.** Run the context ablation: context on, context off, and
   a plain machine-translation baseline (IndicTrans2, once model access is granted).
3. **Choose the voice-cloning provider from evidence** (ADR 0018), or keep stock voice and
   subtitles-only if cloning fails the thresholds.
4. **Re-measure timing fit** after the length-budget and overrun changes, and add a Whisper baseline
   on natural Tamil speech so the CER proxy can be interpreted.
5. **Close the open engineering findings:** move the meaning-check network call out of the consent
   lock, count every HTTP attempt (including retries and failures) in the quota ledger, compare number
   *positions* as well as counts, and add speaker diarization.
6. **Add visual context** (keyframes and on-screen text OCR) and **more language pairs**, including
   several target languages per project.
7. **Run and document the Docker Compose deployment**, and extend the automated browser test to submit
   forms rather than only load pages.
8. **Lip-sync and face processing remain future scope**, and would require their own consent design
   before any implementation.

---

# References

[1] A. Radford, J. W. Kim, T. Xu, G. Brockman, C. McLeavey and I. Sutskever, "Robust Speech
Recognition via Large-Scale Weak Supervision," arXiv:2212.04356, 2022.

[2] J. P. Gala et al., "IndicTrans2: Towards High-Quality and Accessible Machine Translation Models for
all 22 Scheduled Indian Languages," Transactions on Machine Learning Research, 2023.

[3] V. Pratap et al., "Scaling Speech Technology to 1,000+ Languages," arXiv:2305.13516, 2023.

[4] J. Kim, J. Kong and J. Son, "Conditional Variational Autoencoder with Adversarial Learning for
End-to-End Text-to-Speech," in Proc. ICML, 2021.

[5] A. Lommel, H. Uszkoreit and A. Burchardt, "Multidimensional Quality Metrics (MQM): A Framework
for Declaring and Describing Translation Quality Metrics," Tradumàtica, no. 12, 2014.

[6] M. Popović, "chrF: character n-gram F-score for automatic MT evaluation," in Proc. Tenth Workshop
on Statistical Machine Translation, 2015.

[7] Coalition for Content Provenance and Authenticity (C2PA), "C2PA Technical Specification,"
c2pa.org.

[8] M. Nygard, "Documenting Architecture Decisions," 2011 (the ADR format used in this project).

[9] Django Software Foundation, "Django documentation," docs.djangoproject.com.

[10] The PostgreSQL Global Development Group, "PostgreSQL 17 Documentation: SELECT … FOR UPDATE SKIP
LOCKED; CREATE TRIGGER," postgresql.org/docs/17.

[11] SYSTRAN, "faster-whisper," github.com/SYSTRAN/faster-whisper.

[12] Meta AI, "facebook/mms-tts-tam" model card (CC-BY-NC-4.0), huggingface.co.

[13] Google, "Gemini API documentation and free-tier terms," ai.google.dev.

[14] htmx, "htmx documentation," htmx.org.

[15] FFmpeg project, "FFmpeg documentation (ffprobe, scene detection, atempo)," ffmpeg.org.

[16] Wikimedia Commons, source pages and licences of the twelve test videos, listed in
`test_datasets/README.md`.

---

## Notes for you before submission (delete this section)

1. **Fill every placeholder on the cover page** and in the certificate/declaration pages.
2. **Insert the figures.** Render the Mermaid blocks from `docs/uml/README.md` with mermaid.live or
   mermaid-cli; the six screenshots are already in `docs/screenshots/`.
3. **Keep the honesty wording.** Remove the "not measured" rows only if a measurement actually
   replaces them; the project's own rules require the gaps to be visible.
4. **Do not describe the 2026-10-22 export as human-reviewed.** It was reviewed by the AI assistant
   in a test run and later withdrawn (`AGENT_REVIEW_WITHDRAWN`). The 2026-10-29 run has not been
   approved at all. If the report needs an export screenshot, wait until you have personally reviewed
   and approved a project.
5. **Check the declaration** against your college's policy on AI-assisted development.
