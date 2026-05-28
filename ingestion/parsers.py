import csv
import io
from datetime import datetime


# ─── SAP PARSER ───────────────────────────────────────────────
# SAP exports use German column headers, YYYYMMDD dates,
# inconsistent units. We handle a flat file CSV from ME2N report.
#These were the main thn=ings we did in while working on SAP part

SAP_UNIT_CONVERSIONS = {
    'L':   ('litres', 1.0),
    'LT':  ('litres', 1.0),
    'KG':  ('kg', 1.0),
    'KL':  ('litres', 1000.0),   # kilolitres to litres
    'GAL': ('litres', 3.785),    # US gallons to litres
    'M3':  ('litres', 1000.0),   # cubic metres to litres
    'ST':  ('units', 1.0),       # pieces/units
}

def parse_sap_date(date_str):
    # SAP exports dates as YYYYMMDD or DD.MM.YYYY or DD/MM/YYYY
    date_str = str(date_str).strip()
    for fmt in ('%Y%m%d', '%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def parse_sap_csv(file_content):
    results = []
    reader = csv.DictReader(io.StringIO(file_content))
    COLUMN_MAP = {
        'EBELN': 'po_number',
        'Purchasing Document': 'po_number',
        'EBELP': 'line_item',
        'Item': 'line_item',
        'WERKS': 'plant_code',
        'Plant': 'plant_code',
        'MATNR': 'material_code',
        'Material': 'material_code',
        'TXZ01': 'material_desc',
        'Short Text': 'material_desc',
        'MENGE': 'quantity',
        'Order Quantity': 'quantity',
        'MEINS': 'unit',
        'Order Unit': 'unit',
        'NETWR': 'net_value',
        'Net Order Value': 'net_value',
        'WAERS': 'currency',
        'Currency': 'currency',
        'BEDAT': 'doc_date',
        'Document Date': 'doc_date',
        'LIFNR': 'vendor_code',
        'Vendor': 'vendor_code',
    }

    for i, row in enumerate(reader):
        # Normalize column names
        normalized_row = {}
        for key, value in row.items():
            clean_key = key.strip()
            mapped_key = COLUMN_MAP.get(clean_key, clean_key)
            normalized_row[mapped_key] = value.strip() if value else ''      
        parsed_date = parse_sap_date(normalized_row.get('doc_date', ''))
        try:
            raw_qty = float(normalized_row.get('quantity', 0) or 0)
        except ValueError:
            raw_qty = 0
        raw_unit = normalized_row.get('unit', 'L').upper().strip()
        unit_info = SAP_UNIT_CONVERSIONS.get(raw_unit, ('units', 1.0))
        normalized_unit = unit_info[0]
        normalized_qty = raw_qty * unit_info[1]
        parse_status = 'OK'
        parse_error = None
        if raw_qty <= 0:
            parse_status = 'SUSPICIOUS'
            parse_error = 'Quantity is zero or negative'
        elif parsed_date is None:
            parse_status = 'FAILED'
            parse_error = f"Could not parse date: {normalized_row.get('doc_date')}"
        elif not normalized_row.get('plant_code'):
            parse_status = 'SUSPICIOUS'
            parse_error = 'Missing plant code'

        results.append({
            'raw_data': dict(row),
            'parse_status': parse_status,
            'parse_error': parse_error,
            'normalized': {
                'scope': 1,
                'category': 'FUEL',
                'activity_date': parsed_date,
                'quantity': normalized_qty,
                'unit': normalized_unit,
                'original_quantity': raw_qty,
                'original_unit': raw_unit,
                'location': normalized_row.get('plant_code', ''),
                'vendor': normalized_row.get('vendor_code', ''),
                'cost_amount': float(normalized_row.get('net_value') or 0),
                'cost_currency': normalized_row.get('currency', ''),
            }
        })

    return results


# ─── UTILITY PARSER ───────────────────────────────────────────
# Green Button style CSV from utility portals.
# Key challenge: billing periods don't align with calendar months.
# Key challenge: units can be kWh or MWh depending on meter size.
#These were the main thn=ings we did in while working on utility part

def parse_utility_csv(file_content):
    results = []
    reader = csv.DictReader(io.StringIO(file_content))

    COLUMN_MAP = {
        'Account Number': 'account_number',
        'account_number': 'account_number',
        'Meter ID': 'meter_id',
        'meter_id': 'meter_id',
        'Service Address': 'address',
        'address': 'address',
        'Billing Period Start': 'period_start',
        'period_start': 'period_start',
        'Billing Period End': 'period_end',
        'period_end': 'period_end',
        'Usage (kWh)': 'usage_kwh',
        'usage_kwh': 'usage_kwh',
        'Usage (MWh)': 'usage_mwh',
        'usage_mwh': 'usage_mwh',
        'Demand (kW)': 'demand_kw',
        'Rate Schedule': 'rate_schedule',
        'Amount': 'amount',
        'amount': 'amount',
        'Currency': 'currency',
    }

    for i, row in enumerate(reader):
        normalized_row = {}
        for key, value in row.items():
            clean_key = key.strip()
            mapped_key = COLUMN_MAP.get(clean_key, clean_key)
            normalized_row[mapped_key] = value.strip() if value else ''
        period_start = None
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y'):
            try:
                period_start = datetime.strptime(
                    normalized_row.get('period_start', ''), fmt
                ).date()
                break
            except ValueError:
                continue
        try:
            if normalized_row.get('usage_kwh'):
                raw_qty = float(normalized_row['usage_kwh'])
                raw_unit = 'kWh'
                normalized_qty = raw_qty
            elif normalized_row.get('usage_mwh'):
                raw_qty = float(normalized_row['usage_mwh'])
                raw_unit = 'MWh'
                normalized_qty = raw_qty * 1000  # convert to kWh
            else:
                raw_qty = 0
                raw_unit = 'kWh'
                normalized_qty = 0
        except ValueError:
            raw_qty = 0
            raw_unit = 'kWh'
            normalized_qty = 0
        parse_status = 'OK'
        parse_error = None
        if normalized_qty <= 0:
            parse_status = 'SUSPICIOUS'
            parse_error = 'Zero or missing electricity usage'
        elif period_start is None:
            parse_status = 'FAILED'
            parse_error = f"Could not parse billing period start date"

        results.append({
            'raw_data': dict(row),
            'parse_status': parse_status,
            'parse_error': parse_error,
            'normalized': {
                'scope': 2,
                'category': 'ELECTRICITY',
                'activity_date': period_start,
                'quantity': normalized_qty,
                'unit': 'kWh',
                'original_quantity': raw_qty,
                'original_unit': raw_unit,
                'location': normalized_row.get('address', ''),
                'vendor': normalized_row.get('account_number', ''),
                'cost_amount': float(normalized_row.get('amount') or 0),
                'cost_currency': normalized_row.get('currency', 'INR'),
            }
        })

    return results


# ─── TRAVEL PARSER ────────────────────────────────────────────
# Concur expense report CSV export.
# Key challenge: different expense types need different emission factors.
# Key challenge: flights only give airport codes, no distance.
# Rough distance lookup for common Indian + international routes (km)
#These were the main thn=ings we did in while working on travel part
AIRPORT_DISTANCES = {
    ('BOM', 'DEL'): 1148, ('DEL', 'BOM'): 1148,
    ('BOM', 'BLR'): 842,  ('BLR', 'BOM'): 842,
    ('DEL', 'BLR'): 1740, ('BLR', 'DEL'): 1740,
    ('BOM', 'HYD'): 620,  ('HYD', 'BOM'): 620,
    ('DEL', 'HYD'): 1253, ('HYD', 'DEL'): 1253,
    ('BOM', 'CCU'): 1660, ('CCU', 'BOM'): 1660,
    ('BOM', 'LHR'): 7186, ('LHR', 'BOM'): 7186,
    ('DEL', 'LHR'): 6700, ('LHR', 'DEL'): 6700,
    ('BOM', 'DXB'): 1936, ('DXB', 'BOM'): 1936,
    ('DEL', 'DXB'): 2194, ('DXB', 'DEL'): 2194,
    ('DEL', 'SIN'): 4149, ('SIN', 'DEL'): 4149,
    ('BOM', 'SIN'): 4356, ('SIN', 'BOM'): 4356,
    ('BLR', 'SIN'): 3440, ('SIN', 'BLR'): 3440,
    ('BOM', 'JFK'): 12556, ('JFK', 'BOM'): 12556,
    ('DEL', 'JFK'): 11753, ('JFK', 'DEL'): 11753,
    ('BOM', 'CDG'): 7017, ('CDG', 'BOM'): 7017,
    ('DEL', 'CDG'): 6601, ('CDG', 'DEL'): 6601,
}
EXPENSE_TYPE_MAP = {
    'airfare': 'FLIGHT',
    'air fare': 'FLIGHT',
    'flight': 'FLIGHT',
    'hotel': 'HOTEL',
    'lodging': 'HOTEL',
    'accommodation': 'HOTEL',
    'taxi': 'GROUND_TRANSPORT',
    'taxi/car svc': 'GROUND_TRANSPORT',
    'car service': 'GROUND_TRANSPORT',
    'ground transport': 'GROUND_TRANSPORT',
    'rental car': 'GROUND_TRANSPORT',
    'train': 'GROUND_TRANSPORT',
    'rail': 'GROUND_TRANSPORT',
}

def parse_travel_csv(file_content):
    results = []
    reader = csv.DictReader(io.StringIO(file_content))

    COLUMN_MAP = {
        'Report_ID': 'report_id',
        'Employee_ID': 'employee_id',
        'Employee_Name': 'employee_name',
        'Submit_Date': 'submit_date',
        'Expense_Type': 'expense_type',
        'Travel_Date': 'travel_date',
        'Origin': 'origin',
        'Destination': 'destination',
        'Class': 'travel_class',
        'Amount': 'amount',
        'Currency': 'currency',
        'Merchant': 'merchant',
        'Trip_Purpose': 'trip_purpose',
    }

    for i, row in enumerate(reader):
        normalized_row = {}
        for key, value in row.items():
            clean_key = key.strip()
            mapped_key = COLUMN_MAP.get(clean_key, clean_key)
            normalized_row[mapped_key] = value.strip() if value else ''

        # Parse travel date
        travel_date = None
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
            try:
                travel_date = datetime.strptime(
                    normalized_row.get('travel_date', ''), fmt
                ).date()
                break
            except ValueError:
                continue

        # Determine category from expense type
        expense_type_raw = normalized_row.get('expense_type', '').lower().strip()
        category = EXPENSE_TYPE_MAP.get(expense_type_raw, 'GROUND_TRANSPORT')
        parse_status = 'OK'
        parse_error = None

        if category == 'FLIGHT':
            origin = normalized_row.get('origin', '').upper().strip()
            destination = normalized_row.get('destination', '').upper().strip()
            distance = AIRPORT_DISTANCES.get((origin, destination))
            if distance:
                quantity = float(distance)
                unit = 'km'
                original_quantity = float(distance)
                original_unit = 'km'
            else:
                quantity = float(normalized_row.get('amount') or 0)
                unit = 'km_estimated'
                original_quantity = quantity
                original_unit = 'unknown'
                parse_status = 'SUSPICIOUS'
                parse_error = f"Unknown route {origin}→{destination}, distance not in lookup table"
        else:
            try:
                quantity = float(normalized_row.get('amount') or 0)
            except ValueError:
                quantity = 0
            unit = normalized_row.get('currency', 'INR')
            original_quantity = quantity
            original_unit = unit

        if travel_date is None:
            parse_status = 'FAILED'
            parse_error = 'Could not parse travel date'

        results.append({
            'raw_data': dict(row),
            'parse_status': parse_status,
            'parse_error': parse_error,
            'normalized': {
                'scope': 3,
                'category': category,
                'activity_date': travel_date,
                'quantity': quantity,
                'unit': unit,
                'original_quantity': original_quantity,
                'original_unit': original_unit,
                'location': normalized_row.get('destination', ''),
                'vendor': normalized_row.get('merchant', ''),
                'cost_amount': float(normalized_row.get('amount') or 0),
                'cost_currency': normalized_row.get('currency', 'INR'),
            }
        })

    return results