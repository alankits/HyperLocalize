# UML diagrams

| Diagram | Source | Kind |
|---|---|---|
| Class diagram | [`class_diagram.md`](class_diagram.md) | **Generated from the Django models** by `scripts/generate_uml.py` (actual classes only) |
| Use cases, components, sequences, states | this file | Hand-drawn **from the implemented code**; each names the module it describes |

Labels: the **conceptual workflow** (product) is drawn as the use-case diagram. The **actual components** are the Django apps. The **actual classes** are in the generated class diagram.

## 1. Use cases (conceptual workflow; actors and UC1–UC9 are [CONFIRMED])

```mermaid
flowchart LR
  LM([Localization Manager])
  RV([Reviewer / Linguist])
  MO([Media Operator])
  IO([Speaker / Identity Owner])
  AD([Administrator])
  AU([Auditor / Faculty Evaluator])
  UC1[UC1 Create and Generate a Localization Project]
  UC2[UC2 Upload and Analyze Source Video]
  UC3[UC3 Generate Context-Aware Localization Preview]
  UC4[UC4 Generate Localized Preview]
  UC5[UC5 Review and Regenerate a Scene]
  UC6[UC6 Approve and Export Localization Package]
  UC7[UC7 Revoke Consent and Stop Identity]
  UC8[UC8 Administer Users, Providers and Policies]
  UC9[UC9 Inspect Quality, Audit and Evidence]
  RC[Record Consent «include»]
  LM --> UC1
  LM --> UC6
  MO --> UC2
  RV --> UC5
  IO --> UC7
  IO --> RC
  AD --> UC8
  AU --> UC9
  UC1 -. include .-> UC2
  UC1 -. include .-> UC3
  UC1 -. include .-> UC4
  UC5 -. include .-> UC3
  UC5 -. include .-> UC4
  UC1 -. include .-> RC
```

## 2. Components (actual Django apps, ADR 0001)

```mermaid
flowchart TB
  subgraph web[Web process: Django views + htmx templates]
    V1[projects.views]:::v --> S
    V2[review.views]:::v --> S
    V3[identity.views]:::v --> S
    V4[exports.views]:::v --> S
    V5[audit.views]:::v --> S
  end
  subgraph S[Service functions: services.py in each app]
    P[projects] --> L[localization]
    L --> R[rendering]
    R --> RV[review]
    RV --> E[exports]
    I[identity: the only consent decider]
    A[audit: the only audit writer]
  end
  subgraph W[Worker processes: run_worker --lane default / synthesis]
    J[pipeline.jobs + handlers] --> INF[inference subprocess: killable]
  end
  S --> DB[(PostgreSQL)]
  J --> DB
  S --> M[(Media storage: files/, offline/, quarantine/)]
  J --> PR[Provider adapters: MOCK / human transcript / Gemini candidate / faster-whisper candidate]
  classDef v fill:#e9f0f8
```

## 3. Sequence: the main workflow (as implemented)

```mermaid
sequenceDiagram
  actor MO as Media Operator
  actor RV as Reviewer
  actor LM as Manager
  participant Web
  participant Q as Job queue
  participant W as Worker
  participant DB
  MO->>Web: upload video (+ optional human transcript)
  Web->>Web: ffprobe validation (reject before storing)
  Web->>DB: Video + audit VIDEO_UPLOADED
  Web->>Q: analyze_video
  W->>Q: claim (SKIP LOCKED)
  W->>W: extract audio, transcribe (chain), shot cuts
  W->>DB: speakers, segments, scenes
  W->>Q: localize
  W->>W: build context per scene, localization chain
  W->>DB: SegmentTranslation v1 + hard checks + AI flags
  W->>Q: render_scene (per scene)
  W->>W: resolve mode per speaker from consent, synthesise, mix
  W->>DB: RenderedScene, scene IN_REVIEW
  RV->>Web: edit / override with reason / acknowledge / regenerate one scene
  RV->>Web: accept scene (blocked while checks are open)
  LM->>Web: approve (gate: accepted, no blocking checks, current previews, CP8, separation of duties)
  Web->>DB: Approval snapshot + audit APPROVED
  LM->>Web: export (refused if any MOCK artefact or consent invalid)
  W->>DB: CP9 under owner lock, package + manifest with chain head, audit EXPORT_CREATED
```

## 4. Sequence: revocation while a cloned-voice job runs (tested: `test_running_job_is_stopped_within_seconds`)

```mermaid
sequenceDiagram
  actor IO as Identity Owner
  participant ID as identity.services
  participant DB
  participant W as Worker (render_scene)
  participant C as Inference subprocess
  W->>C: synthesise segment (MOCK cloned voice)
  IO->>ID: revoke project consent
  ID->>DB: lock IdentityOwner, insert REVOKED version
  ID->>DB: cancel QUEUED jobs, flag RUNNING job cancel_requested
  ID->>DB: quarantine this project's cloned artefacts, invalidate approvals, block exports
  ID->>DB: scenes NEEDS_REGENERATION, queue purge + stock-voice fallback renders, audit CONSENT_REVOKED
  W->>DB: 1-second poll sees cancel / consent changed
  W->>C: kill
  W->>DB: job CANCELLED (CONSENT_REVOKED), quarantine segments saved by this job
  Note over W,DB: purge job deletes quarantined audio, render files, revoked packages, reference clips
```

## 5. State machines (as implemented)

```mermaid
stateDiagram-v2
  direction LR
  state "Scene (localization.Scene)" as Scene {
    [*] --> PENDING
    PENDING --> TRANSLATED: localized draft saved
    TRANSLATED --> IN_REVIEW: preview rendered
    IN_REVIEW --> ACCEPTED: reviewer accepts (no open checks, preview current)
    IN_REVIEW --> CHANGES_REQUESTED: reviewer requests regeneration
    ACCEPTED --> CHANGES_REQUESTED
    CHANGES_REQUESTED --> REGENERATING: render job starts
    CHANGES_REQUESTED --> TRANSLATED: script regenerated
    REGENERATING --> IN_REVIEW: new preview
    ACCEPTED --> IN_REVIEW: segment edited
    IN_REVIEW --> NEEDS_REGENERATION: consent revoked
    ACCEPTED --> NEEDS_REGENERATION: consent revoked
    NEEDS_REGENERATION --> IN_REVIEW: fallback preview (must be reviewed again)
  }
```

```mermaid
stateDiagram-v2
  direction LR
  [*] --> DRAFT
  DRAFT --> IN_REVIEW: every scene has a preview
  IN_REVIEW --> APPROVED: approval gate passes
  APPROVED --> EXPORTED: package built (CP9)
  APPROVED --> IN_REVIEW: any new version, regeneration or revocation (approval INVALIDATED)
  EXPORTED --> IN_REVIEW: same
```

```mermaid
stateDiagram-v2
  direction LR
  [*] --> QUEUED
  QUEUED --> RUNNING: claim (CP2 in the same transaction)
  QUEUED --> CANCELLED: cancel before claim
  RUNNING --> SUCCEEDED
  RUNNING --> FAILED: terminal error, or retries used up
  RUNNING --> QUEUED: transient error (back-off) or stale heartbeat
  RUNNING --> CANCELLED: cancel_requested seen at a checkpoint / subprocess killed
  note right of RUNNING: DISPATCHED (remote batch) exists in the model but no remote runtime is built
```

```mermaid
stateDiagram-v2
  direction LR
  state "Consent version (append-only rows)" as C {
    [*] --> ACTIVE: owner grants (standing, then project)
    ACTIVE --> ACTIVE: narrowing inserts a new, narrower ACTIVE version
    ACTIVE --> REVOKED: revoke / narrowing to nothing / withdrawal
    ACTIVE --> EXPIRED: expiry sweep (standing consent)
  }
```

## What these diagrams do NOT show (not implemented)

Visual context, remote GPU runtimes (Kaggle), external ASR (CP0), real TTS and voice models, and C2PA manifests.
