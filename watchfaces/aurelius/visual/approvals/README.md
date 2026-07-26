# Intentional visual-change approval records (ADR-009 §5)

One JSON record per proposed/approved visual version change. Approved
goldens may move ONLY when an *authoritative* record binds the exact new
golden hashes — enforced by `tools/validate.py` (stdlib hash checks) and
`tests/visual/` (pixel-level checks).

## Authoritative records (Phase-4 hardening)

A record authorizes golden bytes only when **both** gates are closed:

- `owner.status == "approved"` — the product owner accepted the pixels;
- `architecture_review.status == "approved"` — architecture accepted the
  lineage.

Every committed golden set under `goldens/<version>/` — the active one and
every superseded one — must have **exactly one** such record. Validation
rejects:

- owner-approved but architecture-pending/rejected records;
- architecture-approved but owner-pending/rejected records;
- two or more fully-approved records for one `visual_version`, which is
  reported as ambiguity rather than resolved by taking the last match.

Records that are `proposed` or `rejected` stay committed as historical
evidence (ADR-009 §5); they simply never authorize goldens. `APPROVAL-0002`
and `APPROVAL-0003` are exactly that.

Rationale: `docs/reports/PHASE_3_POST_MERGE_REVIEW.md` §"Non-blocking future
hardening".

Required fields:

| field | meaning |
|---|---|
| `approval_id` | `APPROVAL-<n>`, monotonically increasing |
| `face`, `visual_version` | target face + proposed version directory name |
| `previous_visual_version` | prior approved version (null for the first) |
| `previous_goldens` / `proposed_goldens` | sha256 of normal/aod golden PNGs |
| `inventory_sha256` | sha256 of `inventories/inventory.json` at record time |
| `changed_resources` | repo-relative paths whose bytes change in this delta |
| `handoff_asset_ids` | studio handoff entries backing the change |
| `metrics` | compare_visuals.py metrics vs previous goldens (null for first) |
| `previews` | committed preview/candidate image paths |
| `rationale` | why this visual change exists |
| `owner` | `{status: proposed\|approved\|rejected, by, date}` |
| `architecture_review` | `{status, ref}` |
| `device_evidence` | evidence directory (required for major generations) |

Lifecycle: a record enters as `proposed` alongside candidate renders; the
owner flips it to `approved` (or `rejected`) in a reviewed commit; only then
may `goldens/<version>/` change to the recorded hashes.
