# HostFlow v2 — Complete STR Operating System

**2,971 lines** · Daily ops + tax compliance + material participation + proforma + iCal import + audit PDF

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Click **🎲 Load Demo Data** in the sidebar to populate test data.

## Files

| File | Lines | Purpose |
|------|-------|---------|
| `str_logic.py` | 1,624 | Core engine: data models, briefing generator, material participation, proforma, Schedule E, compliance checklists, audit PDF, iCal parser, Google Sheets persistence |
| `app.py` | 1,347 | Streamlit UI: 11 views, sidebar with live MP tracker, Sheets sync |
| `requirements.txt` | 6 | streamlit, gspread, google-auth, pandas, anthropic, fpdf2 |

## 11 Views

| View | What It Does |
|------|-------------|
| **📋 Briefing** | "What do I need to do today?" — check-ins, checkouts, turnovers, messages, pricing intelligence |
| **⏱️ Time Tracker** | Live timer + manual entry, material participation dashboard (100hr/500hr), pace projections |
| **🏠 Properties** | Full roster with financials (purchase price, mortgage, taxes, insurance, permits, LLC, EIN) |
| **📅 Bookings** | Reservation lifecycle, turnover tracking, status management |
| **📥 iCal Import** | Import from Airbnb/VRBO/Booking.com calendar URLs or pasted .ics data. Auto-deduplication. |
| **💰 Finances** | Revenue analytics, expense tracking (29 categories), proforma/cash-on-cash, Schedule E prep |
| **💬 Messages** | 7 auto-filled guest communication templates |
| **📇 Team** | Contact directory — cleaners, handymen, CPA, vendors |
| **✅ Compliance** | Federal (15 items) + state-specific checklists (8 states + default). Interactive checkboxes. |
| **📎 Documents** | Receipt/photo/permit vault. 15 document types. Audit PDF export. |
| **🤖 AI** | Portfolio analysis, tax tips, audit readiness, message drafting |

## iCal Import (NEW)

Parses standard iCal (.ics) calendar feeds from:

- **Airbnb** — Extracts guest names, phone numbers, guest count from SUMMARY and DESCRIPTION fields
- **VRBO** — Handles "Reserved - Name" and "Booked - Name" formats
- **Booking.com** — Parses "Booking.com - Guest" format
- **Blocked dates** — Detected and separated ("Not available", "Owner block", etc.)

**Features:**
- Import via URL fetch or paste .ics text
- Auto-deduplication against existing bookings (matches on property + check-in + check-out)
- Auto-sets booking status based on dates (confirmed/checked_in/checked_out)
- Calculates payout with platform fees
- Re-import safe — duplicates skipped automatically

**How to get your iCal URL:**
- Airbnb: Listing → Calendar → Availability Settings → Export Calendar
- VRBO: Listing → Calendar → Import/Export → Export URL

## Google Sheets Persistence (NEW)

7 auto-created tabs: `properties`, `bookings`, `expenses`, `time_entries`, `contacts`, `documents`, `maintenance`

**Auto-load:** Data loads from Sheets on app startup when connected.
**Manual sync:** ⬇️ Load / ⬆️ Save buttons in sidebar.
**Full JSON backup:** Properties and bookings store complete JSON in a Full_JSON column for lossless round-tripping.

### Setup

```toml
# .streamlit/secrets.toml
gcp_service_account_json = '{"type":"service_account",...}'
sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_ID/edit"
anthropic_api_key = "sk-ant-api03-..."  # optional, for AI assistant
```

## Material Participation Tracking

| Test | Hours | Purpose |
|------|-------|---------|
| **Test 3** (Primary) | 100+ hrs | Must be largest single participant. Most common for hybrid-managed STR. |
| **Test 1** (Safe Harbor) | 500+ hrs | Automatic qualification. Harder but bulletproof. |

Dashboard shows: current hours, pace/week, hours needed/week to hit target, projected year-end total, monthly distribution, category breakdown.

**21 IRS-qualifying activity categories** including: Guest Communication, Booking Management, Revenue Management, Turnover Coordination, Property Inspection, Maintenance, Cleaning, Financial/Bookkeeping, Tax Compliance, Listing Management, Team Management, and more.

## Audit PDF (9 Sections)

One-click PDF generation with:
1. Cover page
2. Property portfolio (addresses, purchase prices, mortgages, permits, LLCs)
3. Revenue summary (per-property and portfolio)
4. Expense detail (by category with date, description, amount, vendor)
5. Schedule E preparation (line-by-line per property)
6. Material participation time log (every entry in table format)
7. Material participation analysis (Test 3 & Test 1 status)
8. Document & receipt inventory
9. Maintenance log + Contact directory + Disclaimer

## Compliance Checklists

**Federal** (15 items): EIN, Schedule E, 1099-K, material participation log, safe harbor election, depreciation, LLC, insurance, fair housing, record retention, quarterly estimated tax, etc.

**State-specific** (8 states): CA, FL, TX, CO, TN, AZ, NY, HI — each with local requirements (TOT, permits, night caps, inspections).

**Default** (all other states): State tax, lodging tax, STR permit, business license, zoning, safety, HOA.

## Disclaimers

- Not tax advice. Consult a CPA.
- Not legal advice. Consult an attorney.
- Compliance checklists are guidance only. Regulations change.
- IRS requires contemporaneous records. Log time promptly.
- Retain all original documents 7+ years.
