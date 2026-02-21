"""
HostFlow v2 — Complete STR Operating System
Daily ops + tax compliance + material participation + proforma + audit trail
"""

import streamlit as st
import json
import base64
import datetime
from datetime import date, timedelta
from collections import Counter

from str_logic import (
    Property, Booking, Expense, Contact, TimeEntry, Document, MaintenanceItem, ActivityLog,
    PLATFORMS, PROPERTY_TYPES, AMENITIES_OPTIONS, EXPENSE_CATEGORIES,
    TIME_CATEGORIES, CONTACT_ROLES, ACTIVITY_TYPES, DOCUMENT_TYPES,
    PRIORITY_COLORS, STATUS_COLORS, TURNOVER_COLORS,
    MESSAGE_TEMPLATES, fill_template,
    generate_daily_briefing, calculate_property_metrics, calculate_portfolio_metrics,
    get_gap_nights, get_pricing_suggestions,
    calculate_material_participation, get_time_entry_summary_for_audit,
    calculate_proforma, generate_schedule_e_summary,
    get_compliance_checklist, generate_audit_pdf,
    parse_ical, fetch_ical_from_url, deduplicate_ical_bookings,
    SHEETS_TABS, ensure_worksheets, load_all_from_sheets, sync_all_to_sheets,
    to_json, from_json, generate_id, nights_between, calculate_payout,
    format_currency, generate_demo_data, _parse_date,
)

# ─────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="HostFlow — STR Operating System", page_icon="🏠", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    :root { --primary:#2563EB; --success:#10B981; --warn:#F59E0B; --danger:#EF4444; --purple:#8B5CF6; --dark:#1E293B; }
    .action-card { background:white;border-radius:12px;padding:14px 16px;margin:6px 0;border-left:4px solid var(--primary);box-shadow:0 1px 3px rgba(0,0,0,.08); }
    .action-high { border-left-color:var(--danger); }
    .action-medium { border-left-color:var(--warn); }
    .action-low { border-left-color:var(--success); }
    .property-card { background:white;border-radius:12px;padding:16px;margin:8px 0;border-left:4px solid var(--primary);box-shadow:0 1px 3px rgba(0,0,0,.08); }
    .booking-card { background:white;border-radius:12px;padding:14px 16px;margin:6px 0;box-shadow:0 1px 3px rgba(0,0,0,.08); }
    .stat-card { background:linear-gradient(135deg,#1E293B,#334155);color:white;border-radius:14px;padding:18px;margin:6px 0;text-align:center; }
    .badge { display:inline-block;padding:2px 10px;border-radius:12px;font-size:.75rem;font-weight:700;color:white; }
    .metric-big { font-size:2rem;font-weight:800;color:var(--dark); }
    .metric-label { font-size:.8rem;color:#64748B;text-transform:uppercase;letter-spacing:.5px; }
    .timer-display { font-size:3.5rem;font-weight:800;font-family:monospace;text-align:center;padding:20px 0; }
    .progress-ring { background:#F1F5F9;border-radius:10px;padding:12px;margin:6px 0; }
    .message-preview { background:#F8FAFC;border-radius:10px;padding:14px;margin:8px 0;border:1px solid #E2E8F0;font-size:.9rem;white-space:pre-wrap; }
    .compliance-item { background:white;border-radius:10px;padding:12px;margin:4px 0;border-left:3px solid #E2E8F0; }
    .compliance-required { border-left-color:var(--danger); }
    .stButton > button { border-radius:10px;min-height:44px;font-weight:600; }
    .stExpander { border-radius:10px; }
    #MainMenu {visibility:hidden;} footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────
DEFAULTS = {
    "view": "briefing", "properties": [], "bookings": [], "maintenance": [],
    "expenses": [], "time_entries": [], "contacts": [], "documents": [],
    "activity_log": [], "ai_messages": [], "demo_loaded": False,
    "timer_running": False, "timer_start": None, "timer_property": "",
    "timer_category": "Guest Communication", "timer_description": "",
    "compliance_checks": {},
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────
# GOOGLE SHEETS
# ─────────────────────────────────────────────────────────────────────
SHEETS_AVAILABLE = False
gsheet = None
try:
    import gspread
    from google.oauth2.service_account import Credentials
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

    @st.cache_resource
    def get_gspread_client():
        if "gcp_service_account_json" in st.secrets:
            creds_dict = json.loads(st.secrets["gcp_service_account_json"])
        elif "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
        else:
            return None
        if "private_key" in creds_dict:
            key = creds_dict["private_key"]
            if "\\n" in key and "\n" not in key:
                creds_dict["private_key"] = key.replace("\\n", "\n")
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(creds)

    if "gcp_service_account_json" in st.secrets or "gcp_service_account" in st.secrets:
        gc = get_gspread_client()
        if gc and "sheet_url" in st.secrets:
            gsheet = gc.open_by_url(st.secrets["sheet_url"])
            ensure_worksheets(gsheet)
            SHEETS_AVAILABLE = True
except Exception:
    pass

def load_from_sheets():
    """Load all data from Google Sheets into session state."""
    if not SHEETS_AVAILABLE or not gsheet:
        return False
    try:
        data = load_all_from_sheets(gsheet)
        for key in ("properties", "bookings", "expenses", "time_entries", "contacts", "documents", "maintenance"):
            if data.get(key):
                st.session_state[key] = data[key]
        return True
    except Exception as e:
        st.error(f"Sheets load error: {e}")
        return False

def save_to_sheets():
    """Save all session state data to Google Sheets."""
    if not SHEETS_AVAILABLE or not gsheet:
        return False
    try:
        sync_all_to_sheets(
            gsheet, st.session_state.properties, st.session_state.bookings,
            st.session_state.expenses, st.session_state.time_entries,
            st.session_state.contacts, st.session_state.documents,
            st.session_state.maintenance,
        )
        return True
    except Exception as e:
        st.error(f"Sheets save error: {e}")
        return False

# Auto-load from sheets on first run
if SHEETS_AVAILABLE and not st.session_state.get("sheets_loaded"):
    load_from_sheets()
    st.session_state.sheets_loaded = True

# ─────────────────────────────────────────────────────────────────────
# AI
# ─────────────────────────────────────────────────────────────────────
AI_AVAILABLE = False
try:
    import anthropic
    if "anthropic_api_key" in st.secrets:
        ai_client = anthropic.Anthropic(api_key=st.secrets["anthropic_api_key"])
        AI_AVAILABLE = True
except Exception:
    pass

def get_ai_system_prompt():
    props = st.session_state.properties
    mp = calculate_material_participation(st.session_state.time_entries)
    prop_s = "\n".join(f"- {p.get('nickname',p.get('name',''))}: {p.get('bedrooms',0)}BR, ${p.get('base_nightly_rate',0)}/night, {p.get('city','')}, {p.get('state','')}" for p in props)
    return f"""You are HostFlow Assistant, an expert AI short-term rental operations and tax compliance advisor.

PORTFOLIO: {prop_s if prop_s else "No properties yet."}

MATERIAL PARTICIPATION: {mp['total_hours']:.1f} hrs logged ({mp['test_3_pct']}% toward 100hr test)
BOOKINGS: {len(st.session_state.bookings)} total
EXPENSES: {len(st.session_state.expenses)} entries

YOUR EXPERTISE: STR operations, IRS passive activity rules, material participation tests, Schedule E, proforma analysis, guest communication, pricing strategy, state/local compliance.
Be concise, actionable, and tax-aware. Flag audit risks proactively."""

def call_ai(messages, max_tokens=1200):
    if not AI_AVAILABLE:
        return "AI requires an Anthropic API key in secrets."
    try:
        return ai_client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=max_tokens,
            system=get_ai_system_prompt(), messages=messages[-10:]
        ).content[0].text
    except Exception as e:
        return f"AI error: {e}"


# ─────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────
def get_prop(pid):
    return next((p for p in st.session_state.properties if p.get("property_id") == pid), None)

def prop_name(pid):
    p = get_prop(pid)
    return (p.get("nickname") or p.get("name", "Unknown")) if p else "Unknown"

def badge(text, color="#6B7280"):
    return f'<span class="badge" style="background:{color};">{text}</span>'

def status_badge(status, cmap=STATUS_COLORS):
    return badge(status.replace("_"," ").title(), cmap.get(status, "#6B7280"))

def pri_icon(p):
    return {"low":"🟢","medium":"🟡","high":"🔴","urgent":"🚨"}.get(p,"⚪")

def nav_to(view):
    st.session_state.view = view
    st.rerun()


# ─────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:6px 0;">
    <h1 style="margin:0;font-size:1.7rem;">🏠 HostFlow</h1>
    <p style="margin:0;color:#64748B;font-size:.85rem;">STR Operating System · Tax Compliance · Audit Ready</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    host_name = st.text_input("Host Name", value="Host", key="host_nm")
    st.divider()

    # Material participation quick view
    mp = calculate_material_participation(st.session_state.time_entries)
    pct = mp["test_3_pct"]
    color = "#10B981" if pct >= 100 else "#F59E0B" if pct >= 50 else "#EF4444"
    st.markdown(f"""
    <div style="background:#F8FAFC;border-radius:10px;padding:12px;border-left:4px solid {color};">
        <div style="font-size:.75rem;color:#64748B;text-transform:uppercase;">100-Hour Test</div>
        <div style="font-size:1.4rem;font-weight:800;color:{color};">{mp['total_hours']:.1f} / 100 hrs</div>
        <div style="background:#E2E8F0;border-radius:6px;height:8px;margin-top:6px;">
            <div style="background:{color};border-radius:6px;height:8px;width:{min(pct,100)}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.metric("Properties", len(st.session_state.properties))
    st.metric("Active Bookings", len([b for b in st.session_state.bookings if b.get("status") in ("confirmed","checked_in")]))
    st.divider()

    if not st.session_state.demo_loaded:
        if st.button("🎲 Load Demo Data", use_container_width=True):
            props, books, mx, exp, time_e, contacts, docs = generate_demo_data()
            st.session_state.properties = props
            st.session_state.bookings = books
            st.session_state.maintenance = mx
            st.session_state.expenses = exp
            st.session_state.time_entries = time_e
            st.session_state.contacts = contacts
            st.session_state.documents = docs
            st.session_state.demo_loaded = True
            st.rerun()

    st.divider()
    st.markdown("### 💾 Data Sync")
    if SHEETS_AVAILABLE:
        st.success("Google Sheets: Connected", icon="✅")
        sc1, sc2 = st.columns(2)
        with sc1:
            if st.button("⬇️ Load", use_container_width=True, key="sb_load"):
                if load_from_sheets():
                    st.success("Loaded!")
                    st.rerun()
        with sc2:
            if st.button("⬆️ Save", use_container_width=True, key="sb_save"):
                if save_to_sheets():
                    st.success("Saved!")
    else:
        st.caption("Add `gcp_service_account_json` and `sheet_url` to secrets for cloud persistence.")


# ─── NAVIGATION ───
nav_views = [
    ("📋 Brief", "briefing"), ("⏱️ Time", "time_tracker"), ("🏠 Props", "properties"),
    ("📅 Book", "bookings"), ("📥 iCal", "ical_import"), ("💰 Finance", "finances"),
    ("💬 Msg", "messages"), ("📇 Team", "contacts"), ("✅ Comply", "compliance"),
    ("📎 Docs", "documents"), ("🤖 AI", "ai_chat"),
]
cols = st.columns(len(nav_views))
for i, (label, vk) in enumerate(nav_views):
    with cols[i]:
        if st.button(label, use_container_width=True, type="primary" if st.session_state.view == vk else "secondary"):
            nav_to(vk)
st.divider()


# ═══════════════════════════════════════════════════════════════════
# BRIEFING
# ═══════════════════════════════════════════════════════════════════
if st.session_state.view == "briefing":
    st.markdown(f"## 📋 Daily Briefing — {date.today().strftime('%A, %B %d')}")

    if not st.session_state.properties:
        st.info("Add properties and bookings to see your daily briefing, or load demo data from the sidebar.")
    else:
        briefing = generate_daily_briefing(st.session_state.properties, st.session_state.bookings, st.session_state.maintenance)
        occ = briefing["occupancy_rate"]
        occ_c = "#10B981" if occ >= 80 else "#F59E0B" if occ >= 50 else "#EF4444"
        mp = calculate_material_participation(st.session_state.time_entries)

        st.markdown(f"""
        <div class="stat-card">
            <div style="font-size:.85rem;opacity:.8;">TODAY'S SUMMARY</div>
            <div style="font-size:1.05rem;font-weight:600;margin:4px 0;">{briefing['summary']}</div>
            <div style="display:flex;gap:20px;justify-content:center;margin-top:12px;flex-wrap:wrap;">
                <div><span style="font-size:1.4rem;font-weight:800;color:{occ_c};">{occ:.0f}%</span><br><span style="font-size:.7rem;opacity:.7;">Occupancy</span></div>
                <div><span style="font-size:1.4rem;font-weight:800;">{len(briefing['active_stays'])}</span><br><span style="font-size:.7rem;opacity:.7;">Active</span></div>
                <div><span style="font-size:1.4rem;font-weight:800;">{len(briefing['actions'])}</span><br><span style="font-size:.7rem;opacity:.7;">Actions</span></div>
                <div><span style="font-size:1.4rem;font-weight:800;">{mp['total_hours']:.0f}h</span><br><span style="font-size:.7rem;opacity:.7;">Participation</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if briefing["actions"]:
            st.markdown("### 🎯 Action Items")
            for i, action in enumerate(briefing["actions"]):
                pri = action.get("priority","low")
                st.markdown(f'<div class="action-card action-{pri}">{pri_icon(pri)} {action["text"]}</div>', unsafe_allow_html=True)
                if action.get("template"):
                    if st.button(f"📝 Draft", key=f"dr_{i}", use_container_width=True):
                        prop = get_prop(action.get("property_id",""))
                        bk = next((b for b in st.session_state.bookings if b.get("property_id")==action.get("property_id","") and b.get("status")!="cancelled"), None)
                        if prop and bk:
                            st.session_state["draft_message"] = fill_template(action["template"], prop, bk)
                            st.session_state["draft_guest"] = bk.get("guest_name","")
                            nav_to("messages")

        # Check-ins
        if briefing["check_ins_today"]:
            st.markdown("### 🔑 Arriving Today")
            for item in briefing["check_ins_today"]:
                b = item["booking"]
                special = f'<br><span style="color:#F59E0B;font-size:.85rem;">📝 {b.get("special_requests","")}</span>' if b.get("special_requests") else ""
                st.markdown(f'<div class="booking-card" style="border-left:4px solid #10B981;"><strong>{b.get("guest_name","")}</strong> → {item["property"]}<br><span style="color:#64748B;font-size:.85rem;">{b.get("num_guests","")} guests · {b.get("num_nights","")} nights · {format_currency(b.get("total_payout",0))}</span>{special}</div>', unsafe_allow_html=True)

        if briefing["check_outs_today"]:
            st.markdown("### 👋 Departing Today")
            for item in briefing["check_outs_today"]:
                b = item["booking"]
                st.markdown(f'<div class="booking-card" style="border-left:4px solid #6B7280;"><strong>{b.get("guest_name","")}</strong> ← {item["property"]}<br>{status_badge(b.get("turnover_status","pending"), TURNOVER_COLORS)} Turnover</div>', unsafe_allow_html=True)

        if briefing["active_stays"]:
            st.markdown("### 🏨 Currently Hosted")
            for item in briefing["active_stays"]:
                b = item["booking"]
                st.markdown(f'<div class="booking-card" style="border-left:4px solid #8B5CF6;"><strong>{b.get("guest_name","")}</strong> at {item["property"]} · {item["nights_remaining"]} night{"s" if item["nights_remaining"]!=1 else ""} left</div>', unsafe_allow_html=True)

        # Pricing
        st.markdown("### 💰 Pricing Intelligence")
        has_s = False
        for prop in st.session_state.properties:
            for s in get_pricing_suggestions(st.session_state.bookings, prop):
                has_s = True
                st.markdown(f'<div class="action-card" style="border-left-color:#8B5CF6;">{s["message"]}<br><span style="color:#64748B;font-size:.8rem;">{s["reason"]}</span></div>', unsafe_allow_html=True)
        if not has_s:
            st.success("✅ No pricing gaps in next 14 days.")


# ═══════════════════════════════════════════════════════════════════
# TIME TRACKER + MATERIAL PARTICIPATION
# ═══════════════════════════════════════════════════════════════════
elif st.session_state.view == "time_tracker":
    st.markdown("## ⏱️ Time Tracker & Material Participation")

    # ── Live Timer ──
    st.markdown("### 🔴 Live Timer")
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        prop_opts = ["All Properties"] + [p.get("nickname") or p.get("name","") for p in st.session_state.properties]
        t_prop = st.selectbox("Property", prop_opts, key="tp_prop")
    with t_col2:
        t_cat = st.selectbox("Category", TIME_CATEGORIES, key="tp_cat")

    t_desc = st.text_input("What are you working on?", placeholder="e.g., Responding to guest inquiry about check-in", key="tp_desc")

    if st.session_state.timer_running:
        elapsed = (datetime.datetime.now() - st.session_state.timer_start).total_seconds()
        hrs = int(elapsed // 3600)
        mins = int((elapsed % 3600) // 60)
        secs = int(elapsed % 60)
        st.markdown(f'<div class="timer-display" style="color:#EF4444;">⏱️ {hrs:02d}:{mins:02d}:{secs:02d}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="text-align:center;color:#64748B;font-size:.85rem;">Timer running · {t_cat}</div>', unsafe_allow_html=True)

        if st.button("⏹️ Stop & Log Time", use_container_width=True, type="primary"):
            elapsed_hrs = round(elapsed / 3600, 2)
            pid = ""
            if t_prop != "All Properties":
                pid = next((p.get("property_id","") for p in st.session_state.properties if (p.get("nickname") or p.get("name",""))==t_prop), "")
            st.session_state.time_entries.append({
                "entry_id": generate_id(), "property_id": pid,
                "date": date.today().isoformat(),
                "start_time": st.session_state.timer_start.strftime("%H:%M"),
                "end_time": datetime.datetime.now().strftime("%H:%M"),
                "hours": elapsed_hrs, "category": t_cat,
                "description": t_desc or f"Timer session: {t_cat}",
                "platform": "", "communication_with": "", "notes": "", "verified": True,
            })
            st.session_state.timer_running = False
            st.session_state.timer_start = None
            st.success(f"✅ Logged {elapsed_hrs:.2f} hours")
            st.rerun()
    else:
        st.markdown('<div class="timer-display" style="color:#CBD5E1;">00:00:00</div>', unsafe_allow_html=True)
        if st.button("▶️ Start Timer", use_container_width=True, type="primary"):
            st.session_state.timer_running = True
            st.session_state.timer_start = datetime.datetime.now()
            st.session_state.timer_property = t_prop
            st.session_state.timer_category = t_cat
            st.session_state.timer_description = t_desc
            st.rerun()

    st.divider()

    # ── Manual Time Entry ──
    with st.expander("➕ Log Time Manually"):
        with st.form("manual_time"):
            mc1, mc2 = st.columns(2)
            with mc1:
                mt_date = st.date_input("Date", value=date.today(), key="mt_date")
                mt_hours = st.number_input("Hours", 0.0, 24.0, 0.5, 0.25, key="mt_hrs")
                mt_prop = st.selectbox("Property", prop_opts, key="mt_prop")
            with mc2:
                mt_cat = st.selectbox("Category", TIME_CATEGORIES, key="mt_cat")
                mt_platform = st.text_input("Platform/Software Used", placeholder="Airbnb, PriceLabs, Email...", key="mt_plat")
                mt_comm = st.text_input("Communication With", placeholder="Cleaner name, guest name...", key="mt_comm")
            mt_desc = st.text_area("Description (be specific for IRS)", placeholder="Responded to guest Sarah Chen's check-in questions via Airbnb messaging. Coordinated with Maria's Cleaning for turnover schedule.", key="mt_desc")

            if st.form_submit_button("💾 Log Entry", use_container_width=True):
                pid = ""
                if mt_prop != "All Properties":
                    pid = next((p.get("property_id","") for p in st.session_state.properties if (p.get("nickname") or p.get("name",""))==mt_prop), "")
                st.session_state.time_entries.append({
                    "entry_id": generate_id(), "property_id": pid,
                    "date": mt_date.isoformat(), "start_time": "", "end_time": "",
                    "hours": mt_hours, "category": mt_cat,
                    "description": mt_desc or f"{mt_cat} activity",
                    "platform": mt_platform, "communication_with": mt_comm,
                    "notes": "", "verified": True,
                })
                st.success(f"✅ Logged {mt_hours:.2f} hours")
                st.rerun()

    st.divider()

    # ── Material Participation Dashboard ──
    st.markdown("### 📊 Material Participation Dashboard")
    mp = calculate_material_participation(st.session_state.time_entries)

    # 100-Hour Test (Test 3)
    t3_pct = mp["test_3_pct"]
    t3_c = "#10B981" if t3_pct >= 100 else "#F59E0B" if t3_pct >= 60 else "#EF4444"
    t3_status = "✅ TEST MET" if mp["test_3_met"] else f"⏳ Need {mp['test_3_hours_needed']:.1f} more hrs"

    st.markdown(f"""
    <div style="background:white;border-radius:14px;padding:20px;border:2px solid {t3_c};margin:8px 0;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="font-size:.8rem;color:#64748B;text-transform:uppercase;">IRS Test 3: 100+ Hours (Largest Single Participant)</div>
                <div style="font-size:2rem;font-weight:800;color:{t3_c};">{mp['total_hours']:.1f} / 100 hrs</div>
            </div>
            <div style="font-size:1rem;font-weight:700;color:{t3_c};">{t3_status}</div>
        </div>
        <div style="background:#F1F5F9;border-radius:8px;height:12px;margin-top:10px;">
            <div style="background:{t3_c};border-radius:8px;height:12px;width:{min(t3_pct,100)}%;transition:width .3s;"></div>
        </div>
        <div style="display:flex;justify-content:space-between;margin-top:8px;font-size:.8rem;color:#64748B;">
            <span>Pace: {mp['pace_per_week']:.1f} hrs/wk</span>
            <span>Need: {mp['hours_per_week_for_100']:.1f} hrs/wk to hit 100</span>
            <span>Projected: {mp['projected_year_end']:.0f} hrs by Dec 31</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 500-Hour Safe Harbor (Test 1)
    t1_pct = mp["test_1_pct"]
    t1_c = "#10B981" if t1_pct >= 100 else "#3B82F6" if t1_pct >= 30 else "#94A3B8"
    st.markdown(f"""
    <div style="background:#F8FAFC;border-radius:12px;padding:14px;margin:6px 0;">
        <div style="font-size:.75rem;color:#64748B;text-transform:uppercase;">IRS Test 1: 500-Hour Safe Harbor (Real Estate Professional)</div>
        <div style="font-size:1.3rem;font-weight:700;color:{t1_c};">{mp['total_hours']:.1f} / 500 hrs</div>
        <div style="background:#E2E8F0;border-radius:6px;height:8px;margin-top:6px;">
            <div style="background:{t1_c};border-radius:6px;height:8px;width:{min(t1_pct,100)}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Pace info
    st.markdown(f"""
    <div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:10px;padding:12px;margin:8px 0;font-size:.85rem;">
        📅 <strong>{mp['weeks_remaining']:.0f} weeks remaining</strong> in {mp['tax_year']}
        &nbsp;·&nbsp; {mp['days_remaining']} days left
        &nbsp;·&nbsp; Current pace: {mp['pace_per_week']:.1f} hrs/week
    </div>
    """, unsafe_allow_html=True)

    # Hours by category
    if mp["hours_by_category"]:
        st.markdown("#### Hours by Activity")
        for cat, hrs in sorted(mp["hours_by_category"].items(), key=lambda x: -x[1]):
            pct = hrs / max(mp["total_hours"], 1) * 100
            st.progress(pct / 100, text=f"{cat}: {hrs:.1f} hrs ({pct:.0f}%)")

    # Hours by month
    if mp["hours_by_month"]:
        st.markdown("#### Monthly Distribution")
        month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
        for m in range(1, 13):
            hrs = mp["hours_by_month"].get(m, 0)
            if hrs > 0:
                st.progress(hrs / max(mp["total_hours"], 1), text=f"{month_names[m]}: {hrs:.1f} hrs")

    # Recent entries
    st.markdown("#### Recent Time Log")
    recent = sorted(st.session_state.time_entries, key=lambda e: e.get("date",""), reverse=True)[:15]
    for e in recent:
        pn = prop_name(e.get("property_id","")) if e.get("property_id") else "All"
        st.markdown(f"""
        <div class="action-card" style="border-left-color:#8B5CF6;">
            <strong>{e.get('date','')}</strong> · {e.get('hours',0):.2f} hrs · {e.get('category','')}
            <br><span style="color:#64748B;font-size:.85rem;">{pn} · {e.get('description','')[:120]}</span>
            {f'<br><span style="color:#64748B;font-size:.8rem;">Platform: {e.get("platform","")}</span>' if e.get("platform") else ""}
        </div>
        """, unsafe_allow_html=True)
        dc1, dc2 = st.columns([4,1])
        with dc2:
            if st.button("🗑️", key=f"del_te_{e.get('entry_id','')}"):
                st.session_state.time_entries = [t for t in st.session_state.time_entries if t.get("entry_id") != e.get("entry_id")]
                st.rerun()


# ═══════════════════════════════════════════════════════════════════
# PROPERTIES
# ═══════════════════════════════════════════════════════════════════
elif st.session_state.view == "properties":
    st.markdown("## 🏠 Properties")

    with st.expander("➕ Add New Property", expanded=len(st.session_state.properties)==0):
        with st.form("add_prop"):
            st.markdown("**Basic Info**")
            np_name = st.text_input("Property Name *", placeholder="Downtown Loft")
            c1, c2 = st.columns(2)
            with c1:
                np_nick = st.text_input("Nickname", placeholder="Loft")
                np_addr = st.text_input("Street Address")
                np_city = st.text_input("City")
                np_state = st.text_input("State (2-letter)", max_chars=2, placeholder="CA")
            with c2:
                np_zip = st.text_input("ZIP Code")
                np_county = st.text_input("County")
                np_platform = st.selectbox("Primary Platform", PLATFORMS)
                np_type = st.selectbox("Property Type", PROPERTY_TYPES)

            st.markdown("**Property Details**")
            c3, c4 = st.columns(2)
            with c3:
                np_beds = st.number_input("Bedrooms", 0, 10, 1)
                np_baths = st.number_input("Bathrooms", 0.5, 10.0, 1.0, 0.5)
                np_guests = st.number_input("Max Guests", 1, 20, 4)
                np_rate = st.number_input("Base Nightly Rate ($)", 0, 2000, 150)
                np_clean = st.number_input("Cleaning Fee ($)", 0, 500, 75)
            with c4:
                np_min = st.number_input("Min Nights", 1, 30, 2)
                np_checkin = st.text_input("Check-in Time", "3:00 PM")
                np_checkout = st.text_input("Check-out Time", "11:00 AM")
                np_cleaner = st.text_input("Cleaner Name")
                np_crate = st.number_input("Cleaner Rate/Turnover ($)", 0, 500, 75)

            st.markdown("**Guest Info**")
            np_wifi = st.text_input("WiFi Password")
            np_instr = st.text_area("Check-in Instructions")
            np_rules = st.text_area("House Rules")
            np_park = st.text_input("Parking Info")
            np_amen = st.multiselect("Amenities", AMENITIES_OPTIONS)

            st.markdown("**Financial (for Proforma & Tax)**")
            f1, f2 = st.columns(2)
            with f1:
                np_pp = st.number_input("Purchase Price ($)", 0, 10000000, 0, key="np_pp")
                np_dp = st.number_input("Down Payment ($)", 0, 5000000, 0, key="np_dp")
                np_cc = st.number_input("Closing Costs ($)", 0, 200000, 0, key="np_cc")
                np_furn = st.number_input("Furnishing Costs ($)", 0, 200000, 0, key="np_furn")
            with f2:
                np_mort = st.number_input("Monthly Mortgage ($)", 0, 50000, 0, key="np_mort")
                np_ptax = st.number_input("Annual Property Tax ($)", 0, 200000, 0, key="np_ptax")
                np_ins = st.number_input("Annual Insurance ($)", 0, 50000, 0, key="np_ins")
                np_hoa = st.number_input("Monthly HOA ($)", 0, 5000, 0, key="np_hoa")

            st.markdown("**Compliance**")
            lc1, lc2 = st.columns(2)
            with lc1:
                np_permit = st.text_input("STR Permit #")
                np_biz = st.text_input("Business License #")
                np_llc = st.text_input("LLC Name")
            with lc2:
                np_ein = st.text_input("EIN")
                np_tot = st.text_input("TOT/Lodging Tax Registration")
                np_permit_exp = st.date_input("Permit Expiry", value=date.today() + timedelta(days=365), key="np_pexp")

            np_notes = st.text_area("Internal Notes")

            if st.form_submit_button("✅ Add Property", use_container_width=True):
                if np_name:
                    new_p = {
                        "property_id": generate_id(), "name": np_name, "nickname": np_nick,
                        "address": np_addr, "city": np_city, "state": np_state.upper(),
                        "zip_code": np_zip, "county": np_county, "platform": np_platform,
                        "property_type": np_type, "bedrooms": np_beds, "bathrooms": np_baths,
                        "max_guests": np_guests, "base_nightly_rate": float(np_rate),
                        "cleaning_fee": float(np_clean), "min_nights": np_min,
                        "cleaner_name": np_cleaner, "cleaner_phone": "", "cleaner_rate": float(np_crate),
                        "wifi_password": np_wifi, "check_in_time": np_checkin, "check_out_time": np_checkout,
                        "check_in_instructions": np_instr, "house_rules": np_rules,
                        "parking_info": np_park, "amenities": np_amen, "notes": np_notes,
                        "status": "active", "purchase_price": np_pp, "current_value": np_pp,
                        "mortgage_payment": np_mort, "mortgage_balance": 0, "interest_rate": 0,
                        "property_tax_annual": np_ptax, "insurance_annual": np_ins, "hoa_monthly": np_hoa,
                        "down_payment": np_dp, "closing_costs": np_cc, "furnishing_cost": np_furn,
                        "startup_costs": 0, "str_permit_number": np_permit,
                        "str_permit_expiry": np_permit_exp.isoformat(), "business_license": np_biz,
                        "tot_registration": np_tot, "ein": np_ein, "llc_name": np_llc,
                        "created_date": date.today().isoformat(),
                    }
                    st.session_state.properties.append(new_p)
                    st.success(f"✅ Added {np_name}")
                    st.rerun()

    # Property list
    for prop in st.session_state.properties:
        pid = prop.get("property_id","")
        active_bk = [b for b in st.session_state.bookings if b.get("property_id")==pid and b.get("status") in ("confirmed","checked_in")]
        st.markdown(f"""
        <div class="property-card">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <h4 style="margin:0;">🏠 {prop.get('nickname') or prop.get('name','')}</h4>
                {badge(prop.get('status','active').title(), {"active":"#10B981","paused":"#F59E0B","maintenance":"#EF4444"}.get(prop.get('status',''),"#6B7280"))}
            </div>
            <div style="color:#64748B;font-size:.85rem;margin-top:4px;">
                {prop.get('address','')} · {prop.get('city','')} {prop.get('state','')} {prop.get('zip_code','')}
                <br>{prop.get('property_type','')} · {prop.get('bedrooms',0)}BR/{prop.get('bathrooms',0)}BA · ${prop.get('base_nightly_rate',0)}/night · {len(active_bk)} active booking{"s" if len(active_bk)!=1 else ""}
                {f"<br>📜 Permit: {prop.get('str_permit_number','')} · LLC: {prop.get('llc_name','')}" if prop.get('str_permit_number') or prop.get('llc_name') else ""}
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"📋 Details & Financials"):
            dc1, dc2 = st.columns(2)
            with dc1:
                st.markdown(f"**WiFi:** {prop.get('wifi_password','N/A')}")
                st.markdown(f"**Check-in:** {prop.get('check_in_time','')} — {prop.get('check_in_instructions','N/A')[:100]}")
                st.markdown(f"**Parking:** {prop.get('parking_info','N/A')}")
                st.markdown(f"**Cleaner:** {prop.get('cleaner_name','N/A')} · ${prop.get('cleaner_rate',0)}/turnover")
            with dc2:
                st.markdown(f"**Purchase Price:** {format_currency(prop.get('purchase_price',0))}")
                st.markdown(f"**Mortgage:** {format_currency(prop.get('mortgage_payment',0))}/mo")
                st.markdown(f"**Taxes:** {format_currency(prop.get('property_tax_annual',0))}/yr")
                st.markdown(f"**Insurance:** {format_currency(prop.get('insurance_annual',0))}/yr")

            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button("🗑️ Remove", key=f"del_p_{pid}"):
                    st.session_state.properties = [p for p in st.session_state.properties if p.get("property_id")!=pid]
                    st.rerun()
            with bc2:
                if st.button("✅ Compliance", key=f"comp_{pid}"):
                    st.session_state["compliance_property"] = pid
                    nav_to("compliance")


# ═══════════════════════════════════════════════════════════════════
# BOOKINGS
# ═══════════════════════════════════════════════════════════════════
elif st.session_state.view == "bookings":
    st.markdown("## 📅 Bookings")

    with st.expander("➕ Add New Booking"):
        if not st.session_state.properties:
            st.warning("Add a property first.")
        else:
            with st.form("add_bk"):
                po = {(p.get("nickname") or p.get("name","")): p.get("property_id","") for p in st.session_state.properties}
                nb_prop = st.selectbox("Property", list(po.keys()))
                c1, c2 = st.columns(2)
                with c1:
                    nb_g = st.text_input("Guest Name *")
                    nb_ph = st.text_input("Guest Phone")
                    nb_em = st.text_input("Guest Email")
                    nb_ng = st.number_input("Guests", 1, 20, 2)
                with c2:
                    nb_ci = st.date_input("Check-in", value=date.today()+timedelta(days=7))
                    nb_co = st.date_input("Check-out", value=date.today()+timedelta(days=10))
                    nb_plat = st.selectbox("Platform", PLATFORMS, key="nb_pl")
                    pd = get_prop(po.get(nb_prop,""))
                    dr = pd.get("base_nightly_rate",150) if pd else 150
                    nb_rate = st.number_input("Nightly Rate ($)", 0, 2000, int(dr))
                nb_req = st.text_area("Special Requests")

                if st.form_submit_button("✅ Add Booking", use_container_width=True):
                    if nb_g:
                        nn = (nb_co - nb_ci).days
                        cf = pd.get("cleaning_fee",75) if pd else 75
                        payout, pfee = calculate_payout(float(nb_rate), nn, cf)
                        st.session_state.bookings.append({
                            "booking_id": generate_id(), "property_id": po[nb_prop],
                            "guest_name": nb_g, "guest_phone": nb_ph, "guest_email": nb_em,
                            "num_guests": nb_ng, "check_in": nb_ci.isoformat(), "check_out": nb_co.isoformat(),
                            "num_nights": nn, "nightly_rate": float(nb_rate), "cleaning_fee": cf,
                            "total_payout": payout, "platform": nb_plat, "platform_fee": pfee,
                            "status": "confirmed", "special_requests": nb_req, "guest_notes": "",
                            "turnover_status": "pending", "cleaner_confirmed": False, "created_date": date.today().isoformat(),
                        })
                        st.success(f"✅ Added booking for {nb_g}")
                        st.rerun()

    fc1, fc2 = st.columns(2)
    with fc1:
        fs = st.selectbox("Status", ["All","confirmed","checked_in","checked_out","cancelled"])
    with fc2:
        fp = st.selectbox("Property", ["All"] + [p.get("nickname") or p.get("name","") for p in st.session_state.properties])

    bks = st.session_state.bookings[:]
    if fs != "All": bks = [b for b in bks if b.get("status")==fs]
    if fp != "All":
        fpid = next((p.get("property_id","") for p in st.session_state.properties if (p.get("nickname") or p.get("name",""))==fp), "")
        bks = [b for b in bks if b.get("property_id")==fpid]

    for b in sorted(bks, key=lambda x: x.get("check_in",""), reverse=True):
        pn = prop_name(b.get("property_id",""))
        bc = STATUS_COLORS.get(b.get("status",""), "#6B7280")
        st.markdown(f"""
        <div class="booking-card" style="border-left:4px solid {bc};">
            <strong>{b.get('guest_name','')}</strong> {status_badge(b.get('status','confirmed'))}
            <br><span style="color:#64748B;font-size:.85rem;">🏠 {pn} · {b.get('check_in','')} → {b.get('check_out','')} · {b.get('num_nights',0)}n · {format_currency(b.get('total_payout',0))}</span>
            <br>{status_badge(b.get('turnover_status','pending'), TURNOVER_COLORS)} Turnover
            {f'<br><span style="color:#F59E0B;font-size:.85rem;">📝 {b.get("special_requests","")}</span>' if b.get('special_requests') else ''}
        </div>
        """, unsafe_allow_html=True)

        sc = st.columns(4)
        with sc[0]:
            if b.get("status")=="confirmed":
                if st.button("✅ Check In", key=f"ci_{b['booking_id']}", use_container_width=True):
                    b["status"] = "checked_in"; st.rerun()
            elif b.get("status")=="checked_in":
                if st.button("👋 Check Out", key=f"co_{b['booking_id']}", use_container_width=True):
                    b["status"] = "checked_out"; st.rerun()
        with sc[1]:
            if b.get("turnover_status") != "complete":
                ns = {"pending":"scheduled","scheduled":"in_progress","in_progress":"complete"}.get(b.get("turnover_status","pending"),"complete")
                if st.button(f"🧹→{ns[:6]}", key=f"ts_{b['booking_id']}", use_container_width=True):
                    b["turnover_status"] = ns; b["cleaner_confirmed"] = True; st.rerun()
        with sc[2]:
            if st.button("💬 Msg", key=f"m_{b['booking_id']}", use_container_width=True):
                st.session_state["draft_booking_id"] = b["booking_id"]; nav_to("messages")
        with sc[3]:
            if st.button("🗑️", key=f"d_{b['booking_id']}", use_container_width=True):
                st.session_state.bookings = [x for x in st.session_state.bookings if x.get("booking_id")!=b["booking_id"]]; st.rerun()


# ═══════════════════════════════════════════════════════════════════
# iCAL IMPORT
# ═══════════════════════════════════════════════════════════════════
elif st.session_state.view == "ical_import":
    st.markdown("## 📥 iCal Import")
    st.caption("Import bookings from Airbnb, VRBO, or Booking.com calendar feeds.")

    if not st.session_state.properties:
        st.warning("Add a property first, then import its calendar.")
    else:
        st.markdown("### How to Get Your iCal URL")
        with st.expander("📖 Instructions"):
            st.markdown("""
**Airbnb:**
1. Go to your listing → Calendar → Availability Settings
2. Scroll to "Connect calendars"
3. Copy the "Export Calendar" URL

**VRBO:**
1. Go to your listing → Calendar
2. Click "Import/Export"
3. Copy the export URL

**Booking.com:**
1. Go to Property → Calendar
2. Click "Sync calendars"
3. Copy the iCal link

Paste the URL below and click Import. The app will parse all bookings and add them to your property's calendar.
            """)

        st.markdown("---")

        # Property selection
        ical_prop_name = st.selectbox("Property to import into", [p.get("nickname") or p.get("name","") for p in st.session_state.properties], key="ical_prop")
        ical_prop = next((p for p in st.session_state.properties if (p.get("nickname") or p.get("name",""))==ical_prop_name), None)

        if ical_prop:
            pid = ical_prop.get("property_id","")
            ic1, ic2 = st.columns(2)
            with ic1:
                ical_platform = st.selectbox("Platform", ["Airbnb", "VRBO", "Booking.com", "Other"], key="ical_plat")
            with ic2:
                ical_rate = st.number_input("Default Nightly Rate ($)", 0, 2000, int(ical_prop.get("base_nightly_rate", 150)), key="ical_rate",
                                           help="Used for imported bookings where rate isn't in the calendar data")

            st.markdown("---")

            # Method 1: URL fetch
            st.markdown("### Option 1: Import from URL")
            ical_url = st.text_input("iCal URL", placeholder="https://www.airbnb.com/calendar/ical/12345.ics?s=abc123...", key="ical_url")

            if st.button("📥 Import from URL", use_container_width=True, type="primary", disabled=not ical_url):
                with st.spinner("Fetching calendar..."):
                    ical_text = fetch_ical_from_url(ical_url)
                    if ical_text.startswith("ERROR:"):
                        st.error(f"Could not fetch calendar: {ical_text}")
                    elif "VCALENDAR" not in ical_text:
                        st.error("Invalid iCal data. Make sure the URL points to an .ics calendar feed.")
                    else:
                        new_bookings, blocked = parse_ical(
                            ical_text, pid, ical_platform,
                            float(ical_rate), ical_prop.get("cleaning_fee", 75),
                        )
                        unique, dupes = deduplicate_ical_bookings(st.session_state.bookings, new_bookings)
                        st.session_state.bookings.extend(unique)
                        st.success(f"✅ Imported {len(unique)} bookings ({dupes} duplicates skipped, {len(blocked)} blocked dates)")

                        if unique:
                            st.markdown("**Imported bookings:**")
                            for b in unique:
                                st.markdown(f"- **{b['guest_name']}**: {b['check_in']} → {b['check_out']} ({b['num_nights']} nights, {format_currency(b['total_payout'])})")

                        if blocked:
                            with st.expander(f"🚫 {len(blocked)} Blocked Dates"):
                                for bl in blocked:
                                    st.markdown(f"- {bl['start']} → {bl['end']}: {bl['reason']}")

            st.markdown("---")

            # Method 2: Paste iCal text
            st.markdown("### Option 2: Paste iCal Data")
            ical_paste = st.text_area("Paste .ics file contents here", height=150, key="ical_paste",
                                      placeholder="BEGIN:VCALENDAR\nVERSION:2.0\n...")

            if st.button("📋 Import from Paste", use_container_width=True, disabled=not ical_paste):
                if "VCALENDAR" not in ical_paste:
                    st.error("Invalid iCal data. Should start with BEGIN:VCALENDAR")
                else:
                    new_bookings, blocked = parse_ical(
                        ical_paste, pid, ical_platform,
                        float(ical_rate), ical_prop.get("cleaning_fee", 75),
                    )
                    unique, dupes = deduplicate_ical_bookings(st.session_state.bookings, new_bookings)
                    st.session_state.bookings.extend(unique)
                    st.success(f"✅ Imported {len(unique)} bookings ({dupes} duplicates skipped, {len(blocked)} blocked dates)")

                    if unique:
                        st.markdown("**Imported bookings:**")
                        for b in unique:
                            st.markdown(f"- **{b['guest_name']}**: {b['check_in']} → {b['check_out']} ({b['num_nights']} nights)")

            st.markdown("---")

            # Current iCal-imported bookings for this property
            ical_bookings = [b for b in st.session_state.bookings
                            if b.get("property_id") == pid
                            and "ical" in b.get("guest_notes","").lower()]
            if ical_bookings:
                st.markdown(f"### 📅 {len(ical_bookings)} Imported Bookings for {ical_prop_name}")
                for b in sorted(ical_bookings, key=lambda x: x.get("check_in","")):
                    bc = STATUS_COLORS.get(b.get("status",""), "#6B7280")
                    st.markdown(f"""
                    <div class="booking-card" style="border-left:4px solid {bc};">
                        <strong>{b.get('guest_name','')}</strong> {status_badge(b.get('status','confirmed'))}
                        <br><span style="color:#64748B;font-size:.85rem;">{b.get('check_in','')} → {b.get('check_out','')} · {b.get('num_nights',0)}n · {format_currency(b.get('total_payout',0))} · {b.get('platform','')}</span>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")
            st.caption("💡 **Tip:** Airbnb/VRBO calendars update periodically. Re-import to catch new bookings — duplicates are automatically skipped.")


# ═══════════════════════════════════════════════════════════════════
# FINANCES
# ═══════════════════════════════════════════════════════════════════
elif st.session_state.view == "finances":
    st.markdown("## 💰 Finances, Proforma & Tax")

    fin_tab = st.radio("Section", ["Revenue", "Expenses", "Proforma", "Schedule E"], horizontal=True)

    if fin_tab == "Revenue":
        st.markdown("### 📈 Revenue Analytics")
        rc1, rc2 = st.columns(2)
        with rc1: r_start = st.date_input("From", value=date.today().replace(day=1), key="rs")
        with rc2: r_end = st.date_input("To", value=date.today(), key="re")

        if st.session_state.properties:
            port = calculate_portfolio_metrics(st.session_state.bookings, st.session_state.properties, r_start, r_end)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Revenue", format_currency(port["total_revenue"]))
            m2.metric("Net", format_currency(port["net_revenue"]))
            m3.metric("Occupancy", f"{port['avg_occupancy']}%")
            m4.metric("ADR", format_currency(port["avg_nightly_rate"]))

            for prop in st.session_state.properties:
                pid = prop.get("property_id","")
                pm = port["per_property"].get(pid, {})
                pn = prop.get("nickname") or prop.get("name","")
                st.markdown(f"**{pn}:** {format_currency(pm.get('total_revenue',0))} · {pm.get('occupancy_rate',0)}% occ · {pm.get('total_nights_booked',0)} nights")

                gaps = get_gap_nights(st.session_state.bookings, pid, 30)
                if gaps:
                    total_gap = sum(g["nights"] for g in gaps)
                    st.caption(f"📅 {total_gap} vacant nights next 30 days (~{format_currency(total_gap * prop.get('base_nightly_rate',0))} potential)")
        else:
            st.info("Add properties first.")

    elif fin_tab == "Expenses":
        st.markdown("### 💸 Expense Tracking")
        with st.expander("➕ Add Expense"):
            with st.form("add_exp"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    ep = st.selectbox("Property", [p.get("nickname") or p.get("name","") for p in st.session_state.properties] or ["No properties"], key="ep")
                    ecat = st.selectbox("Category", EXPENSE_CATEGORIES, key="ecat")
                    eamt = st.number_input("Amount ($)", 0.0, 999999.0, 0.0, key="eamt")
                with ec2:
                    edate = st.date_input("Date", value=date.today(), key="edate")
                    evend = st.text_input("Vendor", key="evend")
                    etax = st.checkbox("Tax Deductible", value=True, key="etax")
                edesc = st.text_input("Description", key="edesc")
                enotes = st.text_area("Notes / Receipt Reference", placeholder="Receipt uploaded to Docs, receipt #12345...", key="enotes")

                if st.form_submit_button("💾 Add Expense"):
                    pid = next((p.get("property_id","") for p in st.session_state.properties if (p.get("nickname") or p.get("name",""))==ep), "")
                    st.session_state.expenses.append({
                        "expense_id": generate_id(), "property_id": pid,
                        "category": ecat, "description": edesc, "amount": eamt,
                        "date": edate.isoformat(), "vendor": evend, "receipt_doc_id": "",
                        "tax_deductible": etax, "recurring": False, "notes": enotes,
                    })
                    st.success("✅ Expense added")
                    st.rerun()

        # Expense summary
        yr = date.today().year
        yr_exp = [e for e in st.session_state.expenses if _parse_date(e.get("date","")) and _parse_date(e["date"]).year == yr]
        if yr_exp:
            total = sum(e.get("amount",0) for e in yr_exp)
            st.metric(f"{yr} Total Expenses", format_currency(total))
            by_cat = Counter()
            for e in yr_exp: by_cat[e.get("category","Other")] += e.get("amount",0)
            for cat, amt in by_cat.most_common(10):
                st.progress(amt/max(total,1), text=f"{cat}: {format_currency(amt)}")

            st.markdown("#### Recent Expenses")
            for e in sorted(yr_exp, key=lambda x: x.get("date",""), reverse=True)[:20]:
                vendor_str = f" · {e.get('vendor','')}" if e.get("vendor") else ""
                st.markdown(f'<div class="action-card" style="border-left-color:#F59E0B;"><strong>{e.get("date","")}</strong> · {e.get("category","")} · {format_currency(e.get("amount",0))}<br><span style="color:#64748B;font-size:.85rem;">{e.get("description","")}{vendor_str}</span></div>', unsafe_allow_html=True)

    elif fin_tab == "Proforma":
        st.markdown("### 📊 Investment Proforma")
        if not st.session_state.properties:
            st.info("Add a property with financial details first.")
        else:
            pf_prop_name = st.selectbox("Property", [p.get("nickname") or p.get("name","") for p in st.session_state.properties], key="pf_p")
            pf_prop = next((p for p in st.session_state.properties if (p.get("nickname") or p.get("name",""))==pf_prop_name), None)
            if pf_prop:
                pc1, pc2 = st.columns(2)
                with pc1:
                    pf_rev = st.number_input("Projected Annual Revenue ($)", 0, 500000, 45000, key="pf_rev")
                    pf_vac = st.slider("Vacancy Rate (%)", 0, 50, 25, key="pf_vac")
                with pc2:
                    pf_clean = st.number_input("Annual Cleaning ($)", 0, 50000, 3600, key="pf_cl")
                    pf_maint = st.number_input("Annual Maintenance ($)", 0, 50000, 2400, key="pf_mx")
                    pf_util = st.number_input("Annual Utilities ($)", 0, 50000, 3600, key="pf_ut")
                    pf_sup = st.number_input("Annual Supplies ($)", 0, 50000, 1200, key="pf_su")

                exp_dict = {"Cleaning": pf_clean, "Maintenance": pf_maint, "Utilities": pf_util, "Supplies": pf_sup}
                pf = calculate_proforma(pf_prop, pf_rev, exp_dict, pf_vac/100)

                st.markdown("---")
                st.markdown("#### Investment Returns")
                r1, r2, r3 = st.columns(3)
                coc_c = "#10B981" if pf["cash_on_cash"] > 8 else "#F59E0B" if pf["cash_on_cash"] > 0 else "#EF4444"
                r1.markdown(f'<div class="stat-card"><div class="metric-label">Cash-on-Cash</div><div style="font-size:2rem;font-weight:800;color:{coc_c};">{pf["cash_on_cash"]}%</div></div>', unsafe_allow_html=True)
                r2.markdown(f'<div class="stat-card"><div class="metric-label">Cap Rate</div><div style="font-size:2rem;font-weight:800;">{pf["cap_rate"]}%</div></div>', unsafe_allow_html=True)
                r3.markdown(f'<div class="stat-card"><div class="metric-label">Monthly Cash Flow</div><div style="font-size:2rem;font-weight:800;">{format_currency(pf["monthly_cash_flow"])}</div></div>', unsafe_allow_html=True)

                st.markdown("#### Pro Forma Breakdown")
                st.markdown(f"""
                | Line | Amount |
                |------|--------|
                | Gross Revenue | {format_currency(pf['gross_revenue'])} |
                | - Vacancy ({pf_vac}%) | ({format_currency(pf['vacancy_loss'])}) |
                | **Effective Gross** | **{format_currency(pf['effective_gross'])}** |
                | - Operating Expenses | ({format_currency(pf['total_opex'])}) |
                | **NOI** | **{format_currency(pf['noi'])}** |
                | - Debt Service | ({format_currency(pf['annual_debt_service'])}) |
                | **Annual Cash Flow** | **{format_currency(pf['annual_cash_flow'])}** |
                | Total Investment | {format_currency(pf['total_investment'])} |
                | DSCR | {pf['dscr']}x |
                | Gross Yield | {pf['gross_yield']}% |
                | Expense Ratio | {pf['expense_ratio']}% |
                | Break-Even Occupancy | {pf['break_even_occ']}% |
                """)

    elif fin_tab == "Schedule E":
        st.markdown("### 📋 Schedule E Preparation")
        if not st.session_state.properties:
            st.info("Add properties first.")
        else:
            se_yr = st.number_input("Tax Year", 2020, 2030, date.today().year, key="se_yr")
            for prop in st.session_state.properties:
                sc = generate_schedule_e_summary(prop, st.session_state.bookings, st.session_state.expenses, se_yr)
                pn = prop.get("nickname") or prop.get("name","")
                st.markdown(f"#### 🏠 {pn}")
                st.markdown(f"**Address:** {sc.get('property_address','')}")
                st.markdown(f"**Fair Rental Days:** {sc.get('fair_rental_days',0)}")

                st.markdown(f"""
                | Schedule E Line | Amount |
                |----------------|--------|
                | Line 3 - Rents | {format_currency(sc['line_3_rents'])} |
                | Line 5 - Advertising | {format_currency(sc['line_5_advertising'])} |
                | Line 6 - Auto/Travel | {format_currency(sc['line_6_auto'])} |
                | Line 7 - Cleaning | {format_currency(sc['line_7_cleaning'])} |
                | Line 8 - Commissions | {format_currency(sc['line_8_commissions'])} |
                | Line 9 - Insurance | {format_currency(sc['line_9_insurance'])} |
                | Line 10 - Legal/Prof | {format_currency(sc['line_10_legal'])} |
                | Line 12 - Mortgage Int | {format_currency(sc['line_12_mortgage_int'])} |
                | Line 14 - Repairs | {format_currency(sc['line_14_repairs'])} |
                | Line 15 - Supplies | {format_currency(sc['line_15_supplies'])} |
                | Line 16 - Taxes | {format_currency(sc['line_16_taxes'])} |
                | Line 17 - Utilities | {format_currency(sc['line_17_utilities'])} |
                | Line 18 - Depreciation | {format_currency(sc['line_18_depreciation'])} |
                | Line 19 - Other | {format_currency(sc['line_19_other'])} |
                | **Total Expenses** | **{format_currency(sc['total_expenses'])}** |
                | **Net Income** | **{format_currency(sc['net_income'])}** |
                """)
                st.divider()


# ═══════════════════════════════════════════════════════════════════
# MESSAGES
# ═══════════════════════════════════════════════════════════════════
elif st.session_state.view == "messages":
    st.markdown("## 💬 Guest Messages")

    mc1, mc2 = st.columns(2)
    with mc1:
        tmpl_opts = {v["label"]: k for k, v in MESSAGE_TEMPLATES.items()}
        sel_label = st.selectbox("Template", list(tmpl_opts.keys()))
        sel_tmpl = tmpl_opts[sel_label]
    with mc2:
        active_bk = [b for b in st.session_state.bookings if b.get("status") != "cancelled"]
        bk_labels = {f"{b.get('guest_name','')} — {prop_name(b.get('property_id',''))}": b for b in active_bk}
        sel_bk_label = st.selectbox("Guest", list(bk_labels.keys()) or ["No bookings"])

    if bk_labels and sel_bk_label in bk_labels:
        bk = bk_labels[sel_bk_label]
        prop = get_prop(bk.get("property_id",""))
        if st.button("📝 Generate Message", use_container_width=True, type="primary"):
            st.session_state["draft_message"] = fill_template(sel_tmpl, prop, bk)
            st.session_state["draft_guest"] = bk.get("guest_name","")

    draft = st.session_state.get("draft_message","")
    if draft:
        st.markdown(f"**To: {st.session_state.get('draft_guest','Guest')}**")
        edited = st.text_area("Edit before sending:", value=draft, height=250, key="msg_ed")
        mc1, mc2 = st.columns(2)
        with mc1:
            if st.button("📋 Copy", use_container_width=True):
                st.code(edited, language=None)
        with mc2:
            if st.button("🤖 Improve w/ AI", use_container_width=True):
                if AI_AVAILABLE:
                    st.session_state.ai_messages.append({"role":"user","content":f"Improve this guest message. Keep it warm and professional:\n\n{edited}"})
                    nav_to("ai_chat")

    if "draft_booking_id" in st.session_state:
        del st.session_state["draft_booking_id"]


# ═══════════════════════════════════════════════════════════════════
# CONTACTS
# ═══════════════════════════════════════════════════════════════════
elif st.session_state.view == "contacts":
    st.markdown("## 📇 Team & Contacts")

    with st.expander("➕ Add Contact"):
        with st.form("add_contact"):
            cc1, cc2 = st.columns(2)
            with cc1:
                cn = st.text_input("Name *", key="cn")
                cr = st.selectbox("Role", CONTACT_ROLES, key="cr")
                cco = st.text_input("Company", key="cco")
            with cc2:
                cph = st.text_input("Phone", key="cph")
                cem = st.text_input("Email", key="cem")
                crt = st.text_input("Rate/Fee", placeholder="$85/turnover, $50/hr...", key="crt")
            cadr = st.text_input("Address", key="cadr")
            cnotes = st.text_area("Notes", key="cnotes")
            cprop = st.multiselect("Associated Properties", [p.get("nickname") or p.get("name","") for p in st.session_state.properties], key="cprop")

            if st.form_submit_button("✅ Add Contact"):
                if cn:
                    pids = [p.get("property_id","") for p in st.session_state.properties if (p.get("nickname") or p.get("name","")) in cprop]
                    st.session_state.contacts.append({
                        "contact_id": generate_id(), "name": cn, "role": cr,
                        "company": cco, "phone": cph, "email": cem, "address": cadr,
                        "property_ids": pids, "rate": crt, "notes": cnotes,
                        "created_date": date.today().isoformat(),
                    })
                    st.success(f"✅ Added {cn}")
                    st.rerun()

    # Contact directory grouped by role
    by_role = {}
    for c in st.session_state.contacts:
        by_role.setdefault(c.get("role","Other"), []).append(c)

    for role in sorted(by_role.keys()):
        st.markdown(f"**{role}**")
        for c in by_role[role]:
            props_str = ", ".join(prop_name(pid) for pid in c.get("property_ids",[])) or "All"
            st.markdown(f"""
            <div class="action-card">
                <strong>{c.get('name','')}</strong> {f"· {c.get('company','')}" if c.get('company') else ""}
                <br><span style="color:#64748B;font-size:.85rem;">📞 {c.get('phone','N/A')} · ✉️ {c.get('email','N/A')} {f"· 💵 {c.get('rate','')}" if c.get('rate') else ""}</span>
                <br><span style="color:#64748B;font-size:.8rem;">Properties: {props_str}</span>
                {f'<br><span style="color:#64748B;font-size:.8rem;">{c.get("notes","")[:100]}</span>' if c.get("notes") else ""}
            </div>
            """, unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_c_{c.get('contact_id','')}"):
                st.session_state.contacts = [x for x in st.session_state.contacts if x.get("contact_id")!=c.get("contact_id")]
                st.rerun()

    if not st.session_state.contacts:
        st.info("No contacts yet. Add your cleaners, handyman, CPA, and other team members.")


# ═══════════════════════════════════════════════════════════════════
# COMPLIANCE
# ═══════════════════════════════════════════════════════════════════
elif st.session_state.view == "compliance":
    st.markdown("## ✅ Compliance Checklists")
    st.caption("Federal, state, and local requirements for STR operations. Check items as you complete them.")

    if not st.session_state.properties:
        st.info("Add a property with city/state to generate compliance checklists.")
    else:
        comp_prop_name = st.selectbox("Property", [p.get("nickname") or p.get("name","") for p in st.session_state.properties], key="comp_p")
        comp_prop = next((p for p in st.session_state.properties if (p.get("nickname") or p.get("name",""))==comp_prop_name), None)

        if comp_prop:
            state = comp_prop.get("state","")
            city = comp_prop.get("city","")

            if not state:
                st.warning("Enter a state code on the property to generate state-specific requirements.")
                state = "CA"  # fallback

            checklist = get_compliance_checklist(state, city)
            checks_key = comp_prop.get("property_id","")

            if checks_key not in st.session_state.compliance_checks:
                st.session_state.compliance_checks[checks_key] = {}

            # Stats
            total = len(checklist)
            completed = sum(1 for item in checklist if st.session_state.compliance_checks[checks_key].get(item["item"], False))
            req_items = [i for i in checklist if i.get("required")]
            req_complete = sum(1 for i in req_items if st.session_state.compliance_checks[checks_key].get(i["item"], False))
            pct = completed / max(total, 1) * 100

            comp_c = "#10B981" if pct >= 80 else "#F59E0B" if pct >= 50 else "#EF4444"
            st.markdown(f"""
            <div style="background:white;border-radius:12px;padding:16px;border-left:4px solid {comp_c};margin:8px 0;">
                <div style="font-size:1.3rem;font-weight:700;color:{comp_c};">{completed}/{total} Complete ({pct:.0f}%)</div>
                <div style="color:#64748B;font-size:.85rem;">Required items: {req_complete}/{len(req_items)}</div>
                <div style="background:#F1F5F9;border-radius:6px;height:10px;margin-top:8px;">
                    <div style="background:{comp_c};border-radius:6px;height:10px;width:{pct}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Group by level
            levels = {}
            for item in checklist:
                levels.setdefault(item.get("level","Other"), []).append(item)

            for level, items in levels.items():
                st.markdown(f"### {level}")
                for item in items:
                    req_class = "compliance-required" if item.get("required") else ""
                    req_tag = "🔴 REQUIRED" if item.get("required") else "🟡 Recommended"
                    checked = st.session_state.compliance_checks[checks_key].get(item["item"], False)

                    col1, col2 = st.columns([1, 8])
                    with col1:
                        new_val = st.checkbox("", value=checked, key=f"comp_{checks_key}_{item['item']}", label_visibility="collapsed")
                        if new_val != checked:
                            st.session_state.compliance_checks[checks_key][item["item"]] = new_val
                            st.rerun()
                    with col2:
                        strike = "text-decoration:line-through;opacity:.5;" if checked else ""
                        st.markdown(f"""
                        <div class="compliance-item {req_class}" style="{strike}">
                            <strong>{item['item']}</strong> <span style="font-size:.7rem;color:#64748B;">{req_tag}</span>
                            <br><span style="color:#64748B;font-size:.85rem;">{item['description']}</span>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown("---")
            st.caption("⚠️ This checklist is for guidance only and may not be exhaustive. Consult a local attorney or CPA for complete compliance requirements. Regulations change frequently — verify current requirements with your local jurisdiction.")


# ═══════════════════════════════════════════════════════════════════
# DOCUMENTS / RECEIPT VAULT
# ═══════════════════════════════════════════════════════════════════
elif st.session_state.view == "documents":
    st.markdown("## 📎 Documents & Receipt Vault")
    st.caption("Log receipts, photos, permits, and other documents for audit readiness.")

    with st.expander("➕ Add Document / Receipt"):
        with st.form("add_doc"):
            dc1, dc2 = st.columns(2)
            with dc1:
                dd_type = st.selectbox("Document Type", DOCUMENT_TYPES, key="dd_type")
                dd_title = st.text_input("Title *", placeholder="Home Depot receipt - new towels", key="dd_title")
                dd_prop = st.selectbox("Property", ["All"] + [p.get("nickname") or p.get("name","") for p in st.session_state.properties], key="dd_prop")
                dd_cat = st.selectbox("Expense Category", ["N/A"] + EXPENSE_CATEGORIES, key="dd_cat")
            with dc2:
                dd_date = st.date_input("Date", value=date.today(), key="dd_date")
                dd_amt = st.number_input("Amount ($)", 0.0, 999999.0, 0.0, key="dd_amt")
                dd_vend = st.text_input("Vendor", key="dd_vend")
                dd_yr = st.number_input("Tax Year", 2020, 2030, date.today().year, key="dd_yr")
            dd_desc = st.text_area("Description / Notes", placeholder="Include receipt number, what was purchased, reference to uploaded file...", key="dd_desc")
            dd_file = st.text_input("Filename / Reference", placeholder="receipt_2026_0215_homedepot.jpg (upload to Google Drive)", key="dd_file")

            if st.form_submit_button("💾 Add Document"):
                if dd_title:
                    pid = ""
                    if dd_prop != "All":
                        pid = next((p.get("property_id","") for p in st.session_state.properties if (p.get("nickname") or p.get("name",""))==dd_prop), "")
                    st.session_state.documents.append({
                        "doc_id": generate_id(), "property_id": pid,
                        "doc_type": dd_type, "title": dd_title, "description": dd_desc,
                        "filename": dd_file, "file_data": "", "category": dd_cat if dd_cat != "N/A" else "",
                        "amount": dd_amt, "date": dd_date.isoformat(), "vendor": dd_vend,
                        "tax_year": dd_yr, "notes": "",
                    })
                    st.success(f"✅ Added: {dd_title}")
                    st.rerun()

    # Filter
    df_type = st.selectbox("Filter by Type", ["All"] + DOCUMENT_TYPES, key="df_type")
    docs = st.session_state.documents[:]
    if df_type != "All":
        docs = [d for d in docs if d.get("doc_type") == df_type]

    # Stats
    if docs:
        total_receipts = len([d for d in docs if d.get("doc_type")=="Receipt"])
        total_amt = sum(d.get("amount",0) for d in docs if d.get("amount"))
        st.markdown(f"**{len(docs)} documents** · {total_receipts} receipts · {format_currency(total_amt)} total value")

    for d in sorted(docs, key=lambda x: x.get("date",""), reverse=True):
        pn = prop_name(d.get("property_id","")) if d.get("property_id") else "All"
        amt_str = format_currency(d.get("amount",0)) if d.get("amount") else ""
        st.markdown(f"""
        <div class="action-card">
            <strong>{d.get('title','')}</strong> {badge(d.get('doc_type',''), '#8B5CF6')}
            <br><span style="color:#64748B;font-size:.85rem;">{d.get('date','')} · {pn} {f"· {amt_str}" if amt_str else ""} {f"· {d.get('vendor','')}" if d.get('vendor') else ""}</span>
            {f'<br><span style="color:#64748B;font-size:.8rem;">{d.get("description","")[:150]}</span>' if d.get("description") else ""}
            {f'<br><span style="color:#3B82F6;font-size:.8rem;">📁 {d.get("filename","")}</span>' if d.get("filename") else ""}
        </div>
        """, unsafe_allow_html=True)
        if st.button("🗑️", key=f"del_doc_{d.get('doc_id','')}"):
            st.session_state.documents = [x for x in st.session_state.documents if x.get("doc_id")!=d.get("doc_id")]
            st.rerun()

    if not docs:
        st.info("No documents yet. Log receipts, photos, and permits here for audit readiness.")

    st.divider()

    # Audit PDF Export
    st.markdown("### 📄 Generate Audit PDF")
    st.caption("Comprehensive PDF with all properties, revenue, expenses, time log, Schedule E, material participation analysis, and document inventory.")

    pdf_yr = st.number_input("Tax Year for Report", 2020, 2030, date.today().year, key="pdf_yr")
    if st.button("📄 Generate Audit PDF", use_container_width=True, type="primary"):
        try:
            pdf_bytes = generate_audit_pdf(
                st.session_state.properties, st.session_state.bookings,
                st.session_state.expenses, st.session_state.time_entries,
                st.session_state.documents, st.session_state.contacts,
                st.session_state.maintenance, pdf_yr,
            )
            b64 = base64.b64encode(pdf_bytes).decode()
            fname = f"HostFlow_Audit_Report_{pdf_yr}.pdf"
            st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="{fname}" style="display:inline-block;background:#2563EB;color:white;padding:12px 24px;border-radius:10px;text-decoration:none;font-weight:700;margin-top:8px;">⬇️ Download Audit PDF</a>', unsafe_allow_html=True)
            st.success(f"✅ Audit report generated: {len(pdf_bytes):,} bytes")
        except Exception as e:
            st.error(f"PDF generation error: {e}. Ensure fpdf2 is installed.")


# ═══════════════════════════════════════════════════════════════════
# AI ASSISTANT
# ═══════════════════════════════════════════════════════════════════
elif st.session_state.view == "ai_chat":
    st.markdown("## 🤖 AI Assistant")

    if not AI_AVAILABLE:
        st.warning("Add `anthropic_api_key` to Streamlit secrets.")
    else:
        qa1, qa2, qa3, qa4 = st.columns(4)
        with qa1:
            if st.button("📊 Portfolio", use_container_width=True):
                st.session_state.ai_messages.append({"role":"user","content":"Analyze my portfolio — revenue, occupancy, pricing gaps, quick wins?"}); st.rerun()
        with qa2:
            if st.button("💰 Tax Tips", use_container_width=True):
                st.session_state.ai_messages.append({"role":"user","content":"Review my material participation status and suggest tax optimization strategies."}); st.rerun()
        with qa3:
            if st.button("📋 Audit Ready?", use_container_width=True):
                st.session_state.ai_messages.append({"role":"user","content":"Am I audit-ready? What documentation gaps should I fill?"}); st.rerun()
        with qa4:
            if st.button("💬 Draft Msg", use_container_width=True):
                st.session_state.ai_messages.append({"role":"user","content":"Help me draft a message for my next guest."}); st.rerun()

        st.markdown("---")
        for msg in st.session_state.ai_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if st.session_state.ai_messages and st.session_state.ai_messages[-1]["role"] == "user":
            with st.chat_message("assistant"):
                with st.spinner("🤖"):
                    resp = call_ai(st.session_state.ai_messages)
                    st.markdown(resp)
                    st.session_state.ai_messages.append({"role":"assistant","content":resp})

        user_in = st.chat_input("Ask about properties, taxes, pricing, compliance...")
        if user_in:
            st.session_state.ai_messages.append({"role":"user","content":user_in}); st.rerun()
