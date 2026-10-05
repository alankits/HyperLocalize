# ADR 0019: Kaggle Notebooks as a remote GPU batch runtime

**Status:** Pending spike results (2026-10-05). Not approved.
**Source:** Q4 (revised); ADRs 0003, 0005, 0006; `docs/THIRD_PARTY_TERMS.md`; `docs/SPIKE_PLAN.md` M6, M9

## Context

There is no local GPU and no budget. Kaggle Notebooks give free GPU time (about 30 hours/week, a "floating" quota; 12-hour session limit, per Kaggle's own posts). GPU and internet need a **phone-verified account**. The Kaggle CLI can create and delete private datasets (`kaggle datasets create/version/delete`), push and delete kernels (`kaggle kernels push/status/output/delete`, with `enable_gpu`, `enable_internet` and `machine_shape` in the kernel metadata), but has **no cancel command**. Adding infrastructure needs a concrete justification (CLAUDE.md §6): IndicF5 on CPU may be too slow.

## Options Considered

| Criterion | No GPU at all (CPU only) | **Automated batch via the Kaggle CLI** | Manual upload/run/download by a person | Expose a Kaggle notebook as a live API (tunnel) |
|---|---|---|---|---|
| Speed | Possibly too slow (spike M6) | GPU speed plus kernel start-up overhead | Same, plus human delay | Fast |
| Consent control | Full | Dispatch and import checkpoints; remote copies deleted | Error-prone | Hard; exposes our system |
| Terms and risk | — | Uses the official CLI | — | Likely against the platform's intended use [UNVERIFIED]; fragile |
| Explainability | High | High: "upload, run, download, check consent on import" | Medium | Low |

## Decision (provisional; adopted **only if needed**, changed after independent review)

Adopted only if **both** hold:
- (a) IndicF5 on CPU fails the live-use threshold (spike rule 6);
- (b) **overnight CPU rendering can't produce the demo project's cloned-voice previews within 8 hours** [PROPOSED].

Otherwise Plan C (overnight CPU) covers the need **without any Kaggle integration**, and this ADR is deferred. That saves the team the CLI integration, RemoteCopy tracking and the phone-verification risk.

- `synthesise_project_remote` job (ADR 0003), **batched per project** so the kernel start-up and model-load overhead is paid once:
  1. consent check at CP3/CP4;
  2. record `RemoteCopy` rows **first**, then create a **private** dataset with all pending segments' texts and the reference clip and transcript;
  3. push a **private** GPU kernel from a versioned notebook in `kaggle/`;
  4. poll status;
  5. download the output;
  6. **import through the locked CP5 consent check**;
  7. **delete the kernel and the dataset**.
- Model weights: the spike chooses between downloading IndicF5 inside the kernel (needs internet and an HF token held as a Kaggle secret; whether secrets work in CLI-pushed kernels is [UNVERIFIED]) and a private Kaggle dataset holding the weights.
- **GPU quota** is recorded in the usage ledger. `check_providers` reports the remaining weekly hours.
- **Revocation** while DISPATCHED: no import, `kernels delete` + `datasets delete`. Whether this stops remote compute is [UNVERIFIED] and tested in spike M9.

## Consequences

- **+** Free GPU for pre-rendering cloned-voice previews.
- **−** Kernel start-up overhead makes it unsuitable for interactive regeneration; measured in M6.
- **−** Depends on one person's phone-verified Kaggle account, and on Kaggle's free quota staying available. The free alternative is local CPU synthesis (ADR 0018).
- **−** Identity data is temporarily held by Kaggle (named in the consent form; deleted after use).
- **Viva in 2 minutes:** "With no GPU and no budget, we pre-render cloned voices as private batch jobs on Kaggle's free GPUs. Consent is checked before upload and again before we accept the output, and the remote copies are deleted afterwards."
