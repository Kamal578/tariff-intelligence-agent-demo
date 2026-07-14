# Revenue Assurance Policy

Synthetic governance policy for the local demo.

## Proposal classification

- `verified`: recent evidence directly identifies the same pack and field value, and the correction is low operational risk.
- `needs_review`: evidence is partial, conflicting, old, or the field affects commercial status, tariff eligibility, or high-value pricing.
- `insufficient_evidence`: the agent cannot identify a specific source that supports the proposed value.

## Human approval

- The agent must never mutate the source Excel workbook.
- The agent may write an output workbook only after an analyst approves individual proposals.
- Rejected proposals remain in the audit trail but must not be applied to the output workbook.
- Every decision must include timestamp, pack_id, field name, old value, proposed value, decision, evidence, and reasoning.

## Risk guidance

- Low risk: missing activation code, missing validity, missing price with direct current evidence.
- Medium risk: stale dates, name normalization, tariff naming mismatch.
- High risk: status changes, duplicate pack names, roaming price anomalies, and any proposal with conflicting evidence.
