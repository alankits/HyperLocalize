# ADR 0011: Authentication and authorisation: Django sessions + project-scoped roles

**Status:** Proposed (2026-10-05). Not yet approved. It includes proposed defaults for open questions Q10 and Q13 (marked below).
**Source:** `docs/PHASE0_DISCOVERY.md` §6.9; ADR 0009

## Context

Six actors are confirmed. Permissions differ per project (someone can be a Reviewer on one project and have no access to another). Identity Owners must be able to grant and revoke **their own** consent and nothing else. Approval should not be granted by the person who made the last edit (separation of duties). The team has little security-operations experience, so well-trodden defaults are preferred.

## Options Considered

| Criterion | **Django session auth + `ProjectMembership` roles + service-layer checks** | JWT + custom RBAC | External identity provider (e.g. Keycloak) |
|---|---|---|---|
| Effort | **Low** | Medium | Medium–high (ops) |
| Pitfalls | Well known; CSRF handled by Django | Token storage and revocation | Configuration complexity |
| Per-project roles | Custom table (simple) | Custom | Custom anyway |
| Viva | **Clear** | Medium | "Why do you need this?" |

## Decision

- Django session authentication, with Django's password hashing and validators. Login is rate-limited.
- `ProjectMembership(user, project, role)` with roles `LOCALIZATION_MANAGER`, `REVIEWER`, `MEDIA_OPERATOR`, `AUDITOR`.
- Global flags: `is_administrator`; `identity_owner` (a link from a User to an IdentityOwner).
- Permission checks live in **service functions** (e.g. `review.services.approve(user, localization)`), not only in views, and every check has a test.

| Actor [CONFIRMED] | Can [PROPOSED] |
|---|---|
| Localization Manager | Create and configure the project, assign members, start generation, **approve** (UC6), export |
| Reviewer / Linguist | Edit segments, resolve or override checks (with a reason), acknowledge AI flags, review scenes, request regeneration |
| Media Operator | Upload source video, start and monitor jobs, retry failed jobs, assign speakers. **[PROPOSED default for Q12]** |
| Speaker / Identity Owner | View, grant and revoke **their own** consent; see where their identity was used. No access to project content. **[PROPOSED default for Q10: a normal account with the identity-owner link, invited by the Manager; no magic links.]** |
| Administrator | Users, provider configuration, policies (provider chain order, quota warnings, retention, whether cloning is allowed). **Cannot grant consent on anyone's behalf.** |
| Auditor | Read-only access to audit records, check results, reviews, approvals and evidence manifests (UC9) |

**Separation of duties [PROPOSED default for Q13]:** a policy, on by default, that the approver must not be the last editor of any segment in the snapshot. With a 4-person team, a demo typically uses one Reviewer and a different Manager.

## Consequences

- **+** Simple, standard and testable; the role table maps one-to-one onto the UML actors.
- **−** Identity Owners need accounts. That's fine for a team-only demo; real external speakers would need an onboarding flow (future scope).
- **−** Two-factor authentication is not in the MVP. This is stated, not hidden.
- **Viva in 2 minutes:** "Django sessions handle login. A membership table gives each user a role per project. Every action checks permission in the service layer, and consent can only be changed by the identity owner."
