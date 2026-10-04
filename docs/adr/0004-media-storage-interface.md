# ADR 0004: Media storage behind an interface, local filesystem for the MVP

**Status:** Proposed (2026-10-04). Not yet approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §6.6

## Context

The system stores source videos, extracted audio, reference voice samples, synthesised audio, rendered previews and export packages. These are sensitive personal data (CLAUDE.md §5). Revocation must be able to quarantine and delete identity-derived media (ADR 0006). Hosting is still undecided (group B2, Q4/Q18).

## Options Considered

| Criterion | Local filesystem behind an interface | S3-compatible object storage (MinIO / cloud) | Database blobs |
|---|---|---|---|
| Simplicity | High | Medium | High |
| Multi-host scaling | No | Yes | Poor |
| Large video files | OK | Good | Bad |
| Time-limited download URLs | Must be built | Built in | No |

## Decision

All media access goes through a `MediaStorage` interface (save, open, delete, quarantine, exists). The MVP implementation stores files on the local filesystem:
- **outside the web root**, under random keys (no user-supplied filenames in paths);
- served only through endpoints that check authorisation and artefact status (consent checkpoint CP10, ADR 0006);
- with the SHA-256 of each file recorded in the database.

An S3-compatible implementation can be added later without changing callers. Media is never committed to git (already in `.gitignore`).

## Consequences

- **+** Simple, testable (a temporary-directory implementation for tests), and swappable.
- **+** Quarantine and deletion are explicit operations, which revocation needs.
- **−** Single machine. Backups and encryption at rest are the operator's job and are [UNKNOWN] until configured; they must not be claimed.
- **−** Deleting a file from a filesystem doesn't guarantee it can't be recovered from the disk. Documented as a limitation.
