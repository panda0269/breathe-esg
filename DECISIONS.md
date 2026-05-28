# Decisions

## SAP — Flat File CSV chosen over IDoc/OData/BAPI
IDoc is XML-based and requires SAP middleware to generate.
OData requires a live SAP system with API access.
BAPI requires ABAP function calls.
For a client onboarding scenario, the most realistic format
is a flat file CSV exported via ME2N transaction — this is
what a client's SAP admin would actually email you.
I chose this format and built a column mapper that handles
both German headers (MANDT, EBELN, WERKS) and English
equivalents, since SAP language settings vary by client.

What I would ask the PM:
- What SAP version is the client running?
- Are exports in German or English?
- Do they have a plant code lookup table they can share?
- Is this a one-time dump or recurring feed?

## Utility — Portal CSV chosen over PDF or API
PDF parsing is brittle — bill layouts change between
utilities and even between billing periods.
APIs require per-utility OAuth credentials and
vary completely between providers.
Portal CSV export is what a facilities manager
actually downloads and emails. I modeled this
after the Green Button Data standard used by
major US and Indian utilities.

Key challenge handled: billing periods don't align
with calendar months. I store the billing period
start date as the activity date and note in SOURCES.md
that proration logic would be needed for monthly reporting.

What I would ask the PM:
- Which utility providers does the client use?
- Do they have AMI (smart meter) data or just monthly bills?
- What is the reporting period — calendar month or billing cycle?

## Travel — Concur CSV export chosen over API
The Concur API requires OAuth and admin credentials.
For a prototype onboarding scenario, the CSV export
from Concur's expense processor view is realistic —
finance teams already pull this regularly.

Key challenge handled: flights often only provide
airport codes, not distances. I built a distance
lookup table for common Indian and international routes.
Unknown routes are flagged SUSPICIOUS for analyst review
rather than silently dropped or estimated incorrectly.

What I would ask the PM:
- Does the client use Concur, Navan, or another platform?
- Do they have class of service data for flights?
- How should unknown airport routes be handled?

## Subset decisions
- SAP: handling fuel and procurement only, not HR or finance data
- Utility: handling electricity only, not gas or water
- Travel: handling flights, hotels, ground transport.
  Meals and miscellaneous expenses excluded as they
  have negligible emission factors.

## Authentication
Basic session auth is in place via Django REST Framework.
JWT tokens were not implemented — noted in TRADEOFFS.md.