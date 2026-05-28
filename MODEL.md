# Data Model

## Overview
The data model is designed around four core concerns:
multi-tenancy, source-of-truth preservation, unit normalization,
and audit integrity.

## Tables

### Client
Represents an enterprise client company.
Every record in the system belongs to a client.
This enables multi-tenancy — multiple companies
can use the same platform with full data isolation.

Fields: id, name, slug, created_at

### IngestionBatch
Every file upload creates one batch record.
This tracks who uploaded what, when, from which source,
and whether processing succeeded.
This is our source-of-truth tracking — you can always
trace any normalized record back to the exact file it came from.

Fields: id, client, source_type, uploaded_by, uploaded_at,
file_name, status, row_count, error_count

### RawRecord
Stores the original row exactly as it came in — never modified.
This is critical. If our normalization logic has a bug,
we can re-run it against the raw data without losing anything.
Each row stores the full original data as JSON.

Fields: id, batch, row_number, raw_data, parse_status, parse_error

### NormalizedRecord
The cleaned, standardized version of each raw record.
Key design decisions:
- original_quantity and original_unit preserved alongside
  normalized values so conversions are always auditable
- scope field categorizes as Scope 1 (direct/fuel),
  Scope 2 (electricity), Scope 3 (travel)
- status tracks the analyst review workflow:
  PENDING → APPROVED or REJECTED or FLAGGED
- is_locked prevents any edits after approval,
  protecting audit integrity

Fields: id, raw_record, client, source_type, scope, category,
activity_date, quantity, unit, original_quantity, original_unit,
location, vendor, cost_amount, cost_currency, status,
reviewed_by, reviewed_at, notes, created_at, updated_at, is_locked

### AuditLog
Every action taken on every record is logged here.
Who did it, when, what the value was before and after.
This is mandatory for ESG audit submissions.

Fields: id, record, action, performed_by, performed_at,
old_value, new_value

## Scope Classification
- Scope 1: SAP fuel and procurement data — direct combustion
- Scope 2: Utility electricity data — purchased energy
- Scope 3: Corporate travel data — value chain emissions

## Unit Normalization
- SAP: all quantities normalized to litres or kg.
  GAL converted to litres (×3.785), KL to litres (×1000)
- Utility: all quantities normalized to kWh.
  MWh converted to kWh (×1000)
- Travel: flights normalized to km using airport code lookup.
  Unknown routes flagged as SUSPICIOUS for analyst review