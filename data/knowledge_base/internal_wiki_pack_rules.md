# Internal Wiki: Pack Data Rules

Synthetic source. Rules are designed for this local demo only.

## Field rules

- `pack_id`, `pack_name`, `tariff_name`, `price_azn`, `validity_days`, `activation_code`, `effective_date`, `status`, and `last_updated` are required for downstream reporting.
- Activation codes must start with `*`, end with `#`, and contain only digits and `*` between those characters.
- Validity should normally be one of 1, 3, 7, 14, 30, or 90 days.
- Standard local pack prices should be between 1.00 AZN and 80.00 AZN unless the pack is a roaming add-on.
- Roaming add-ons may be between 5.00 AZN and 120.00 AZN.
- Active records should have an effective date and a last updated date within the last 120 days.

## Eligibility rules

- Night Internet Pack 5GB is prepaid-only.
- Business Pro Plus is business postpaid-only.
- YouthMax 10GB and Student Social 3GB should use Youth or Prepaid tariff naming.
- Data-only tariff names should not be used for voice packs with more than 0 included minutes.

## Review rules

- High price anomalies, retired status changes, and tariff eligibility conflicts require human review.
- Missing values with directly matching recent evidence can be proposed with low risk.
- If evidence is missing or stale, classify the proposal as needs_review.
