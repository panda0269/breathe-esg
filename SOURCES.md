# Sources

## SAP — Fuel and Procurement

### What I researched
SAP MM (Materials Management) module stores purchase orders
across two tables — EKKO (header) and EKPO (line items).
Exports are generated via ME2N, ME2L, or ME2M transactions
and downloaded as flat file CSV or Excel.

I researched the EKKO and EKPO table structures on
saplearners.com, saponlinetutorials.com, and the SAP
community forums. Key finding: SAP column headers appear
in German when the system language is set to German —
fields like MANDT (client), EBELN (PO number), WERKS (plant),
MENGE (quantity), MEINS (unit of measure), BEDAT (document date).

### What I learned
- Dates export as YYYYMMDD — not human-friendly
- Units are SAP-specific codes: L, LT, KL, GAL, KG, ST
- Plant codes (WERKS) are numeric codes meaningless
  without a lookup table the client must provide
- A single PO can have multiple line items with
  different materials, quantities and units

### Why my sample data looks the way it does
- Mixed German column names (MANDT, EBELN, WERKS)
  reflecting real SAP exports
- Date format YYYYMMDD
- One row with quantity 0 to test suspicious flagging
- One row with GAL units to test unit conversion
- Multiple plant codes to show the lookup problem
- Mix of diesel, petrol, LPG to reflect real fuel procurement

### What would break in real deployment
- Plant codes need a client-provided lookup table
  to map to human-readable facility names
- Material codes (MATNR) need a material master
  to know if a purchase is fuel vs non-fuel
- Some clients export with German headers,
  some with English — would need to auto-detect
- Large exports (100k+ rows) would need chunked
  processing, not loading the whole file into memory

---

## Utility — Electricity

### What I researched
The Green Button initiative is an industry standard
for utility data exports, adopted by major utilities
in the US and increasingly in India. Facilities managers
download CSV or XML exports from their utility portal.

I researched the Green Button standard on
greenbuttonalliance.org, docs.oracle.com, and
energy.gov. Key finding: CSV exports vary between
utilities but consistently include account number,
meter ID, billing period start/end, usage in kWh,
demand in kW, rate schedule, and amount.

### What I learned
- Billing periods are NOT calendar months —
  a bill might run Jan 15 to Feb 14
- Large facilities have multiple meters
- Units can be kWh or MWh depending on meter size
- Rate schedule codes are utility-specific gibberish
- Some utilities export at 15-minute or hourly intervals,
  not just monthly billing totals

### Why my sample data looks the way it does
- Two different meter IDs for one address
  to reflect multi-meter facilities
- Billing periods starting mid-month
- One row with zero usage to test suspicious flagging
- Mix of kWh values reflecting realistic
  industrial electricity consumption

### What would break in real deployment
- Billing period proration needed for monthly reporting
- MWh vs kWh detection needs to be more robust
- Indian utility portals don't all follow Green Button —
  would need per-utility parsers
- PDF bills are still common and would need
  a separate parsing approach

---

## Travel — Corporate Travel (Concur)

### What I researched
SAP Concur is the dominant corporate travel and
expense platform. Finance teams export expense reports
via the Expense Processor view as CSV or Excel.

I researched Concur's expense report structure on
the SAP Concur community forums, the Concur developer
documentation, and university Concur implementation guides.
Key finding: each row is one expense line item with
fields including report ID, employee ID, expense type,
travel date, origin, destination, amount, currency,
merchant, and trip purpose.

### What I learned
- Expense types include: Airfare, Hotel, Taxi/Car Svc,
  Rail, Rental Car, Meals, Parking
- Flights give airport codes, not distances
- Class of service (Economy/Business/First) affects
  emission factors significantly
- Hotels give no location detail beyond merchant name
- Ground transport has no distance data at all

### Why my sample data looks the way it does
- Mix of flight, hotel, and ground transport rows
- Real Indian airport codes (BOM, DEL, BLR)
- One unknown airport code (XYZ) to test flagging
- International routes (BOM→LHR) to test
  long-haul distance lookup
- Multiple employees on different trips

### What would break in real deployment
- Airport distance lookup table covers ~20 routes —
  a real deployment needs a full IATA distance API
- Class of service missing from many exports —
  emission factor calculation would be imprecise
- Multi-currency expenses need exchange rate
  normalization for consistent cost reporting
- Concur customization means column names
  vary between company implementations