"""
HostFlow STR Logic — Complete Short-Term Rental Operating System
v2.0: Tax compliance, material participation, proforma, audit trail

Core modules:
1.  Data models (Property, Booking, Expense, Contact, TimeEntry, Document, etc.)
2.  Constants & templates
3.  Guest communication templates
4.  Daily briefing generator
5.  Revenue & occupancy analytics
6.  Calendar & gap analysis
7.  Pricing suggestions
8.  TIME TRACKING & MATERIAL PARTICIPATION (IRS compliance)
9.  PROFORMA / INVESTMENT ANALYSIS (cash-on-cash, cap rate, NOI)
10. COMPLIANCE CHECKLISTS (federal + state/local)
11. AUDIT PDF EXPORT (comprehensive documentation)
12. Contacts management
13. Document/receipt vault
14. Activity/communication log
15. Serialization & helpers
16. Demo data generator
"""

import json
import os
from dataclasses import dataclass, asdict, field
from typing import Optional
from datetime import datetime, date, timedelta
from collections import Counter

# ═══════════════════════════════════════════════════════════════════
# 1. DATA MODELS
# ═══════════════════════════════════════════════════════════════════

@dataclass
class Property:
    property_id: str
    name: str
    nickname: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    county: str = ""
    platform: str = "Airbnb"
    property_type: str = "Entire home"
    bedrooms: int = 1
    bathrooms: float = 1.0
    max_guests: int = 4
    base_nightly_rate: float = 150.0
    cleaning_fee: float = 75.0
    min_nights: int = 2
    cleaner_name: str = ""
    cleaner_phone: str = ""
    cleaner_rate: float = 0.0
    wifi_password: str = ""
    check_in_time: str = "3:00 PM"
    check_out_time: str = "11:00 AM"
    check_in_instructions: str = ""
    house_rules: str = ""
    parking_info: str = ""
    amenities: list = field(default_factory=list)
    notes: str = ""
    status: str = "active"
    purchase_price: float = 0.0
    current_value: float = 0.0
    mortgage_payment: float = 0.0
    mortgage_balance: float = 0.0
    interest_rate: float = 0.0
    property_tax_annual: float = 0.0
    insurance_annual: float = 0.0
    hoa_monthly: float = 0.0
    down_payment: float = 0.0
    closing_costs: float = 0.0
    furnishing_cost: float = 0.0
    startup_costs: float = 0.0
    str_permit_number: str = ""
    str_permit_expiry: str = ""
    business_license: str = ""
    tot_registration: str = ""
    ein: str = ""
    llc_name: str = ""
    created_date: str = ""

    def to_dict(self):
        return asdict(self)

    @property
    def total_investment(self):
        return self.down_payment + self.closing_costs + self.furnishing_cost + self.startup_costs

    @property
    def annual_fixed_costs(self):
        return (self.mortgage_payment * 12) + self.property_tax_annual + self.insurance_annual + (self.hoa_monthly * 12)


@dataclass
class Booking:
    booking_id: str
    property_id: str
    guest_name: str
    guest_phone: str = ""
    guest_email: str = ""
    num_guests: int = 2
    check_in: str = ""
    check_out: str = ""
    num_nights: int = 0
    nightly_rate: float = 0.0
    cleaning_fee: float = 0.0
    total_payout: float = 0.0
    platform: str = "Airbnb"
    platform_fee: float = 0.0
    status: str = "confirmed"
    special_requests: str = ""
    guest_notes: str = ""
    turnover_status: str = "pending"
    cleaner_confirmed: bool = False
    rating_given: int = 0
    review_text: str = ""
    created_date: str = ""

    def to_dict(self):
        return asdict(self)

@dataclass
class Expense:
    expense_id: str
    property_id: str
    category: str
    description: str
    amount: float
    date: str = ""
    vendor: str = ""
    receipt_doc_id: str = ""
    tax_deductible: bool = True
    recurring: bool = False
    notes: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class Contact:
    contact_id: str
    name: str
    role: str = ""
    company: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    property_ids: list = field(default_factory=list)
    rate: str = ""
    notes: str = ""
    created_date: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class TimeEntry:
    entry_id: str
    property_id: str
    date: str = ""
    start_time: str = ""
    end_time: str = ""
    hours: float = 0.0
    category: str = ""
    description: str = ""
    platform: str = ""
    communication_with: str = ""
    notes: str = ""
    verified: bool = False

    def to_dict(self):
        return asdict(self)


@dataclass
class Document:
    doc_id: str
    property_id: str
    doc_type: str = "receipt"
    title: str = ""
    description: str = ""
    filename: str = ""
    file_data: str = ""
    category: str = ""
    amount: float = 0.0
    date: str = ""
    vendor: str = ""
    tax_year: int = 0
    notes: str = ""

    def to_dict(self):
        d = asdict(self)
        d.pop("file_data", None)
        return d


@dataclass
class MaintenanceItem:
    item_id: str
    property_id: str
    title: str
    description: str = ""
    priority: str = "medium"
    status: str = "open"
    reported_date: str = ""
    resolved_date: str = ""
    cost: float = 0.0
    vendor: str = ""
    notes: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class ActivityLog:
    log_id: str
    property_id: str
    date: str = ""
    activity_type: str = ""
    subject: str = ""
    description: str = ""
    contact_name: str = ""
    platform: str = ""
    duration_minutes: int = 0
    time_entry_id: str = ""
    notes: str = ""

    def to_dict(self):
        return asdict(self)


# ═══════════════════════════════════════════════════════════════════
# 2. CONSTANTS
# ═══════════════════════════════════════════════════════════════════

PLATFORMS = ["Airbnb", "VRBO", "Booking.com", "Direct", "Multi"]
PROPERTY_TYPES = ["Entire home", "Private room", "Shared room", "Condo", "Cabin", "Townhouse", "Apartment"]

AMENITIES_OPTIONS = [
    "WiFi", "TV", "Kitchen", "Washer", "Dryer", "Free parking",
    "Pool", "Hot tub", "Air conditioning", "Heating", "Workspace",
    "Self check-in", "Keypad", "Smart lock", "Security cameras (exterior)",
    "Smoke alarm", "Carbon monoxide alarm", "Fire extinguisher",
    "First aid kit", "Pet friendly", "EV charger", "BBQ grill",
    "Patio/balcony", "Gym", "Beach access", "Lake access",
    "Mountain view", "City view", "Ocean view",
]

EXPENSE_CATEGORIES = [
    "Cleaning", "Maintenance/Repairs", "Supplies (Guest)", "Supplies (Cleaning)",
    "Utilities (Electric)", "Utilities (Gas)", "Utilities (Water/Sewer)", "Utilities (Internet/Cable)",
    "Utilities (Trash)", "Mortgage Interest", "Property Tax", "Insurance",
    "HOA/Condo Fees", "Platform Fees", "Software/Tools", "Furnishing/Decor",
    "Professional Services (Accounting)", "Professional Services (Legal)",
    "Professional Services (Photography)", "Advertising/Marketing",
    "Travel (Property Visits)", "Vehicle/Mileage", "Depreciation",
    "Lawn/Landscaping", "Pest Control", "Snow Removal",
    "Linen Service", "Permits/Licenses", "Other"
]

TIME_CATEGORIES = [
    "Guest Communication", "Booking Management", "Revenue Management",
    "Turnover Coordination", "Property Inspection", "Maintenance Coordination",
    "Maintenance (Self-Performed)", "Cleaning (Self-Performed)", "Restocking/Supplies",
    "Financial/Bookkeeping", "Tax Compliance", "Legal/Insurance",
    "Listing Management", "Marketing/Advertising", "Team Management",
    "Property Improvement", "Research/Education", "Travel to Property",
    "Local Compliance", "Technology/Software", "Other Management Activity",
]

CONTACT_ROLES = [
    "Cleaner", "Handyman/Maintenance", "Plumber", "Electrician", "HVAC",
    "Locksmith", "Landscaper", "Pest Control", "Property Manager", "Co-Host",
    "Accountant/CPA", "Tax Attorney", "Real Estate Attorney", "Insurance Agent",
    "Mortgage Broker", "Real Estate Agent", "Photographer", "Interior Designer",
    "General Contractor", "Pool Service", "Guest (VIP/Repeat)", "Neighbor",
    "HOA Contact", "City/Permit Office", "Other"
]

ACTIVITY_TYPES = [
    "Email", "Phone Call", "Text Message", "Platform Message (Airbnb/VRBO)",
    "In-Person Meeting", "Software/Platform Work", "On-Site Visit",
    "Research", "Document Preparation", "Other"
]

DOCUMENT_TYPES = [
    "Receipt", "Photo (Property)", "Photo (Maintenance)", "Photo (Before/After)",
    "Inspection Report", "Permit/License", "Insurance Policy", "Contract/Agreement",
    "Tax Document", "Appraisal", "Mortgage Statement", "Utility Bill",
    "Guest Agreement", "Inventory List", "Other"
]

PRIORITY_COLORS = {"low": "#10B981", "medium": "#F59E0B", "high": "#EF4444", "urgent": "#DC2626"}
STATUS_COLORS = {"confirmed": "#3B82F6", "checked_in": "#10B981", "checked_out": "#6B7280", "cancelled": "#EF4444"}
TURNOVER_COLORS = {"pending": "#F59E0B", "scheduled": "#3B82F6", "in_progress": "#8B5CF6", "complete": "#10B981"}


# ═══════════════════════════════════════════════════════════════════
# 3. GUEST COMMUNICATION TEMPLATES
# ═══════════════════════════════════════════════════════════════════

MESSAGE_TEMPLATES = {
    "booking_confirmation": {
        "label": "Booking Confirmation",
        "template": "Hi {guest_name}! Thanks for booking {property_name}. We're excited to host you!\n\nCheck-in: {check_in} at {check_in_time}\nCheck-out: {check_out} at {check_out_time}\nGuests: {num_guests}\n\nI'll send check-in instructions a day before your arrival. Feel free to reach out with any questions!",
    },
    "check_in_instructions": {
        "label": "Check-In Instructions",
        "template": "Hi {guest_name}! Your stay at {property_name} starts tomorrow. Here's everything you need:\n\nCHECK-IN: {check_in_instructions}\n\nWIFI: {wifi_password}\nPARKING: {parking_info}\n\nHOUSE RULES:\n{house_rules}\n\nDon't hesitate to message me. Enjoy!",
    },
    "check_in_day": {
        "label": "Check-In Day Welcome",
        "template": "Hi {guest_name}! Welcome to {property_name}! The space is all ready for you.\n\nCheck-in is at {check_in_time}. {check_in_instructions}\n\nWiFi: {wifi_password}\n\nLet me know once you're settled in!",
    },
    "mid_stay_check": {
        "label": "Mid-Stay Check-In",
        "template": "Hi {guest_name}! Just checking in - hope you're enjoying your stay at {property_name}!\n\nIs everything going well? Happy to help with restaurant recs or activity suggestions.",
    },
    "checkout_reminder": {
        "label": "Checkout Reminder",
        "template": "Hi {guest_name}! Friendly reminder that checkout is tomorrow at {check_out_time}.\n\nBefore you leave, please:\n- Start any dishes in the dishwasher\n- Take out any trash\n- Lock the door behind you\n\nNo need to strip beds. Thanks for staying with us!",
    },
    "review_request": {
        "label": "Review Request",
        "template": "Hi {guest_name}! Thanks again for staying at {property_name}. We hope you had a great time!\n\nIf you have a moment, we'd really appreciate a review. It helps other guests find us.\n\nWe'd love to host you again!",
    },
    "issue_response": {
        "label": "Issue/Problem Response",
        "template": "Hi {guest_name}, I'm sorry to hear about that! Thank you for letting me know right away.\n\nI'm working on getting this resolved as quickly as possible. I'll follow up shortly.",
    },
}

def fill_template(template_key, property_data=None, booking_data=None, extra_vars=None):
    if template_key not in MESSAGE_TEMPLATES:
        return ""
    template = MESSAGE_TEMPLATES[template_key]["template"]
    variables = {}
    if property_data:
        variables.update({
            "property_name": property_data.get("name", property_data.get("nickname", "")),
            "check_in_time": property_data.get("check_in_time", "3:00 PM"),
            "check_out_time": property_data.get("check_out_time", "11:00 AM"),
            "wifi_password": property_data.get("wifi_password", "[WiFi]"),
            "parking_info": property_data.get("parking_info", "[Parking]"),
            "check_in_instructions": property_data.get("check_in_instructions", "[Check-in instructions]"),
            "house_rules": property_data.get("house_rules", "[House rules]"),
        })
    if booking_data:
        variables.update({
            "guest_name": booking_data.get("guest_name", "Guest"),
            "check_in": booking_data.get("check_in", ""),
            "check_out": booking_data.get("check_out", ""),
            "num_guests": str(booking_data.get("num_guests", "")),
        })
    if extra_vars:
        variables.update(extra_vars)
    result = template
    for k, v in variables.items():
        result = result.replace(f"{{{k}}}", str(v))
    return result


# ═══════════════════════════════════════════════════════════════════
# 4. DAILY BRIEFING GENERATOR
# ═══════════════════════════════════════════════════════════════════

def generate_daily_briefing(properties, bookings, maintenance_items, today=None):
    if today is None:
        today = date.today()
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)

    briefing = {"date": today.isoformat(), "actions": [], "check_ins_today": [], "check_outs_today": [], "check_ins_tomorrow": [], "active_stays": [], "turnovers_needed": [], "maintenance_urgent": [], "vacant_tonight": [], "occupancy_rate": 0.0, "revenue_this_month": 0.0, "summary": ""}
    property_map = {p.get("property_id", ""): p for p in properties}
    active_properties = [p for p in properties if p.get("status") == "active"]
    occupied_tonight = set()

    for booking in bookings:
        if booking.get("status") == "cancelled":
            continue
        b_in = _parse_date(booking.get("check_in", ""))
        b_out = _parse_date(booking.get("check_out", ""))
        pid = booking.get("property_id", "")
        prop = property_map.get(pid, {})
        pname = prop.get("nickname") or prop.get("name", "Unknown")
        guest = booking.get("guest_name", "Guest")

        if b_in == today:
            briefing["check_ins_today"].append({"booking": booking, "property": pname})
            briefing["actions"].append({"priority": "high", "type": "check_in", "text": f"🔑 {guest} checks into {pname} at {prop.get('check_in_time', '3 PM')}", "property_id": pid})
            briefing["actions"].append({"priority": "medium", "type": "message", "text": f"📱 Send check-in instructions to {guest} ({pname})", "property_id": pid, "template": "check_in_day"})
        if b_in == tomorrow:
            briefing["check_ins_tomorrow"].append({"booking": booking, "property": pname})
            briefing["actions"].append({"priority": "medium", "type": "message", "text": f"📱 Send day-before instructions to {guest} ({pname})", "property_id": pid, "template": "check_in_instructions"})
        if b_out == today:
            briefing["check_outs_today"].append({"booking": booking, "property": pname})
            briefing["actions"].append({"priority": "high", "type": "checkout", "text": f"👋 {guest} checks out of {pname} at {prop.get('check_out_time', '11 AM')}", "property_id": pid})
            if not booking.get("cleaner_confirmed"):
                briefing["turnovers_needed"].append({"booking": booking, "property": pname})
                briefing["actions"].append({"priority": "high", "type": "turnover", "text": f"🧹 Confirm turnover for {pname}", "property_id": pid})
        if b_out == yesterday:
            briefing["actions"].append({"priority": "low", "type": "message", "text": f"⭐ Review request to {guest} ({pname})", "property_id": pid, "template": "review_request"})

        if b_in and b_out and b_in <= today < b_out:
            briefing["active_stays"].append({"booking": booking, "property": pname, "nights_remaining": (b_out - today).days})
            occupied_tonight.add(pid)
            if booking.get("num_nights", 0) >= 4:
                mid = b_in + timedelta(days=booking["num_nights"] // 2)
                if mid == today:
                    briefing["actions"].append({"priority": "low", "type": "message", "text": f"💬 Mid-stay check with {guest} ({pname})", "property_id": pid, "template": "mid_stay_check"})

        if b_in and b_in.month == today.month and b_in.year == today.year:
            briefing["revenue_this_month"] += booking.get("total_payout", 0)

    for prop in active_properties:
        if prop.get("property_id", "") not in occupied_tonight:
            briefing["vacant_tonight"].append(prop)
    if active_properties:
        briefing["occupancy_rate"] = len(occupied_tonight) / len(active_properties) * 100

    for item in maintenance_items:
        if item.get("status") in ("open", "in_progress") and item.get("priority") in ("high", "urgent"):
            prop = property_map.get(item.get("property_id", ""), {})
            briefing["maintenance_urgent"].append(item)
            briefing["actions"].append({"priority": "high" if item["priority"] == "urgent" else "medium", "type": "maintenance", "text": f"🔧 {item.get('title', '')} at {prop.get('nickname', prop.get('name', ''))}", "property_id": item.get("property_id", "")})

    briefing["actions"].sort(key=lambda a: {"high": 0, "medium": 1, "low": 2}.get(a.get("priority", "low"), 3))

    parts = []
    if briefing["check_ins_today"]: parts.append(f"{len(briefing['check_ins_today'])} check-in{'s' if len(briefing['check_ins_today']) > 1 else ''}")
    if briefing["check_outs_today"]: parts.append(f"{len(briefing['check_outs_today'])} checkout{'s' if len(briefing['check_outs_today']) > 1 else ''}")
    if briefing["turnovers_needed"]: parts.append(f"{len(briefing['turnovers_needed'])} turnover{'s' if len(briefing['turnovers_needed']) > 1 else ''}")
    briefing["summary"] = f"Today: {', '.join(parts)}. {len(briefing['actions'])} action items." if parts else (f"Quiet day. {len(briefing['active_stays'])} active stays." if briefing["active_stays"] else "All clear today.")
    return briefing


# ═══════════════════════════════════════════════════════════════════
# 5. REVENUE & OCCUPANCY ANALYTICS
# ═══════════════════════════════════════════════════════════════════

def calculate_property_metrics(bookings, property_id, start_date=None, end_date=None):
    if start_date is None: start_date = date.today().replace(day=1)
    if end_date is None: end_date = date.today()
    total_days = max((end_date - start_date).days, 1)
    prop_bookings = [b for b in bookings if b.get("property_id") == property_id and b.get("status") != "cancelled"]
    total_revenue = total_nights = 0
    ratings = []
    for b in prop_bookings:
        b_in, b_out = _parse_date(b.get("check_in", "")), _parse_date(b.get("check_out", ""))
        if not b_in or not b_out: continue
        nights = max((min(b_out, end_date) - max(b_in, start_date)).days, 0)
        if nights > 0:
            total_nights += nights
            prorate = nights / max((b_out - b_in).days, 1)
            total_revenue += b.get("total_payout", 0) * prorate
        if b.get("rating_given", 0) > 0: ratings.append(b["rating_given"])
    return {
        "total_revenue": round(total_revenue, 2), "total_nights_booked": total_nights, "total_days": total_days,
        "occupancy_rate": round(total_nights / total_days * 100 if total_days else 0, 1),
        "avg_nightly_rate": round(total_revenue / total_nights if total_nights else 0, 2),
        "total_bookings": len(prop_bookings), "avg_rating": round(sum(ratings)/len(ratings), 1) if ratings else 0,
    }

def calculate_portfolio_metrics(bookings, properties, start_date=None, end_date=None):
    combined = {"total_revenue": 0, "total_nights_booked": 0, "avg_occupancy": 0, "avg_nightly_rate": 0, "total_bookings": 0, "per_property": {}}
    occs, rates = [], []
    for prop in properties:
        pid = prop.get("property_id", "")
        m = calculate_property_metrics(bookings, pid, start_date, end_date)
        combined["per_property"][pid] = m
        combined["total_revenue"] += m["total_revenue"]
        combined["total_nights_booked"] += m["total_nights_booked"]
        combined["total_bookings"] += m["total_bookings"]
        if m["occupancy_rate"] > 0: occs.append(m["occupancy_rate"])
        if m["avg_nightly_rate"] > 0: rates.append(m["avg_nightly_rate"])
    combined["avg_occupancy"] = round(sum(occs)/len(occs), 1) if occs else 0
    combined["avg_nightly_rate"] = round(sum(rates)/len(rates), 2) if rates else 0
    return combined


# ═══════════════════════════════════════════════════════════════════
# 6 & 7. GAP ANALYSIS & PRICING
# ═══════════════════════════════════════════════════════════════════

def get_gap_nights(bookings, property_id, lookahead_days=30):
    today_date = date.today()
    end_date = today_date + timedelta(days=lookahead_days)
    prop_bookings = sorted([b for b in bookings if b.get("property_id") == property_id and b.get("status") != "cancelled" and _parse_date(b.get("check_out","")) and _parse_date(b["check_out"]) > today_date], key=lambda b: b.get("check_in",""))
    gaps, current = [], today_date
    for b in prop_bookings:
        b_in, b_out = _parse_date(b.get("check_in","")), _parse_date(b.get("check_out",""))
        if not b_in or not b_out: continue
        if b_in > current and (b_in - current).days >= 1:
            gaps.append({"start": current.isoformat(), "end": b_in.isoformat(), "nights": (b_in - current).days})
        current = max(current, b_out)
    if current < end_date:
        gaps.append({"start": current.isoformat(), "end": end_date.isoformat(), "nights": (end_date - current).days})
    return gaps

def get_pricing_suggestions(bookings, property_data, lookahead_days=14):
    suggestions = []
    pid = property_data.get("property_id", "")
    base = property_data.get("base_nightly_rate", 150)
    today_date = date.today()
    for gap in get_gap_nights(bookings, pid, lookahead_days):
        gs = _parse_date(gap["start"])
        days_until = (gs - today_date).days if gs else 0
        if gap["nights"] <= 2 and days_until <= 7:
            suggestions.append({"type": "discount", "message": f"💰 {gap['nights']}-night gap starting {gap['start']}. Consider ${round(base*0.85)}/night (15% off).", "reason": "Short gap close to date"})
        elif gap["nights"] >= 7 and days_until <= 3:
            suggestions.append({"type": "urgent", "message": f"🚨 {gap['nights']}-night gap in {days_until} days. Drop to ${round(base*0.75)}/night.", "reason": "Long vacancy imminent"})
    return suggestions


# ═══════════════════════════════════════════════════════════════════
# 8. TIME TRACKING & MATERIAL PARTICIPATION (IRS)
# ═══════════════════════════════════════════════════════════════════

def calculate_material_participation(time_entries, tax_year=None):
    if tax_year is None: tax_year = date.today().year
    year_entries = [e for e in time_entries if _parse_date(e.get("date","")) and _parse_date(e["date"]).year == tax_year]
    total_hours = sum(e.get("hours", 0) for e in year_entries)
    hours_by_property = Counter()
    hours_by_category = Counter()
    hours_by_month = Counter()

    for e in year_entries:
        hours_by_property[e.get("property_id", "")] += e.get("hours", 0)
        hours_by_category[e.get("category", "Other")] += e.get("hours", 0)
        d = _parse_date(e.get("date", ""))
        if d: hours_by_month[d.month] += e.get("hours", 0)

    today_date = date.today()
    year_end = date(tax_year, 12, 31)
    days_remaining = max((year_end - today_date).days, 0) if today_date.year == tax_year else 0
    weeks_remaining = days_remaining / 7
    days_elapsed = (today_date - date(tax_year, 1, 1)).days + 1 if today_date.year == tax_year else 365
    pace = total_hours / max(days_elapsed / 7, 1)
    projected = total_hours + (pace * weeks_remaining) if weeks_remaining > 0 else total_hours

    return {
        "tax_year": tax_year, "total_hours": round(total_hours, 2), "total_entries": len(year_entries),
        "hours_by_property": dict(hours_by_property), "hours_by_category": dict(hours_by_category), "hours_by_month": dict(hours_by_month),
        "test_3_met": total_hours >= 100, "test_3_hours_needed": round(max(100 - total_hours, 0), 2), "test_3_pct": min(round(total_hours/100*100, 1), 100),
        "test_1_met": total_hours >= 500, "test_1_hours_needed": round(max(500 - total_hours, 0), 2), "test_1_pct": min(round(total_hours/500*100, 1), 100),
        "pace_per_week": round(pace, 2), "projected_year_end": round(projected, 1),
        "days_remaining": days_remaining, "weeks_remaining": round(weeks_remaining, 1),
        "hours_per_week_for_100": round(max(100 - total_hours, 0) / max(weeks_remaining, 1), 2),
        "hours_per_week_for_500": round(max(500 - total_hours, 0) / max(weeks_remaining, 1), 2),
    }

def get_time_entry_summary_for_audit(time_entries, tax_year=None):
    if tax_year is None: tax_year = date.today().year
    year_entries = sorted([e for e in time_entries if _parse_date(e.get("date","")) and _parse_date(e["date"]).year == tax_year], key=lambda e: e.get("date",""))
    return {"entries": year_entries, "total_hours": round(sum(e.get("hours",0) for e in year_entries), 2), "total_entries": len(year_entries)}


# ═══════════════════════════════════════════════════════════════════
# 9. PROFORMA / INVESTMENT ANALYSIS
# ═══════════════════════════════════════════════════════════════════

def calculate_proforma(property_data, annual_revenue, annual_expenses_dict, vacancy_rate=0.25):
    pp = property_data.get("purchase_price", 0) or 0
    total_inv = property_data.get("down_payment", 0) + property_data.get("closing_costs", 0) + property_data.get("furnishing_cost", 0) + property_data.get("startup_costs", 0)
    mortgage_yr = property_data.get("mortgage_payment", 0) * 12
    prop_tax = property_data.get("property_tax_annual", 0)
    ins = property_data.get("insurance_annual", 0)
    hoa = property_data.get("hoa_monthly", 0) * 12

    gross = annual_revenue
    vacancy = gross * vacancy_rate
    egi = gross - vacancy
    opex = sum(annual_expenses_dict.values()) + prop_tax + ins + hoa
    noi = egi - opex
    cash_flow = noi - mortgage_yr

    return {
        "gross_revenue": round(gross, 2), "vacancy_loss": round(vacancy, 2), "vacancy_rate": vacancy_rate,
        "effective_gross": round(egi, 2), "total_opex": round(opex, 2), "noi": round(noi, 2),
        "annual_debt_service": round(mortgage_yr, 2), "annual_cash_flow": round(cash_flow, 2),
        "monthly_cash_flow": round(cash_flow / 12, 2), "total_investment": round(total_inv, 2),
        "cap_rate": round(noi / pp * 100, 2) if pp else 0,
        "cash_on_cash": round(cash_flow / total_inv * 100, 2) if total_inv else 0,
        "dscr": round(noi / mortgage_yr, 2) if mortgage_yr else 0,
        "gross_yield": round(gross / pp * 100, 2) if pp else 0,
        "expense_ratio": round(opex / egi * 100, 1) if egi else 0,
        "break_even_occ": round((opex + mortgage_yr) / gross * 100, 1) if gross else 0,
    }

def generate_schedule_e_summary(property_data, bookings, expenses, tax_year=None):
    if tax_year is None: tax_year = date.today().year
    pid = property_data.get("property_id", "")
    year_bookings = [b for b in bookings if b.get("property_id") == pid and b.get("status") != "cancelled"]
    total_nights = 0
    for b in year_bookings:
        b_in, b_out = _parse_date(b.get("check_in","")), _parse_date(b.get("check_out",""))
        if b_in and b_out and (b_in.year == tax_year or b_out.year == tax_year):
            s, e = max(b_in, date(tax_year,1,1)), min(b_out, date(tax_year,12,31)+timedelta(days=1))
            total_nights += max((e - s).days, 0)
    gross = sum(b.get("total_payout",0) for b in year_bookings if _parse_date(b.get("check_in","")) and _parse_date(b["check_in"]).year == tax_year)

    sched = {"property_address": property_data.get("address",""), "fair_rental_days": total_nights, "line_3_rents": round(gross, 2),
             "line_5_advertising": 0, "line_6_auto": 0, "line_7_cleaning": 0, "line_8_commissions": 0,
             "line_9_insurance": round(property_data.get("insurance_annual",0), 2), "line_10_legal": 0,
             "line_12_mortgage_int": 0, "line_14_repairs": 0, "line_15_supplies": 0,
             "line_16_taxes": round(property_data.get("property_tax_annual",0), 2), "line_17_utilities": 0,
             "line_18_depreciation": 0, "line_19_other": 0}

    cat_map = {"Advertising/Marketing": "line_5_advertising", "Travel (Property Visits)": "line_6_auto", "Vehicle/Mileage": "line_6_auto",
               "Cleaning": "line_7_cleaning", "Maintenance/Repairs": "line_14_repairs", "Platform Fees": "line_8_commissions",
               "Professional Services (Accounting)": "line_10_legal", "Professional Services (Legal)": "line_10_legal",
               "Mortgage Interest": "line_12_mortgage_int", "Supplies (Guest)": "line_15_supplies", "Supplies (Cleaning)": "line_15_supplies",
               "Utilities (Electric)": "line_17_utilities", "Utilities (Gas)": "line_17_utilities",
               "Utilities (Water/Sewer)": "line_17_utilities", "Utilities (Internet/Cable)": "line_17_utilities",
               "Utilities (Trash)": "line_17_utilities", "Depreciation": "line_18_depreciation"}

    for exp in expenses:
        if exp.get("property_id") == pid and _parse_date(exp.get("date","")) and _parse_date(exp["date"]).year == tax_year:
            line = cat_map.get(exp.get("category",""), "line_19_other")
            sched[line] += exp.get("amount", 0)

    total_exp = sum(v for k,v in sched.items() if k.startswith("line_") and k != "line_3_rents" and isinstance(v, (int,float)))
    sched["total_expenses"] = round(total_exp, 2)
    sched["net_income"] = round(sched["line_3_rents"] - total_exp, 2)
    return sched


# ═══════════════════════════════════════════════════════════════════
# 10. COMPLIANCE CHECKLISTS
# ═══════════════════════════════════════════════════════════════════

FEDERAL_REQUIREMENTS = [
    {"item": "EIN (Employer Identification Number)", "description": "Obtain from IRS if operating as LLC or have employees.", "category": "Tax", "required": True},
    {"item": "Schedule E Filing", "description": "Report rental income/expenses on IRS Form 1040, Schedule E.", "category": "Tax", "required": True},
    {"item": "1099-K Reconciliation", "description": "Airbnb/VRBO issue 1099-K if gross payments exceed $600. Reconcile with records.", "category": "Tax", "required": True},
    {"item": "Material Participation Log", "description": "Maintain contemporaneous log of hours for IRS material participation tests.", "category": "Tax", "required": True},
    {"item": "Safe Harbor Election (Rev. Proc. 2019-38)", "description": "Rental real estate safe harbor: 250+ hours/year with separate books.", "category": "Tax", "required": False},
    {"item": "Depreciation Records", "description": "Track basis, improvements, depreciation schedule (27.5 yr residential).", "category": "Tax", "required": True},
    {"item": "Cost Segregation Study", "description": "Accelerate depreciation on components (5, 7, 15-yr property). Consult CPA.", "category": "Tax", "required": False},
    {"item": "LLC Formation", "description": "Consider LLC for liability protection.", "category": "Legal", "required": False},
    {"item": "Umbrella Insurance ($1M+)", "description": "Umbrella policy beyond standard landlord policy.", "category": "Insurance", "required": False},
    {"item": "STR-Specific Insurance", "description": "Proper STR policy (Proper, CBIZ) - standard homeowner may not cover.", "category": "Insurance", "required": True},
    {"item": "Fair Housing Compliance", "description": "Cannot discriminate based on protected classes.", "category": "Legal", "required": True},
    {"item": "Record Retention (7 Years)", "description": "Keep all financial records, receipts, tax documents 7+ years.", "category": "Tax", "required": True},
    {"item": "Quarterly Estimated Tax", "description": "Make quarterly estimated payments (Form 1040-ES) if liability expected.", "category": "Tax", "required": True},
    {"item": "Sales/Lodging Tax", "description": "Some platforms collect automatically. Verify for direct bookings.", "category": "Tax", "required": True},
    {"item": "Separate Bank Account", "description": "Required for safe harbor. Maintain separate account for rental activity.", "category": "Financial", "required": True},
]

STATE_REQUIREMENTS = {
    "CA": {"state_name": "California", "items": [
        {"item": "Transient Occupancy Tax (TOT) Registration", "description": "Register with city/county. Rates 8-15%. Airbnb collects in some cities.", "required": True},
        {"item": "City STR Permit/License", "description": "Many CA cities require permits (SF, LA, SD, Palm Springs). Check local.", "required": True},
        {"item": "Primary Residence Requirement", "description": "Many CA cities restrict STR to primary residence (SF, LA, Santa Monica).", "required": False},
        {"item": "Night Cap Limits", "description": "Some cities cap nights (SF: 90 unhosted, LA: 120 days).", "required": False},
        {"item": "CA State Tax Return", "description": "Report on Form 540, Schedule CA.", "required": True},
        {"item": "Business License", "description": "Most CA cities require general business license.", "required": True},
        {"item": "Hosting Platform Registration", "description": "Some cities require permit number on listing.", "required": True},
    ]},
    "FL": {"state_name": "Florida", "items": [
        {"item": "DBPR Vacation Rental License", "description": "Register with FL DBPR. Required for all STRs.", "required": True},
        {"item": "Sales Tax Registration", "description": "FL sales tax (6%) plus county surtax.", "required": True},
        {"item": "Tourist Development Tax", "description": "County-level (2-6%). Register with county.", "required": True},
        {"item": "Annual Safety Inspection", "description": "DBPR requires periodic inspections.", "required": True},
        {"item": "Local Business Tax Receipt", "description": "Required in many FL counties.", "required": True},
    ]},
    "TX": {"state_name": "Texas", "items": [
        {"item": "Hotel Occupancy Tax", "description": "TX Comptroller. State 6% plus local.", "required": True},
        {"item": "City STR Permit", "description": "Austin, Dallas, SA, Houston have registration requirements.", "required": True},
        {"item": "No State Income Tax", "description": "Federal filing only.", "required": False},
    ]},
    "CO": {"state_name": "Colorado", "items": [
        {"item": "Sales Tax License", "description": "CO Dept of Revenue for state/local sales tax.", "required": True},
        {"item": "Lodging Tax", "description": "State + local vary by jurisdiction.", "required": True},
        {"item": "City/County STR License", "description": "Denver, Boulder, mountain towns require licensing.", "required": True},
    ]},
    "TN": {"state_name": "Tennessee", "items": [
        {"item": "State Sales Tax", "description": "TN Dept of Revenue. State 7% + local.", "required": True},
        {"item": "STR Permit", "description": "Nashville and other cities require permits.", "required": True},
    ]},
    "AZ": {"state_name": "Arizona", "items": [
        {"item": "Transaction Privilege Tax (TPT)", "description": "Register with AZ DOR.", "required": True},
        {"item": "Residential Rental Registration", "description": "Register with county assessor.", "required": True},
        {"item": "State Income Tax", "description": "Report on AZ return.", "required": True},
    ]},
    "NY": {"state_name": "New York", "items": [
        {"item": "NYC Local Law 18 Registration", "description": "NYC requires registration. Must be present during stay.", "required": True},
        {"item": "Sales Tax + Hotel Room Occupancy Tax", "description": "NYS + NYC hotel tax (5.875% + $1.50/night).", "required": True},
        {"item": "Multiple Dwelling Law (NYC)", "description": "Restricts STR in multi-unit buildings <30 days.", "required": True},
    ]},
    "HI": {"state_name": "Hawaii", "items": [
        {"item": "GET License", "description": "General Excise Tax 4-4.5%.", "required": True},
        {"item": "Transient Accommodations Tax (TAT)", "description": "State TAT 10.25% + county surcharge 3%.", "required": True},
        {"item": "County STR Permit", "description": "Varies by island/county.", "required": True},
    ]},
}

DEFAULT_STATE_ITEMS = [
    {"item": "State Tax Return", "description": "Report rental income on state return if applicable.", "required": True},
    {"item": "Lodging/Hotel Tax", "description": "Check state/local lodging tax requirements.", "required": True},
    {"item": "City/County STR Permit", "description": "Check local ordinances for permit requirements.", "required": True},
    {"item": "Business License", "description": "Check city/county business license requirements.", "required": True},
    {"item": "Zoning Compliance", "description": "Verify STR permitted in your zone.", "required": True},
    {"item": "Safety/Fire Compliance", "description": "Smoke/CO detectors, fire extinguisher. Some require inspection.", "required": True},
    {"item": "HOA/Condo Rules", "description": "Check CC&Rs for STR restrictions.", "required": True},
]

def get_compliance_checklist(state_code, city=""):
    federal = [{"item": r["item"], "description": r["description"], "category": r.get("category","Federal"), "required": r["required"], "level": "Federal"} for r in FEDERAL_REQUIREMENTS]
    sd = STATE_REQUIREMENTS.get(state_code.upper())
    if sd:
        state = [{"item": r["item"], "description": r["description"], "category": "State", "required": r["required"], "level": f"State ({sd['state_name']})"} for r in sd["items"]]
    else:
        state = [{"item": r["item"], "description": r["description"], "category": "State/Local", "required": r["required"], "level": f"State ({state_code.upper()})"} for r in DEFAULT_STATE_ITEMS]
    return federal + state


# ═══════════════════════════════════════════════════════════════════
# 11. AUDIT PDF EXPORT
# ═══════════════════════════════════════════════════════════════════

def generate_audit_pdf(properties, bookings, expenses, time_entries, documents, contacts, maintenance, tax_year=None):
    from fpdf import FPDF
    if tax_year is None: tax_year = date.today().year
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    def s(t):
        if not isinstance(t, str): t = str(t)
        for o, n in {"\u2014":"-","\u2013":"-","\u2018":"'","\u2019":"'","\u201c":'"',"\u201d":'"',"\u2026":"...","\u2022":"*"}.items():
            t = t.replace(o, n)
        return t.encode("latin-1", errors="replace").decode("latin-1")

    def header(title):
        pdf.set_font("Helvetica","B",14)
        pdf.set_fill_color(30,41,59)
        pdf.set_text_color(255,255,255)
        pdf.cell(0,10,s(title),new_x="LMARGIN",new_y="NEXT",fill=True)
        pdf.set_text_color(0,0,0)
        pdf.ln(3)

    def lv(label, val, bold=False):
        pdf.set_font("Helvetica","",9)
        pdf.cell(55,6,s(label),new_x="RIGHT")
        pdf.set_font("Helvetica","B" if bold else "",9)
        pdf.cell(0,6,s(str(val)),new_x="LMARGIN",new_y="NEXT")

    # Cover
    pdf.add_page()
    pdf.set_font("Helvetica","B",24)
    pdf.ln(40)
    pdf.cell(0,15,s("SHORT-TERM RENTAL"),align="C",new_x="LMARGIN",new_y="NEXT")
    pdf.cell(0,15,s("OPERATIONS & TAX REPORT"),align="C",new_x="LMARGIN",new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica","",14)
    pdf.cell(0,10,s(f"Tax Year {tax_year}"),align="C",new_x="LMARGIN",new_y="NEXT")
    pdf.set_font("Helvetica","",11)
    pdf.cell(0,8,s(f"Prepared: {date.today().strftime('%B %d, %Y')}"),align="C",new_x="LMARGIN",new_y="NEXT")
    pdf.cell(0,8,s(f"Properties: {len(properties)}"),align="C",new_x="LMARGIN",new_y="NEXT")
    pdf.ln(20)
    pdf.set_font("Helvetica","I",9)
    pdf.cell(0,6,s("Generated by HostFlow STR Operations Platform"),align="C",new_x="LMARGIN",new_y="NEXT")
    pdf.cell(0,6,s("For tax preparation and audit documentation purposes."),align="C",new_x="LMARGIN",new_y="NEXT")

    # 1. Properties
    pdf.add_page()
    header("1. PROPERTY PORTFOLIO")
    for p in properties:
        pdf.set_font("Helvetica","B",11)
        pdf.cell(0,7,s(p.get("nickname") or p.get("name","")),new_x="LMARGIN",new_y="NEXT")
        lv("Address:", p.get("address",""))
        lv("City/State:", f"{p.get('city','')} {p.get('state','')} {p.get('zip_code','')}")
        lv("Type:", f"{p.get('property_type','')} {p.get('bedrooms',0)}BR/{p.get('bathrooms',0)}BA")
        lv("Purchase Price:", f"${p.get('purchase_price',0):,.0f}")
        lv("Mortgage:", f"${p.get('mortgage_payment',0):,.0f}/mo")
        lv("STR Permit:", p.get("str_permit_number","N/A"))
        lv("LLC:", p.get("llc_name","N/A"))
        pdf.ln(5)

    # 2. Revenue
    pdf.add_page()
    header("2. REVENUE SUMMARY")
    port = calculate_portfolio_metrics(bookings, properties, date(tax_year,1,1), date(tax_year,12,31))
    lv("Total Revenue:", f"${port['total_revenue']:,.2f}", bold=True)
    lv("Nights Booked:", str(port["total_nights_booked"]))
    lv("Avg Occupancy:", f"{port['avg_occupancy']}%")
    lv("Avg Nightly Rate:", f"${port['avg_nightly_rate']:,.2f}")
    lv("Total Bookings:", str(port["total_bookings"]))
    pdf.ln(5)
    for p in properties:
        pid = p.get("property_id","")
        pm = port["per_property"].get(pid, {})
        pdf.set_font("Helvetica","B",10)
        pdf.cell(0,6,s(p.get("nickname") or p.get("name","")),new_x="LMARGIN",new_y="NEXT")
        lv("  Revenue:", f"${pm.get('total_revenue',0):,.2f}")
        lv("  Occupancy:", f"{pm.get('occupancy_rate',0)}%")
        lv("  Nights:", str(pm.get("total_nights_booked",0)))

    # 3. Expenses
    pdf.add_page()
    header("3. EXPENSE DETAIL")
    yr_exp = [e for e in expenses if _parse_date(e.get("date","")) and _parse_date(e["date"]).year == tax_year]
    by_cat = {}
    for e in yr_exp:
        c = e.get("category","Other")
        by_cat.setdefault(c, []).append(e)
    total_exp = 0
    for cat in sorted(by_cat):
        items = by_cat[cat]
        ct = sum(i.get("amount",0) for i in items)
        total_exp += ct
        pdf.set_font("Helvetica","B",10)
        pdf.cell(0,6,s(f"{cat}: ${ct:,.2f}"),new_x="LMARGIN",new_y="NEXT")
        pdf.set_font("Helvetica","",8)
        for i in sorted(items, key=lambda x: x.get("date","")):
            vendor_str = f" ({i['vendor']})" if i.get('vendor') else ""
            pdf.cell(0,5,s(f"  {i.get('date','')} - {i.get('description','')} - ${i.get('amount',0):,.2f}{vendor_str}"),new_x="LMARGIN",new_y="NEXT")
        pdf.ln(2)
    pdf.set_font("Helvetica","B",11)
    pdf.cell(0,8,s(f"TOTAL: ${total_exp:,.2f}"),new_x="LMARGIN",new_y="NEXT")

    # 4. Schedule E
    pdf.add_page()
    header("4. SCHEDULE E PREPARATION")
    for p in properties:
        sc = generate_schedule_e_summary(p, bookings, expenses, tax_year)
        pdf.set_font("Helvetica","B",11)
        pdf.cell(0,7,s(f"{p.get('nickname') or p.get('name','')} - Schedule E"),new_x="LMARGIN",new_y="NEXT")
        lv("Address:", sc.get("property_address",""))
        lv("Rental Days:", str(sc.get("fair_rental_days",0)))
        lv("Line 3 Rents:", f"${sc.get('line_3_rents',0):,.2f}")
        lv("Line 7 Cleaning:", f"${sc.get('line_7_cleaning',0):,.2f}")
        lv("Line 9 Insurance:", f"${sc.get('line_9_insurance',0):,.2f}")
        lv("Line 14 Repairs:", f"${sc.get('line_14_repairs',0):,.2f}")
        lv("Line 15 Supplies:", f"${sc.get('line_15_supplies',0):,.2f}")
        lv("Line 16 Taxes:", f"${sc.get('line_16_taxes',0):,.2f}")
        lv("Line 17 Utilities:", f"${sc.get('line_17_utilities',0):,.2f}")
        lv("Line 19 Other:", f"${sc.get('line_19_other',0):,.2f}")
        lv("Total Expenses:", f"${sc.get('total_expenses',0):,.2f}", bold=True)
        lv("Net Income:", f"${sc.get('net_income',0):,.2f}", bold=True)
        pdf.ln(8)

    # 5. Time Log
    pdf.add_page()
    header("5. MATERIAL PARTICIPATION TIME LOG")
    ts = get_time_entry_summary_for_audit(time_entries, tax_year)
    pdf.set_font("Helvetica","B",10)
    pdf.cell(0,6,s(f"Total Hours: {ts['total_hours']:.2f} | Entries: {ts['total_entries']}"),new_x="LMARGIN",new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica","B",7)
    pdf.cell(22,5,"Date",border=1); pdf.cell(12,5,"Hours",border=1); pdf.cell(35,5,"Category",border=1)
    pdf.cell(0,5,"Description",border=1,new_x="LMARGIN",new_y="NEXT")
    pdf.set_font("Helvetica","",7)
    for e in ts["entries"]:
        if pdf.get_y() > 260:
            pdf.add_page()
            pdf.set_font("Helvetica","B",7)
            pdf.cell(22,5,"Date",border=1); pdf.cell(12,5,"Hours",border=1); pdf.cell(35,5,"Category",border=1)
            pdf.cell(0,5,"Description",border=1,new_x="LMARGIN",new_y="NEXT")
            pdf.set_font("Helvetica","",7)
        pdf.cell(22,5,s(e.get("date","")),border=1)
        pdf.cell(12,5,s(f"{e.get('hours',0):.2f}"),border=1)
        pdf.cell(35,5,s(e.get("category","")[:25]),border=1)
        pdf.cell(0,5,s(e.get("description","")[:80]),border=1,new_x="LMARGIN",new_y="NEXT")

    # 6. Material Participation Analysis
    pdf.add_page()
    header("6. MATERIAL PARTICIPATION ANALYSIS")
    mp = calculate_material_participation(time_entries, tax_year)
    lv("Total Hours:", f"{mp['total_hours']:.2f}")
    lv("Total Entries:", str(mp["total_entries"]))
    pdf.ln(3)
    pdf.set_font("Helvetica","B",10)
    pdf.cell(0,6,s("IRS Test 3: 100+ Hours (Largest Participant)"),new_x="LMARGIN",new_y="NEXT")
    lv("  Status:", "MET" if mp["test_3_met"] else "NOT YET MET")
    lv("  Progress:", f"{mp['test_3_pct']}%")
    if not mp["test_3_met"]: lv("  Remaining:", f"{mp['test_3_hours_needed']:.2f} hrs")
    pdf.ln(3)
    pdf.set_font("Helvetica","B",10)
    pdf.cell(0,6,s("IRS Test 1: 500-Hour Safe Harbor"),new_x="LMARGIN",new_y="NEXT")
    lv("  Status:", "MET" if mp["test_1_met"] else "NOT YET MET")
    lv("  Progress:", f"{mp['test_1_pct']}%")
    if not mp["test_1_met"]: lv("  Remaining:", f"{mp['test_1_hours_needed']:.2f} hrs")
    pdf.ln(5)
    pdf.set_font("Helvetica","B",10)
    pdf.cell(0,6,s("Hours by Category:"),new_x="LMARGIN",new_y="NEXT")
    pdf.set_font("Helvetica","",9)
    for cat, hrs in sorted(mp["hours_by_category"].items(), key=lambda x: -x[1]):
        pdf.cell(0,5,s(f"  {cat}: {hrs:.2f} hrs"),new_x="LMARGIN",new_y="NEXT")

    # 7. Documents
    pdf.add_page()
    header("7. DOCUMENT & RECEIPT INVENTORY")
    yr_docs = [d for d in documents if d.get("tax_year",0) == tax_year or (_parse_date(d.get("date","")) and _parse_date(d["date"]).year == tax_year)]
    if yr_docs:
        pdf.set_font("Helvetica","B",7)
        pdf.cell(22,5,"Date",border=1); pdf.cell(25,5,"Type",border=1); pdf.cell(50,5,"Title",border=1)
        pdf.cell(20,5,"Amount",border=1); pdf.cell(0,5,"Vendor",border=1,new_x="LMARGIN",new_y="NEXT")
        pdf.set_font("Helvetica","",7)
        for d in sorted(yr_docs, key=lambda x: x.get("date","")):
            pdf.cell(22,5,s(d.get("date","")),border=1)
            pdf.cell(25,5,s(d.get("doc_type","")[:18]),border=1)
            pdf.cell(50,5,s(d.get("title","")[:35]),border=1)
            amt = f"${d.get('amount',0):,.2f}" if d.get("amount") else ""
            pdf.cell(20,5,s(amt),border=1)
            pdf.cell(0,5,s(d.get("vendor","")[:25]),border=1,new_x="LMARGIN",new_y="NEXT")
    else:
        pdf.set_font("Helvetica","",10)
        pdf.cell(0,6,s("No documents logged."),new_x="LMARGIN",new_y="NEXT")

    # 8. Maintenance
    header("8. MAINTENANCE LOG")
    for item in maintenance:
        pn = next((p.get("nickname") or p.get("name","") for p in properties if p.get("property_id")==item.get("property_id")), "")
        pdf.set_font("Helvetica","B",9)
        pdf.cell(0,5,s(f"{item.get('title','')} - {pn}"),new_x="LMARGIN",new_y="NEXT")
        pdf.set_font("Helvetica","",8)
        pdf.cell(0,4,s(f"  Priority: {item.get('priority','')} | Status: {item.get('status','')} | Cost: ${item.get('cost',0):,.2f}"),new_x="LMARGIN",new_y="NEXT")
        pdf.ln(2)

    # 9. Contacts
    pdf.add_page()
    header("9. CONTACT DIRECTORY")
    for c in contacts:
        pdf.set_font("Helvetica","B",9)
        pdf.cell(0,5,s(f"{c.get('name','')} - {c.get('role','')}"),new_x="LMARGIN",new_y="NEXT")
        pdf.set_font("Helvetica","",8)
        parts = [x for x in [c.get("phone"), c.get("email"), c.get("rate")] if x]
        pdf.cell(0,4,s(f"  {' | '.join(parts)}"),new_x="LMARGIN",new_y="NEXT")
        pdf.ln(1)

    # Disclaimer
    pdf.add_page()
    header("DISCLAIMER")
    pdf.set_font("Helvetica","",9)
    pdf.multi_cell(0,5,s("This report was generated by HostFlow for tax preparation and audit documentation. Based on user-entered data, not independently verified. Does not constitute tax advice. Consult a qualified CPA for guidance on material participation, passive activity rules, and Schedule E reporting. The IRS requires contemporaneous records for material participation claims. Retain all original documents 7+ years."))

    return pdf.output()


# ═══════════════════════════════════════════════════════════════════
# 15. iCAL IMPORT (Airbnb / VRBO / Booking.com calendar sync)
# ═══════════════════════════════════════════════════════════════════

def parse_ical(ical_text, property_id="", platform="Airbnb", default_rate=150.0, cleaning_fee=75.0):
    """
    Parse iCal (.ics) text into booking dicts.
    
    Airbnb iCal format:
        SUMMARY: "Reserved" or guest name or "Not available" (blocked)
        DTSTART;VALUE=DATE:20260315
        DTEND;VALUE=DATE:20260318
        UID: unique booking ref
        DESCRIPTION: sometimes has phone, # of guests

    VRBO iCal format:
        SUMMARY: "Reserved - XXXX" or "Booked - Guest Name"
        Similar DTSTART/DTEND structure

    Booking.com:
        SUMMARY: "CLOSED - Not available" or "Booking.com - Guest"
    """
    if not ical_text or not ical_text.strip():
        return [], []

    bookings = []
    blocked = []
    lines = ical_text.replace("\r\n ", "").replace("\r\n\t", "").splitlines()

    in_event = False
    event = {}

    for line in lines:
        line = line.strip()

        if line == "BEGIN:VEVENT":
            in_event = True
            event = {}
        elif line == "END:VEVENT":
            in_event = False
            if event:
                parsed = _process_ical_event(event, property_id, platform, default_rate, cleaning_fee)
                if parsed:
                    if parsed.get("_blocked"):
                        blocked.append(parsed)
                    else:
                        bookings.append(parsed)
            event = {}
        elif in_event:
            if ":" in line:
                key, _, val = line.partition(":")
                # Handle params like DTSTART;VALUE=DATE:20260315
                key_base = key.split(";")[0]
                event[key_base] = val

    return bookings, blocked


def _process_ical_event(event, property_id, platform, default_rate, cleaning_fee):
    """Convert a parsed iCal VEVENT dict into a booking dict."""
    summary = event.get("SUMMARY", "")
    dtstart = event.get("DTSTART", "")
    dtend = event.get("DTEND", "")
    uid = event.get("UID", "")
    description = event.get("DESCRIPTION", "")

    # Parse dates — iCal uses YYYYMMDD or YYYYMMDDTHHMMSS
    check_in = _parse_ical_date(dtstart)
    check_out = _parse_ical_date(dtend)
    if not check_in or not check_out:
        return None

    # Detect blocked dates vs actual bookings
    summary_lower = summary.lower()
    is_blocked = any(kw in summary_lower for kw in [
        "not available", "blocked", "closed", "airbnb (not available)",
        "owner block", "maintenance", "unavailable",
    ])

    if is_blocked:
        return {
            "_blocked": True,
            "start": check_in.isoformat(),
            "end": check_out.isoformat(),
            "reason": summary,
            "property_id": property_id,
        }

    # Extract guest name from summary
    guest_name = _extract_guest_name(summary, platform)

    # Try to extract details from description
    num_guests = 2  # default
    phone = ""
    if description:
        desc_lower = description.lower()
        # Airbnb sometimes includes "Phone: +1..."
        if "phone" in desc_lower:
            for part in description.split("\n"):
                if "phone" in part.lower():
                    phone = part.split(":", 1)[-1].strip() if ":" in part else ""
        # Guest count
        for part in description.split("\n"):
            pl = part.lower()
            if "guest" in pl:
                import re
                nums = re.findall(r"\d+", part)
                if nums:
                    num_guests = int(nums[0])

    num_nights = max((check_out - check_in).days, 1)
    payout, plat_fee = calculate_payout(default_rate, num_nights, cleaning_fee)

    return {
        "booking_id": generate_id(),
        "property_id": property_id,
        "guest_name": guest_name,
        "guest_phone": phone,
        "guest_email": "",
        "num_guests": num_guests,
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "num_nights": num_nights,
        "nightly_rate": default_rate,
        "cleaning_fee": cleaning_fee,
        "total_payout": payout,
        "platform": platform,
        "platform_fee": plat_fee,
        "status": "confirmed" if check_in > date.today() else ("checked_in" if check_out > date.today() else "checked_out"),
        "special_requests": "",
        "guest_notes": f"Imported from iCal. UID: {uid[:40]}" if uid else "Imported from iCal",
        "turnover_status": "pending",
        "cleaner_confirmed": False,
        "ical_uid": uid,
        "created_date": date.today().isoformat(),
    }


def _parse_ical_date(dt_str):
    """Parse iCal date formats: YYYYMMDD or YYYYMMDDTHHMMSS or YYYYMMDDTHHMMSSZ"""
    if not dt_str:
        return None
    dt_str = dt_str.strip().rstrip("Z")
    for fmt in ("%Y%m%d", "%Y%m%dT%H%M%S"):
        try:
            return datetime.strptime(dt_str, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _extract_guest_name(summary, platform):
    """Extract guest name from iCal SUMMARY field."""
    if not summary:
        return "Guest (iCal)"

    s = summary.strip()
    sl = s.lower()

    # Airbnb: "Reserved" (no name), or just the name, or "Name (HMXXXXXXX)"
    if sl == "reserved" or sl == "airbnb (reserved)":
        return "Airbnb Guest"

    # VRBO: "Reserved - XXXX" or "Booked - Name"
    if " - " in s:
        parts = s.split(" - ", 1)
        if parts[0].lower() in ("reserved", "booked", "vrbo", "booking.com"):
            name = parts[1].strip()
            return name if name and name.lower() not in ("reserved", "booked") else f"{platform} Guest"
        return parts[1].strip() or f"{platform} Guest"

    # Airbnb confirmation code in parens: "John Smith (HMXXXXXXX)"
    if "(" in s:
        name = s.split("(")[0].strip()
        if name:
            return name

    # Clean common prefixes
    for prefix in ["Airbnb ", "VRBO ", "Booking.com "]:
        if s.startswith(prefix):
            s = s[len(prefix):]

    return s if s else f"{platform} Guest"


def fetch_ical_from_url(url):
    """Fetch iCal data from a URL. Works on Streamlit Cloud (network enabled)."""
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "HostFlow/2.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"ERROR: {e}"


def deduplicate_ical_bookings(existing_bookings, new_bookings):
    """
    Avoid duplicate imports. Match by property_id + check_in + check_out.
    Returns only new bookings that don't already exist.
    """
    existing_keys = set()
    for b in existing_bookings:
        key = (b.get("property_id",""), b.get("check_in",""), b.get("check_out",""))
        existing_keys.add(key)

    unique = []
    dupes = 0
    for b in new_bookings:
        key = (b.get("property_id",""), b.get("check_in",""), b.get("check_out",""))
        if key not in existing_keys:
            unique.append(b)
            existing_keys.add(key)
        else:
            dupes += 1

    return unique, dupes


# ═══════════════════════════════════════════════════════════════════
# 16. GOOGLE SHEETS PERSISTENCE
# ═══════════════════════════════════════════════════════════════════

# Tab definitions: (tab_name, header_row)
SHEETS_TABS = {
    "properties": [
        "Property_ID", "Name", "Nickname", "Address", "City", "State", "Zip",
        "Platform", "Type", "Bedrooms", "Bathrooms", "Max_Guests",
        "Base_Rate", "Cleaning_Fee", "Min_Nights", "Status",
        "Purchase_Price", "Mortgage_Mo", "Property_Tax_Yr", "Insurance_Yr",
        "HOA_Mo", "Down_Payment", "Closing_Costs", "Furnishing",
        "STR_Permit", "Business_License", "LLC", "EIN",
        "Cleaner_Name", "Cleaner_Rate", "WiFi", "Check_In_Time", "Check_Out_Time",
        "Full_JSON",
    ],
    "bookings": [
        "Booking_ID", "Property_ID", "Guest_Name", "Check_In", "Check_Out",
        "Nights", "Nightly_Rate", "Cleaning_Fee", "Total_Payout", "Platform",
        "Status", "Turnover_Status", "Cleaner_Confirmed", "Full_JSON",
    ],
    "expenses": [
        "Expense_ID", "Property_ID", "Date", "Category", "Description",
        "Amount", "Vendor", "Tax_Deductible", "Receipt_Doc_ID", "Notes",
    ],
    "time_entries": [
        "Entry_ID", "Property_ID", "Date", "Hours", "Category",
        "Description", "Platform", "Communication_With", "Start_Time", "End_Time",
        "Verified",
    ],
    "contacts": [
        "Contact_ID", "Name", "Role", "Company", "Phone", "Email",
        "Rate", "Property_IDs", "Notes",
    ],
    "documents": [
        "Doc_ID", "Property_ID", "Doc_Type", "Title", "Date",
        "Amount", "Vendor", "Category", "Tax_Year", "Filename", "Description",
    ],
    "maintenance": [
        "Item_ID", "Property_ID", "Title", "Priority", "Status",
        "Reported_Date", "Resolved_Date", "Cost", "Vendor", "Description",
    ],
}


def ensure_worksheets(spreadsheet):
    """Create any missing tabs with headers."""
    existing = [ws.title for ws in spreadsheet.worksheets()]
    for tab_name, headers in SHEETS_TABS.items():
        if tab_name not in existing:
            ws = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=len(headers))
            ws.append_row(headers)
    return True


def save_property_to_sheets(ws, prop):
    """Save a single property to the properties sheet."""
    row = [
        prop.get("property_id",""), prop.get("name",""), prop.get("nickname",""),
        prop.get("address",""), prop.get("city",""), prop.get("state",""), prop.get("zip_code",""),
        prop.get("platform",""), prop.get("property_type",""),
        prop.get("bedrooms",0), prop.get("bathrooms",0), prop.get("max_guests",0),
        prop.get("base_nightly_rate",0), prop.get("cleaning_fee",0), prop.get("min_nights",0),
        prop.get("status","active"),
        prop.get("purchase_price",0), prop.get("mortgage_payment",0),
        prop.get("property_tax_annual",0), prop.get("insurance_annual",0),
        prop.get("hoa_monthly",0), prop.get("down_payment",0),
        prop.get("closing_costs",0), prop.get("furnishing_cost",0),
        prop.get("str_permit_number",""), prop.get("business_license",""),
        prop.get("llc_name",""), prop.get("ein",""),
        prop.get("cleaner_name",""), prop.get("cleaner_rate",0),
        prop.get("wifi_password",""), prop.get("check_in_time",""), prop.get("check_out_time",""),
        to_json(prop),
    ]
    ws.append_row(row)


def save_booking_to_sheets(ws, booking):
    row = [
        booking.get("booking_id",""), booking.get("property_id",""),
        booking.get("guest_name",""), booking.get("check_in",""), booking.get("check_out",""),
        booking.get("num_nights",0), booking.get("nightly_rate",0),
        booking.get("cleaning_fee",0), booking.get("total_payout",0),
        booking.get("platform",""), booking.get("status",""),
        booking.get("turnover_status",""), booking.get("cleaner_confirmed",False),
        to_json(booking),
    ]
    ws.append_row(row)


def save_expense_to_sheets(ws, expense):
    row = [
        expense.get("expense_id",""), expense.get("property_id",""),
        expense.get("date",""), expense.get("category",""), expense.get("description",""),
        expense.get("amount",0), expense.get("vendor",""),
        expense.get("tax_deductible",True), expense.get("receipt_doc_id",""),
        expense.get("notes",""),
    ]
    ws.append_row(row)


def save_time_entry_to_sheets(ws, entry):
    row = [
        entry.get("entry_id",""), entry.get("property_id",""),
        entry.get("date",""), entry.get("hours",0), entry.get("category",""),
        entry.get("description",""), entry.get("platform",""),
        entry.get("communication_with",""), entry.get("start_time",""),
        entry.get("end_time",""), entry.get("verified",True),
    ]
    ws.append_row(row)


def save_contact_to_sheets(ws, contact):
    row = [
        contact.get("contact_id",""), contact.get("name",""),
        contact.get("role",""), contact.get("company",""),
        contact.get("phone",""), contact.get("email",""),
        contact.get("rate",""),
        json.dumps(contact.get("property_ids",[])),
        contact.get("notes",""),
    ]
    ws.append_row(row)


def save_document_to_sheets(ws, doc):
    row = [
        doc.get("doc_id",""), doc.get("property_id",""),
        doc.get("doc_type",""), doc.get("title",""),
        doc.get("date",""), doc.get("amount",0), doc.get("vendor",""),
        doc.get("category",""), doc.get("tax_year",0),
        doc.get("filename",""), doc.get("description",""),
    ]
    ws.append_row(row)


def save_maintenance_to_sheets(ws, item):
    row = [
        item.get("item_id",""), item.get("property_id",""),
        item.get("title",""), item.get("priority",""), item.get("status",""),
        item.get("reported_date",""), item.get("resolved_date",""),
        item.get("cost",0), item.get("vendor",""), item.get("description",""),
    ]
    ws.append_row(row)


def load_all_from_sheets(spreadsheet):
    """Load all data from Google Sheets. Returns dict of lists."""
    data = {
        "properties": [], "bookings": [], "expenses": [],
        "time_entries": [], "contacts": [], "documents": [], "maintenance": [],
    }

    try:
        ws = spreadsheet.worksheet("properties")
        rows = ws.get_all_records()
        for r in rows:
            if r.get("Full_JSON"):
                prop = from_json(r["Full_JSON"])
                if prop:
                    data["properties"].append(prop)
                    continue
            # Fallback: build from columns
            data["properties"].append({
                "property_id": r.get("Property_ID",""), "name": r.get("Name",""),
                "nickname": r.get("Nickname",""), "address": r.get("Address",""),
                "city": r.get("City",""), "state": r.get("State",""),
                "zip_code": r.get("Zip",""), "platform": r.get("Platform",""),
                "property_type": r.get("Type",""), "bedrooms": r.get("Bedrooms",0),
                "bathrooms": r.get("Bathrooms",0), "max_guests": r.get("Max_Guests",0),
                "base_nightly_rate": float(r.get("Base_Rate",0)),
                "cleaning_fee": float(r.get("Cleaning_Fee",0)),
                "min_nights": r.get("Min_Nights",2), "status": r.get("Status","active"),
                "purchase_price": float(r.get("Purchase_Price",0)),
                "mortgage_payment": float(r.get("Mortgage_Mo",0)),
                "property_tax_annual": float(r.get("Property_Tax_Yr",0)),
                "insurance_annual": float(r.get("Insurance_Yr",0)),
                "hoa_monthly": float(r.get("HOA_Mo",0)),
                "down_payment": float(r.get("Down_Payment",0)),
                "closing_costs": float(r.get("Closing_Costs",0)),
                "furnishing_cost": float(r.get("Furnishing",0)),
                "str_permit_number": r.get("STR_Permit",""),
                "business_license": r.get("Business_License",""),
                "llc_name": r.get("LLC",""), "ein": r.get("EIN",""),
                "cleaner_name": r.get("Cleaner_Name",""),
                "cleaner_rate": float(r.get("Cleaner_Rate",0)),
                "wifi_password": r.get("WiFi",""),
                "check_in_time": r.get("Check_In_Time","3:00 PM"),
                "check_out_time": r.get("Check_Out_Time","11:00 AM"),
            })
    except Exception:
        pass

    try:
        ws = spreadsheet.worksheet("bookings")
        rows = ws.get_all_records()
        for r in rows:
            if r.get("Full_JSON"):
                bk = from_json(r["Full_JSON"])
                if bk:
                    data["bookings"].append(bk)
                    continue
            data["bookings"].append({
                "booking_id": r.get("Booking_ID",""), "property_id": r.get("Property_ID",""),
                "guest_name": r.get("Guest_Name",""), "check_in": r.get("Check_In",""),
                "check_out": r.get("Check_Out",""), "num_nights": int(r.get("Nights",0)),
                "nightly_rate": float(r.get("Nightly_Rate",0)),
                "cleaning_fee": float(r.get("Cleaning_Fee",0)),
                "total_payout": float(r.get("Total_Payout",0)),
                "platform": r.get("Platform",""), "status": r.get("Status","confirmed"),
                "turnover_status": r.get("Turnover_Status","pending"),
                "cleaner_confirmed": str(r.get("Cleaner_Confirmed","")).lower() == "true",
            })
    except Exception:
        pass

    try:
        ws = spreadsheet.worksheet("expenses")
        for r in ws.get_all_records():
            data["expenses"].append({
                "expense_id": r.get("Expense_ID",""), "property_id": r.get("Property_ID",""),
                "date": r.get("Date",""), "category": r.get("Category",""),
                "description": r.get("Description",""), "amount": float(r.get("Amount",0)),
                "vendor": r.get("Vendor",""),
                "tax_deductible": str(r.get("Tax_Deductible","")).lower() != "false",
                "receipt_doc_id": r.get("Receipt_Doc_ID",""), "notes": r.get("Notes",""),
            })
    except Exception:
        pass

    try:
        ws = spreadsheet.worksheet("time_entries")
        for r in ws.get_all_records():
            data["time_entries"].append({
                "entry_id": r.get("Entry_ID",""), "property_id": r.get("Property_ID",""),
                "date": r.get("Date",""), "hours": float(r.get("Hours",0)),
                "category": r.get("Category",""), "description": r.get("Description",""),
                "platform": r.get("Platform",""),
                "communication_with": r.get("Communication_With",""),
                "start_time": r.get("Start_Time",""), "end_time": r.get("End_Time",""),
                "verified": str(r.get("Verified","")).lower() != "false",
            })
    except Exception:
        pass

    try:
        ws = spreadsheet.worksheet("contacts")
        for r in ws.get_all_records():
            pids = r.get("Property_IDs","")
            try:
                pids = json.loads(pids) if pids else []
            except:
                pids = []
            data["contacts"].append({
                "contact_id": r.get("Contact_ID",""), "name": r.get("Name",""),
                "role": r.get("Role",""), "company": r.get("Company",""),
                "phone": r.get("Phone",""), "email": r.get("Email",""),
                "rate": r.get("Rate",""), "property_ids": pids, "notes": r.get("Notes",""),
            })
    except Exception:
        pass

    try:
        ws = spreadsheet.worksheet("documents")
        for r in ws.get_all_records():
            data["documents"].append({
                "doc_id": r.get("Doc_ID",""), "property_id": r.get("Property_ID",""),
                "doc_type": r.get("Doc_Type",""), "title": r.get("Title",""),
                "date": r.get("Date",""), "amount": float(r.get("Amount",0)),
                "vendor": r.get("Vendor",""), "category": r.get("Category",""),
                "tax_year": int(r.get("Tax_Year",0)) if r.get("Tax_Year") else 0,
                "filename": r.get("Filename",""), "description": r.get("Description",""),
            })
    except Exception:
        pass

    try:
        ws = spreadsheet.worksheet("maintenance")
        for r in ws.get_all_records():
            data["maintenance"].append({
                "item_id": r.get("Item_ID",""), "property_id": r.get("Property_ID",""),
                "title": r.get("Title",""), "priority": r.get("Priority","medium"),
                "status": r.get("Status","open"),
                "reported_date": r.get("Reported_Date",""),
                "resolved_date": r.get("Resolved_Date",""),
                "cost": float(r.get("Cost",0)), "vendor": r.get("Vendor",""),
                "description": r.get("Description",""),
            })
    except Exception:
        pass

    return data


def sync_all_to_sheets(spreadsheet, properties, bookings, expenses, time_entries, contacts, documents, maintenance):
    """Full sync: clear all tabs and rewrite. Use for periodic save-all."""
    ensure_worksheets(spreadsheet)

    # Properties
    ws = spreadsheet.worksheet("properties")
    ws.clear()
    ws.append_row(SHEETS_TABS["properties"])
    for p in properties:
        save_property_to_sheets(ws, p)

    # Bookings
    ws = spreadsheet.worksheet("bookings")
    ws.clear()
    ws.append_row(SHEETS_TABS["bookings"])
    for b in bookings:
        save_booking_to_sheets(ws, b)

    # Expenses
    ws = spreadsheet.worksheet("expenses")
    ws.clear()
    ws.append_row(SHEETS_TABS["expenses"])
    for e in expenses:
        save_expense_to_sheets(ws, e)

    # Time Entries
    ws = spreadsheet.worksheet("time_entries")
    ws.clear()
    ws.append_row(SHEETS_TABS["time_entries"])
    for t in time_entries:
        save_time_entry_to_sheets(ws, t)

    # Contacts
    ws = spreadsheet.worksheet("contacts")
    ws.clear()
    ws.append_row(SHEETS_TABS["contacts"])
    for c in contacts:
        save_contact_to_sheets(ws, c)

    # Documents
    ws = spreadsheet.worksheet("documents")
    ws.clear()
    ws.append_row(SHEETS_TABS["documents"])
    for d in documents:
        save_document_to_sheets(ws, d)

    # Maintenance
    ws = spreadsheet.worksheet("maintenance")
    ws.clear()
    ws.append_row(SHEETS_TABS["maintenance"])
    for m in maintenance:
        save_maintenance_to_sheets(ws, m)

    return True


# ═══════════════════════════════════════════════════════════════════
# 17. HELPERS
# ═══════════════════════════════════════════════════════════════════

def to_json(data): return json.dumps(data, default=str)
def from_json(s):
    try: return json.loads(s)
    except: return {}

def _parse_date(ds):
    if isinstance(ds, date): return ds
    if not ds: return None
    for f in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"):
        try: return datetime.strptime(ds, f).date()
        except: continue
    return None

def generate_id(): return datetime.now().strftime("%Y%m%d%H%M%S%f")[:18]

def nights_between(ci, co):
    a, b = _parse_date(ci), _parse_date(co)
    return max((b-a).days, 0) if a and b else 0

def calculate_payout(rate, nights, clean, pct=0.03):
    g = (rate * nights) + clean
    f = g * pct
    return round(g - f, 2), round(f, 2)

def format_currency(a): return f"${a:,.2f}" if a else "$0.00"


# ═══════════════════════════════════════════════════════════════════
# 18. DEMO DATA
# ═══════════════════════════════════════════════════════════════════

def generate_demo_data():
    td = date.today()
    ty = td.year

    properties = [
        {"property_id":"prop_001","name":"Downtown Loft","nickname":"Loft","address":"456 Main St, Unit 3A","city":"San Jose","state":"CA","zip_code":"95112","county":"Santa Clara","platform":"Airbnb","property_type":"Entire home","bedrooms":1,"bathrooms":1.0,"max_guests":4,"base_nightly_rate":165.0,"cleaning_fee":85.0,"min_nights":2,"cleaner_name":"Maria's Cleaning Co","cleaner_phone":"(555) 234-5678","cleaner_rate":85.0,"wifi_password":"LoftGuest2026","check_in_time":"3:00 PM","check_out_time":"11:00 AM","check_in_instructions":"Lockbox 4521. Unit 3A, 3rd floor, elevator right.","house_rules":"No smoking. No parties. Quiet 10pm-8am. Max 4 guests.","parking_info":"Free street parking. Garage $15/day.","amenities":["WiFi","TV","Kitchen","Washer","Dryer","Air conditioning","Workspace","Self check-in"],"notes":"Upstairs neighbor sensitive to noise.","purchase_price":420000,"current_value":465000,"mortgage_payment":2100,"mortgage_balance":336000,"interest_rate":6.5,"property_tax_annual":5250,"insurance_annual":1800,"hoa_monthly":350,"down_payment":84000,"closing_costs":12600,"furnishing_cost":15000,"startup_costs":3000,"str_permit_number":"STR-2025-4521","str_permit_expiry":"2026-12-31","llc_name":"Loft Stays LLC","ein":"XX-XXXXXXX","status":"active","created_date":"2025-06-01"},
        {"property_id":"prop_002","name":"Beachside Bungalow","nickname":"Beach","address":"789 Ocean Dr","city":"Santa Cruz","state":"CA","zip_code":"95060","county":"Santa Cruz","platform":"Multi","property_type":"Entire home","bedrooms":2,"bathrooms":2.0,"max_guests":6,"base_nightly_rate":225.0,"cleaning_fee":120.0,"min_nights":3,"cleaner_name":"Coastal Cleans","cleaner_phone":"(555) 876-5432","cleaner_rate":120.0,"wifi_password":"BeachLife2026","check_in_time":"4:00 PM","check_out_time":"10:00 AM","check_in_instructions":"Smart lock code sent day of. Beach access back gate.","house_rules":"No smoking. No parties >6. Outdoor shower for sand.","parking_info":"Driveway fits 2 cars.","amenities":["WiFi","TV","Kitchen","Free parking","BBQ grill","Beach access","Ocean view","Smart lock"],"notes":"Hot water heater temperamental.","purchase_price":685000,"current_value":720000,"mortgage_payment":3425,"mortgage_balance":548000,"interest_rate":6.25,"property_tax_annual":8560,"insurance_annual":3200,"hoa_monthly":0,"down_payment":137000,"closing_costs":20550,"furnishing_cost":22000,"startup_costs":5000,"str_permit_number":"SC-STR-2025-789","str_permit_expiry":"2026-06-30","llc_name":"Coastal Stays LLC","status":"active","created_date":"2025-03-15"},
    ]

    bookings = [
        {"booking_id":"bk_001","property_id":"prop_001","guest_name":"Sarah Chen","guest_phone":"(555) 111-2222","num_guests":2,"check_in":(td-timedelta(days=2)).isoformat(),"check_out":(td+timedelta(days=1)).isoformat(),"num_nights":3,"nightly_rate":165.0,"cleaning_fee":85.0,"total_payout":570.0,"platform":"Airbnb","platform_fee":17.10,"status":"checked_in","special_requests":"Late check-in ~9pm","turnover_status":"pending","cleaner_confirmed":False,"created_date":(td-timedelta(days=14)).isoformat()},
        {"booking_id":"bk_002","property_id":"prop_001","guest_name":"Mike Johnson","guest_phone":"(555) 333-4444","num_guests":3,"check_in":(td+timedelta(days=2)).isoformat(),"check_out":(td+timedelta(days=5)).isoformat(),"num_nights":3,"nightly_rate":175.0,"cleaning_fee":85.0,"total_payout":610.0,"platform":"Airbnb","platform_fee":18.30,"status":"confirmed","turnover_status":"pending","cleaner_confirmed":False,"created_date":(td-timedelta(days=7)).isoformat()},
        {"booking_id":"bk_003","property_id":"prop_002","guest_name":"The Rivera Family","guest_phone":"(555) 555-6666","num_guests":5,"check_in":td.isoformat(),"check_out":(td+timedelta(days=4)).isoformat(),"num_nights":4,"nightly_rate":240.0,"cleaning_fee":120.0,"total_payout":1080.0,"platform":"VRBO","platform_fee":32.40,"status":"confirmed","special_requests":"Traveling with toddler","turnover_status":"complete","cleaner_confirmed":True,"created_date":(td-timedelta(days=21)).isoformat()},
        {"booking_id":"bk_004","property_id":"prop_002","guest_name":"David Park","guest_phone":"(555) 777-8888","num_guests":2,"check_in":(td+timedelta(days=6)).isoformat(),"check_out":(td+timedelta(days=9)).isoformat(),"num_nights":3,"nightly_rate":225.0,"cleaning_fee":120.0,"total_payout":795.0,"platform":"Airbnb","platform_fee":23.85,"status":"confirmed","turnover_status":"pending","cleaner_confirmed":False,"created_date":(td-timedelta(days=3)).isoformat()},
    ]

    expenses = [
        {"expense_id":"exp_001","property_id":"prop_001","category":"Cleaning","description":"Regular turnover","amount":85.0,"date":(td-timedelta(days=5)).isoformat(),"vendor":"Maria's Cleaning","tax_deductible":True,"recurring":True},
        {"expense_id":"exp_002","property_id":"prop_001","category":"Supplies (Guest)","description":"Toiletries restock","amount":45.0,"date":(td-timedelta(days=3)).isoformat(),"vendor":"Amazon","tax_deductible":True},
        {"expense_id":"exp_003","property_id":"prop_002","category":"Cleaning","description":"Deep clean","amount":120.0,"date":(td-timedelta(days=1)).isoformat(),"vendor":"Coastal Cleans","tax_deductible":True},
        {"expense_id":"exp_004","property_id":"prop_001","category":"Software/Tools","description":"PriceLabs","amount":19.99,"date":(td-timedelta(days=15)).isoformat(),"vendor":"PriceLabs","tax_deductible":True,"recurring":True},
        {"expense_id":"exp_005","property_id":"prop_001","category":"Utilities (Internet/Cable)","description":"Internet","amount":79.99,"date":(td-timedelta(days=10)).isoformat(),"vendor":"Comcast","tax_deductible":True,"recurring":True},
    ]

    maintenance = [{"item_id":"mx_001","property_id":"prop_002","title":"Hot water heater noise","description":"Guests reported intermittent banging.","priority":"medium","status":"open","reported_date":(td-timedelta(days=5)).isoformat()}]

    time_entries = []
    cats = ["Guest Communication","Booking Management","Revenue Management","Turnover Coordination","Maintenance Coordination","Financial/Bookkeeping","Listing Management","Research/Education","Team Management","Property Inspection"]
    for i in range(25):
        d = td - timedelta(days=i*3+1)
        if d.year == ty:
            cat = cats[i % len(cats)]
            hrs = round(0.5 + (i % 5) * 0.5, 2)
            time_entries.append({"entry_id":f"te_{i:03d}","property_id":"prop_001" if i%3 else "prop_002","date":d.isoformat(),"start_time":"09:00 AM","end_time":f"{9+int(hrs)}:{int((hrs%1)*60):02d} AM","hours":hrs,"category":cat,"description":f"{cat} - property management activity","platform":"Airbnb" if "Communication" in cat else "","verified":True})

    contacts = [
        {"contact_id":"ct_001","name":"Maria Gonzalez","role":"Cleaner","company":"Maria's Cleaning Co","phone":"(555) 234-5678","email":"maria@cleaning.co","property_ids":["prop_001"],"rate":"$85/turnover","notes":"Reliable. 48hr notice preferred."},
        {"contact_id":"ct_002","name":"Jake Thompson","role":"Cleaner","company":"Coastal Cleans","phone":"(555) 876-5432","email":"jake@coastalcleans.com","property_ids":["prop_002"],"rate":"$120/turnover"},
        {"contact_id":"ct_003","name":"Lisa Park","role":"Accountant/CPA","company":"Park Tax Services","phone":"(555) 999-0000","email":"lisa@parktax.com","property_ids":["prop_001","prop_002"],"rate":"$200/hr","notes":"STR specialist."},
        {"contact_id":"ct_004","name":"Mike Reyes","role":"Handyman/Maintenance","phone":"(555) 444-3333","property_ids":["prop_001","prop_002"],"rate":"$75/hr","notes":"Weekdays only."},
    ]

    documents = [
        {"doc_id":"doc_001","property_id":"prop_001","doc_type":"Permit/License","title":"STR Permit 2025-2026","date":"2025-06-01","tax_year":2025},
        {"doc_id":"doc_002","property_id":"prop_001","doc_type":"Receipt","title":"West Elm furniture","amount":3200.0,"vendor":"West Elm","date":"2025-05-15","category":"Furnishing/Decor","tax_year":2025},
    ]

    return properties, bookings, maintenance, expenses, time_entries, contacts, documents


if __name__ == "__main__":
    props, bookings, mx, expenses, time_entries, contacts, documents = generate_demo_data()
    print("=" * 60)
    print("HOSTFLOW v2 - STR OPERATING SYSTEM")
    print("=" * 60)
    print(f"Properties: {len(props)}, Bookings: {len(bookings)}, Expenses: {len(expenses)}")
    print(f"Time Entries: {len(time_entries)}, Contacts: {len(contacts)}, Documents: {len(documents)}")

    briefing = generate_daily_briefing(props, bookings, mx)
    print(f"\nBriefing: {briefing['summary']}")

    mp = calculate_material_participation(time_entries)
    print(f"\nMaterial Participation: {mp['total_hours']} hrs")
    t3_status = "MET" if mp["test_3_met"] else f"Need {mp['test_3_hours_needed']:.1f} more"
    t1_status = "MET" if mp["test_1_met"] else f"Need {mp['test_1_hours_needed']:.1f} more"
    print(f"  100hr: {t3_status}")
    print(f"  500hr: {t1_status}")

    pf = calculate_proforma(props[0], 45000, {"Cleaning": 3400, "Supplies": 1200, "Utilities": 2400})
    print(f"\nProforma (Loft): NOI ${pf['noi']:,.0f}, CoC {pf['cash_on_cash']}%, Cap {pf['cap_rate']}%")

    print(f"\nCompliance (CA): {len(get_compliance_checklist('CA'))} items")

    pdf_bytes = generate_audit_pdf(props, bookings, expenses, time_entries, documents, contacts, mx)
    print(f"\nAudit PDF: {len(pdf_bytes):,} bytes")
