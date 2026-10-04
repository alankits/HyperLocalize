# ADR 0010: Frontend: server-rendered Django templates + HTMX, with one small review-player script

**Status:** Proposed (2026-10-05). Not yet approved. **This changes the Phase 0 recommendation (React + TypeScript), because of the Q2 answer.**
**Source:** `docs/PHASE0_DISCOVERY.md` §6.3; Q2 answer

## Context

The team has **basic** JavaScript/React (Q2). The UI needs:
- forms for projects, glossary and consent;
- live job status;
- a **review workspace**: a video player synced to the segment list, inline segment editing, flags and check results, scene-level accept / request changes / regenerate;
- an audit and evidence viewer.

A live demo and a viva are required (Q8). A separate single-page app adds a second codebase, an API layer, CSRF and session handling across origins, and a build toolchain.

## Options Considered

| Criterion | React + TypeScript SPA | **Django templates + HTMX + one small vanilla-JS module** | React "islands" inside Django templates |
|---|---|---|---|
| Fit with basic JS skills | Weak (state management, API layer, auth across origins) | **Strong** | Medium |
| Codebases and build tools | 2; Node toolchain | **1; no build step** | 1 + bundler |
| Review workspace interactivity | Excellent | **Adequate**: HTMX partial updates; the player sync is about 100 lines of JS using the `<video>` `timeupdate` event | Good |
| Auth and CSRF | Must design for the SPA | **Django defaults** | Django defaults |
| Demo risk | Higher (more moving parts) | **Lower** | Medium |
| Product credibility | High | Good with a clean CSS framework | High |

## Decision

- Django templates for every page.
- **HTMX** for partial updates: job-status polling every 2 seconds, saving a segment edit, accept / request changes, showing check results. The HTMX file is vendored into static files, so the UI doesn't depend on a CDN during the demo.
- **One vanilla-JS module** (`review_player.js`) for the review workspace. It highlights the current segment as the video plays and seeks when a segment is clicked.
- A small classless or utility CSS framework (a minor choice, made during S1).
- **Every permission and consent decision is made on the server.** The UI only reflects them.
- Accessibility basics: keyboard-operable controls, labelled form fields, and a toggle for subtitles in the preview.

## Consequences

- **+** One codebase, no frontend build, less to learn; the team's Python strength carries the UI.
- **+** Every UI action goes through a Django view with the standard permission checks, so there's no second enforcement layer to keep in sync.
- **−** A richer editor (e.g. a waveform display) would be harder. It is out of MVP scope.
- **−** Evaluators may expect a "modern SPA". The answer is a deliberate trade-off for reliability and team fit, which can be defended.
- **Viva in 2 minutes:** "We chose server-rendered pages with HTMX because our team is strongest in Python and a live demo has to be reliable. The only custom JavaScript is the video-segment sync. Security decisions are all on the server."
