# User manual: demo walk-through

This walk-through uses the demo scenario: a synthetic video (test patterns and a tone, with no real person) and the English ORS script, localized into Tamil. The script's health facts are [UNVERIFIED] and **it is not health advice**. In DEV mode a purple banner reminds you that MOCK providers are active: mock text starts with `[MOCK`, mock voices are beeping tones, and mock output can never be exported.

Start the app and seed it first (see `README.md`). Keep a worker running: `scripts/run_dev.sh` starts one.

## 1. Media Operator (`operator`): source and analysis

- `seed_demo` has already uploaded the demo video with a **human-made transcript**.
- For your own project, open it and use **Source video**: choose an MP4/MOV/MKV/WebM (MVP limit: 5 min / 500 MB). You can add an SRT or VTT transcript.
- Invalid files are rejected **before** anything is stored.
- The **Jobs** panel updates every 2 s and shows analysis → localization → previews.
- Under **Speakers and identity**, link a speaker to an identity owner. **Linking grants nothing**: the server uses a cloned voice only while that person's own consent is valid.

## 2. Localization Manager (`manager`): project, context, people

- **New project:** set the name, the languages, the audience (formality, reading level, cultural notes), and the data classification. Only "scripted, team-authored" content may be sent to a free-tier hosted LLM.
- **Glossary:** add source terms. Their target forms and accepted inflected forms come from a rater who reads the target language. A term with no forms is reported as *unverifiable*, never as passed.
- **Members:** add users by username and role.
- **Invite an identity owner:** link an existing account. They grant consent themselves.

## 3. Reviewer (`reviewer`): human review and regeneration

Open **Review** on a scene. You see:
- the **preview**, with subtitles;
- for each segment: the source, the localized draft, the adapter that produced it (with a MOCK badge if it was a mock), the model's *stated* reason, and the **context inputs used**;
- **checks:**
  - red *rule* checks (numbers, units, glossary, structure) **block approval**. Fix the text, or *override* with a written reason (audited);
  - amber *AI flags* need an *acknowledgement* that says what you checked.

Actions:
- **Edit** a segment. This saves a new HUMAN version, re-runs the checks and re-renders the preview.
- **Request changes → regenerate this scene only.** Choose the *script* (with an instruction, such as "simpler words"), or the *preview*. Other scenes are untouched.
- **Accept scene.** This is only possible with no open checks and a current preview.

## 4. Localization Manager: approval and export

- The **Approval gate** panel lists every reason approval is blocked. It never approves automatically.
- **Separation of duties:** if you edited a segment, a different manager (`manager2`) must approve.
- **Export** builds a ZIP containing the localized MP4, SRT and VTT subtitles, `script.json`, `quality_report.json`, and `evidence_manifest.json` with the audit chain head.
- **Export is refused while any approved artefact is MOCK.** To demonstrate a real export without AI models:
  - use a human transcript;
  - edit every segment (human text);
  - an Administrator sets *synthesis_allowed* off, which gives SUBTITLES_ONLY.

## 5. Speaker / Identity Owner (`speaker`): consent

On **My consent**:
1. Record a **standing consent**: uses, project kinds, languages, expiry, and the **signed form ID**. The paper form itself stays outside the system.
2. For a project you are linked to, **grant project consent**. It can't be wider than your standing consent.
3. **Upload a reference clip** (3–30 s) with its exact transcript. The preview now uses the identity-preserving voice, which in DEV mode is a MOCK tone.
4. **Revoke for this project.**
   - Running jobs stop within seconds, and your cloned audio is quarantined, then deleted.
   - Affected scenes fall back to a stock voice and must be reviewed again.
   - Only approvals and exports that contained your voice are invalidated or blocked.
   - Exports already downloaded cannot be recalled.
5. **Narrow** (remove a use, project kind, language or copy kind) or **Withdraw** (final).

A revocation inside a *Demo rehearsal* project is a demonstration. Withdrawal is the real one.

## 6. Auditor (`auditor`): quality, audit, evidence

**Audit trail and evidence:**
- filter by action;
- **Verify the whole chain**, which recomputes every hash;
- see the rule overrides and their reasons.

The chain is *tamper-evident, not tamper-proof*.

## 7. Administrator (`admin`)

- **Policies & providers:** synthesis and cloning switches, retention days, separation of duties, and the provider chain order per stage. The page shows which adapters are ready and which are MOCK.
- `/admin/` manages users and memberships only. Administrators **cannot grant consent**.

## Demo-day commands

- `manage.py check_providers`: providers, media tools and drift warnings.
- `manage.py build_demo_seed` and `manage.py demo_reset --admin admin --owner <id> --project <id>`: build a fresh rehearsal project for the revocation demo.
- `manage.py verify_audit_chain`.
