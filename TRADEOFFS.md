# Tradeoffs — Three Things Deliberately Not Built

## 1. JWT Authentication and Role-Based Access Control
The current implementation uses Django session authentication.
I did not build JWT tokens, refresh token rotation,
or role-based permissions (analyst vs admin vs auditor).

Why: Implementing proper auth would have consumed a full day
and the assignment is evaluating data model quality and
ingestion logic, not auth infrastructure.
In production this would be the first thing to add —
analysts should only see their client's data,
and auditors should have read-only locked access.

## 2. Emission Factor Calculation
The app normalizes activity data (litres of fuel,
kWh of electricity, km of flight distance) but does
not multiply by emission factors to produce CO2e figures.

Why: Emission factors are jurisdiction-specific, updated
annually by bodies like IPCC, DEFRA, and MoEFCC.
Hard-coding them would produce wrong numbers.
The right approach is a separate emission factor table
with versioning and source attribution — a week of work
on its own. The normalized activity data this app
produces is the correct input to that calculation layer.

## 3. Recurring Ingestion / Scheduled Pulls
The app handles one-time file uploads only.
It does not support scheduled API pulls from SAP OData,
Green Button Connect My Data, or Concur's live API.

Why: Scheduled ingestion requires job queues (Celery),
credential storage, per-client API configuration,
and error retry logic. For a 4-day prototype focused
on the onboarding problem, file upload covers the
realistic first-month scenario. Recurring ingestion
would be phase 2.