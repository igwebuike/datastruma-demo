import base64
import hashlib
import io
import json
import os
import urllib.error
import urllib.request
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html, no_update, dash_table, ctx, ALL

COLORS = {
    "bg": "#071120",
    "panel": "#0D1A2B",
    "panel2": "#12213A",
    "text": "#F4F7FB",
    "muted": "#93A8C6",
    "accent": "#53C7FF",
    "accent2": "#7B8CFF",
    "accent3": "#78F0A7",
    "warn": "#FFB454",
    "danger": "#FF7A90",
}

logo_svg = """
<svg width="240" height="52" viewBox="0 0 240 52" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect x="1" y="1" width="48" height="48" rx="14" fill="#0E1628" stroke="#2B466E"/>
  <circle cx="25" cy="25" r="12" fill="#EAF7FF"/>
  <path d="M19 25h12" stroke="#6CCBFF" stroke-width="3" stroke-linecap="round"/>
  <path d="M25 19v12" stroke="#8CFFB8" stroke-width="3" stroke-linecap="round"/>
  <text x="64" y="22" fill="#F5F7FB" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="700">Datastruma</text>
  <text x="64" y="40" fill="#8FA8C9" font-family="Inter, Arial, sans-serif" font-size="11" font-weight="500">Operations Demo</text>
</svg>
"""
LOGO_SRC = "data:image/svg+xml;base64," + base64.b64encode(logo_svg.encode()).decode()

# ---------------- Main demo data ----------------
INDUSTRIES = {
    "home_services": {
        "label": "Home Services",
        "headline": "See where dispatch chaos builds — and what better looks like.",
        "subheadline": "A realistic business demo for companies handling service calls, technician dispatch, onboarding, billing cleanup, and office coordination.",
        "clients": ["UrbanFix HVAC", "BluePeak Plumbing", "Metro Electric", "EverFlow Services", "RapidHome Repairs"],
        "metric_names": {"backlog": "Jobs still waiting", "onboarding": "Technician setup delay", "billing": "Daily missed billing", "manual": "Dispatch and office admin time", "response": "Average scheduling response time"},
        "units": {"backlog": "", "onboarding": " hrs", "billing": "$", "manual": " min", "response": " min"},
        "meanings": {
            "backlog": "how many jobs are still waiting because work is coming in faster than it is being scheduled or completed.",
            "onboarding": "how long it takes to fully set up a new technician with systems, schedules, tools, and permissions.",
            "billing": "money lost when trip fees, add-on work, or changes in scope do not get captured properly.",
            "manual": "time spent manually dispatching, calling, rescheduling, updating customers, and correcting paperwork.",
            "response": "how long it takes before the office gets back to the customer with a real scheduling update.",
        },
        "chaos_story": "Calls were being rescheduled too often, route changes were handled manually, office staff were chasing technicians for updates, and billing details were often fixed after the fact.",
        "owner_impact": "When this improves, jobs move faster, dispatch becomes calmer, customers get clearer updates, and fewer dollars are missed.",
        "base": {"backlog": 430, "onboarding": 12.5, "billing": 273, "manual": 218, "response": 45},
        "resolved": {"backlog": 210, "onboarding": 6.8, "billing": 110, "manual": 119, "response": 30},
        "chart_title": "Dispatch and field operations trend",
    },
    "healthcare": {
        "label": "Healthcare",
        "headline": "See where admin bottlenecks build — and what better looks like.",
        "subheadline": "A realistic business demo for clinics and healthcare operators dealing with intake backlog, staff onboarding delays, billing leakage, and manual coordination.",
        "clients": ["PrimeCare Clinic", "Summit Therapy", "Harbor Family Health", "WellSpring Urgent Care", "BlueOak Diagnostics"],
        "metric_names": {"backlog": "Patient requests still waiting", "onboarding": "Staff onboarding delay", "billing": "Daily missed revenue", "manual": "Manual coordination time", "response": "Average patient response time"},
        "units": {"backlog": "", "onboarding": " hrs", "billing": "$", "manual": " min", "response": " min"},
        "meanings": {
            "backlog": "how many patient-related requests are still waiting to be handled.",
            "onboarding": "how long it takes to fully set up a new staff member across systems and processes.",
            "billing": "revenue lost when charge capture, coding follow-up, or process handoffs break down.",
            "manual": "time staff spend chasing information, updating status, and coordinating across teams.",
            "response": "how long patients wait before the clinic responds clearly.",
        },
        "chaos_story": "Requests were bouncing between teams, handoffs were slow, new staff setup was inconsistent, and revenue capture depended too much on manual follow-up.",
        "owner_impact": "When this improves, patients feel better service, teams lose less time, and fewer dollars get trapped in broken processes.",
        "base": {"backlog": 380, "onboarding": 14.2, "billing": 365, "manual": 242, "response": 38},
        "resolved": {"backlog": 170, "onboarding": 7.1, "billing": 145, "manual": 128, "response": 22},
        "chart_title": "Clinic operations trend",
    },
    "logistics": {
        "label": "Logistics",
        "headline": "See where logistics operations get overloaded — and what better looks like.",
        "subheadline": "A realistic business demo for logistics operators dealing with shipment backlog, team onboarding delays, revenue leakage, and dispatch/admin overload.",
        "clients": ["DesertLink Logistics", "Gulf Trade Movers", "HarborCross Freight", "Atlas Route Systems", "Falcon Cargo Services"],
        "metric_names": {"backlog": "Shipments still waiting", "onboarding": "New staff setup delay", "billing": "Daily missed revenue", "manual": "Dispatch and admin time", "response": "Average customer update time"},
        "units": {"backlog": "", "onboarding": " hrs", "billing": "$", "manual": " min", "response": " min"},
        "meanings": {
            "backlog": "how many shipments, jobs, or exceptions are still waiting to be processed or cleared.",
            "onboarding": "how long it takes to fully set up a new coordinator, warehouse staff member, or operations user.",
            "billing": "revenue missed when storage, handling, route changes, surcharges, or accessorials are not billed cleanly.",
            "manual": "time spent dispatching, correcting manifests, chasing proof of delivery, updating customers, and reconciling exceptions.",
            "response": "how long it takes before a customer gets a reliable status update.",
        },
        "chaos_story": "Shipment exceptions were piling up, updates were being chased manually, proof-of-delivery and surcharge details were not always flowing cleanly into billing, and operations staff were spending too much time fixing status issues by hand.",
        "owner_impact": "When this improves, fewer shipments sit in limbo, customers get clearer updates, teams spend less time firefighting, and less revenue slips away.",
        "base": {"backlog": 620, "onboarding": 16.2, "billing": 640, "manual": 312, "response": 54},
        "resolved": {"backlog": 285, "onboarding": 8.4, "billing": 245, "manual": 158, "response": 28},
        "chart_title": "Logistics operations trend",
    },
}

# ---------------- Rock of Ages client workspace ----------------
ROCK_CLIENT = {
    "client_name": "Rock of Ages Group",
    "hero_title": "Logistics operations, customer support, invoicing, and document processing in one connected workspace.",
    "hero_subtitle": "A Datastruma client workspace tailored for Rock of Ages Group to handle shipment estimates, invoice creation, shipment status updates, missing-goods follow-up, uploaded logistics documents, and AI-assisted support.",
    "summary": "Rock of Ages Group handles freight coordination, customer support, invoice processing, customs and delivery follow-up, and issue handling across a growing logistics operation.",
}
ROCK_SAVED_CUSTOMERS = [
    {"label": "Queen Esther Trading LLC", "value": "Queen Esther Trading LLC", "email": "operations@queenesthertrading.com"},
    {"label": "Blue Pearl General Trading", "value": "Blue Pearl General Trading", "email": "ops@bluepearltrade.com"},
    {"label": "Al Noor Fashion Hub", "value": "Al Noor Fashion Hub", "email": "support@alnoorfashion.ae"},
    {"label": "Noble Market Supplies", "value": "Noble Market Supplies", "email": "purchasing@noblemarket.com"},
]
ROCK_DESTINATIONS = {
    "Dubai": {"rate_per_kg": 10.50, "base_shipping": 105, "handling": 15, "vat_rate": 0.05, "eta": "1-2 days"},
    "Lagos": {"rate_per_kg": 15.00, "base_shipping": 160, "handling": 25, "vat_rate": 0.05, "eta": "4-6 days"},
    "Abuja": {"rate_per_kg": 15.50, "base_shipping": 170, "handling": 25, "vat_rate": 0.05, "eta": "4-6 days"},
    "Port Harcourt": {"rate_per_kg": 16.00, "base_shipping": 180, "handling": 28, "vat_rate": 0.05, "eta": "5-7 days"},
    "Accra": {"rate_per_kg": 13.00, "base_shipping": 140, "handling": 20, "vat_rate": 0.05, "eta": "3-5 days"},
}
ROCK_GOODS_MULTIPLIERS = {
    "Fashion Items": 1.00,
    "Electronics": 1.18,
    "Documents": 0.72,
    "Household Goods": 1.05,
    "Mixed Commercial Goods": 1.12,
    "Heavy Equipment Parts": 1.28,
}
ROCK_TRACKING_ROWS = [
    {"shipment_id": "ROA-24019", "customer": "Queen Esther Trading LLC", "status": "In transit", "origin": "Dubai", "destination": "Lagos", "eta": "2026-04-27", "issue": "None"},
    {"shipment_id": "ROA-24020", "customer": "Blue Pearl General Trading", "status": "Customs review", "origin": "Dubai", "destination": "Abuja", "eta": "2026-04-29", "issue": "Awaiting customs release"},
    {"shipment_id": "ROA-24021", "customer": "Al Noor Fashion Hub", "status": "In warehouse", "origin": "Dubai", "destination": "Port Harcourt", "eta": "2026-05-01", "issue": "Pending manifest confirmation"},
    {"shipment_id": "ROA-24022", "customer": "Noble Market Supplies", "status": "Delivered", "origin": "Dubai", "destination": "Accra", "eta": "2026-04-22", "issue": "Closed"},
]
ROCK_ISSUE_ROWS = [
    {"case_id": "MG-1041", "shipment_id": "ROA-24020", "customer": "Blue Pearl General Trading", "issue": "2 cartons missing", "status": "Investigating", "owner": "Fatima", "priority": "High", "last_update": "Container checked. Supplier follow-up in progress.", "customer_message": "We have confirmed the missing cartons issue and our team is checking the last verified handoff. Next update within 24 hours."},
    {"case_id": "MG-1042", "shipment_id": "ROA-24021", "customer": "Al Noor Fashion Hub", "issue": "Damaged package", "status": "Customer updated", "owner": "David", "priority": "Medium", "last_update": "Images received and replacement discussion started.", "customer_message": "We received the package images and are reviewing replacement options. We will confirm the next step shortly."},
]
ROCK_SCENARIOS = {
    "Standard Operations": {"shipments": 148, "issues": 2, "customers_saved": 4, "documents": 18, "badge": "Standard flow"},
    "High Shipment Volume": {"shipments": 226, "issues": 7, "customers_saved": 4, "documents": 31, "badge": "Peak volume"},
    "Delayed Shipments": {"shipments": 151, "issues": 11, "customers_saved": 4, "documents": 20, "badge": "Delay pressure"},
    "Invoice Leakage": {"shipments": 141, "issues": 4, "customers_saved": 4, "documents": 17, "badge": "Margin cleanup"},
    "Missing Goods Escalation": {"shipments": 136, "issues": 15, "customers_saved": 4, "documents": 26, "badge": "Issue surge"},
}
ROCK_MODULES = [
    ("shipping", "Shipping Calculator", "Create fast, customer-ready estimates."),
    ("invoice", "Invoice Generator", "Generate a clean invoice breakdown."),
    ("tracking", "Shipment Tracking", "View shipment status and blockers."),
    ("missing", "Missing Goods", "Handle claims and customer updates cleanly."),
    ("documents", "Document Upload", "Upload and summarize logistics docs."),
    ("assistant", "AI Assistant", "Use Gemini to draft and explain."),
    ("scenario", "Scenario Builder", "Show alternate operating conditions."),
]

# ---------------- Utilities ----------------
def stable_seed(*parts):
    key = "|".join(str(p) for p in parts)
    return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)

def gemini_key():
    for k in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
        v = os.getenv(k)
        if v:
            return v.strip()
    j = os.getenv("GEMINI_API_KEY_JSON") or os.getenv("GOOGLE_API_KEY_JSON")
    if j:
        try:
            d = json.loads(j)
            for k in ["api_key", "key", "GEMINI_API_KEY", "GOOGLE_API_KEY"]:
                if d.get(k):
                    return str(d[k]).strip()
        except Exception:
            pass
    return None

def gemini_enabled():
    return bool(gemini_key())

def call_gemini(prompt, system_instruction=""):
    key = gemini_key()
    if not key:
        return "Gemini is not configured yet. Add GEMINI_API_KEY or GOOGLE_API_KEY in Render to enable live responses."
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    body = {
        "contents": [{"parts": ([{"text": system_instruction}] if system_instruction else []) + [{"text": prompt}]}]
    }
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        cand = payload.get("candidates", [])
        if not cand:
            return "No response returned from Gemini."
        parts = cand[0].get("content", {}).get("parts", [])
        text = "\n".join([p.get("text", "") for p in parts if p.get("text")]).strip()
        return text or "Gemini returned an empty response."
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8")
        except Exception:
            detail = str(e)
        return f"Gemini request failed: {detail}"
    except Exception as e:
        return f"Gemini request failed: {e}"

def current_stage(alpha):
    return "Messy" if alpha <= 0.15 else "Improving" if alpha < 0.85 else "Controlled"

def tone_color(alpha):
    return COLORS["danger"] if alpha <= 0.15 else COLORS["warn"] if alpha < 0.85 else COLORS["accent3"]

def fig_base(title):
    fig = go.Figure()
    fig.update_layout(template="plotly_dark", paper_bgcolor=COLORS["panel"], plot_bgcolor=COLORS["panel"], font=dict(color=COLORS["text"], family="Inter, Arial, sans-serif"), title=dict(text=title, x=0.02, xanchor="left", font=dict(size=21)), margin=dict(l=30, r=20, t=58, b=35), legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.01))
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)", zeroline=False)
    return fig

def graph(fig, height="430px"):
    return dcc.Graph(figure=fig, config={"displayModeBar": False, "showSendToCloud": False, "displaylogo": False}, style={"height": height})

def metric_card(label, value, detail, accent):
    return html.Div(className="metric-card", children=[html.Div(label, className="metric-label"), html.Div(value, className="metric-value", style={"color": accent}), html.Div(detail, className="metric-detail")])

def options_for_clients(industry_key):
    return [{"label": c, "value": c} for c in INDUSTRIES[industry_key]["clients"]]

def generate_data(industry_key, client_name, days=120):
    cfg = INDUSTRIES[industry_key]
    rng = np.random.default_rng(stable_seed(industry_key, client_name))
    dates = pd.date_range("2026-01-01", periods=days, freq="D")
    def series_between(start, end, volatility, weekly=0.08):
        vals = []
        for i, d in enumerate(dates):
            weekend_factor = 0.92 if d.weekday() >= 5 else 1.0
            seasonal = 1 + weekly * np.sin(i / 10.5)
            noise = rng.normal(0, volatility)
            vals.append(max(0.1, (start * weekend_factor * seasonal) + noise))
        raw = np.array(vals)
        improved = raw * (end / max(raw.mean(), 0.1))
        return raw, improved
    b0, a0 = series_between(cfg["base"]["backlog"], cfg["resolved"]["backlog"], max(8, cfg["base"]["backlog"] * 0.04))
    b1, a1 = series_between(cfg["base"]["onboarding"], cfg["resolved"]["onboarding"], 0.6)
    b2, a2 = series_between(cfg["base"]["billing"], cfg["resolved"]["billing"], max(18, cfg["base"]["billing"] * 0.07))
    b3, a3 = series_between(cfg["base"]["manual"], cfg["resolved"]["manual"], 12)
    b4, a4 = series_between(cfg["base"]["response"], cfg["resolved"]["response"], 3.5)
    before = pd.DataFrame({"date": dates, "backlog": b0.round(0), "onboarding": b1.round(1), "billing": b2.round(0), "manual": b3.round(0), "response": b4.round(0)})
    after = pd.DataFrame({"date": dates, "backlog": a0.round(0), "onboarding": a1.round(1), "billing": a2.round(0), "manual": a3.round(0), "response": a4.round(0)})
    return before, after

def build_trend_fig(before_df, after_df, alpha, cfg):
    current = before_df.copy()
    for c in ["backlog", "onboarding", "billing", "manual", "response"]:
        current[c] = before_df[c] + (after_df[c] - before_df[c]) * alpha
    fig = fig_base(cfg["chart_title"])
    fig.add_trace(go.Scatter(x=before_df["date"], y=before_df["backlog"], mode="lines", name="Messy", line=dict(color=COLORS["danger"], width=2, dash="dot"), opacity=0.45))
    fig.add_trace(go.Scatter(x=after_df["date"], y=after_df["backlog"], mode="lines", name="Controlled", line=dict(color=COLORS["accent3"], width=2, dash="dot"), opacity=0.45))
    fig.add_trace(go.Scatter(x=current["date"], y=current["backlog"], mode="lines", name="Current view", line=dict(color=tone_color(alpha), width=4)))
    fig.update_yaxes(title_text=cfg["metric_names"]["backlog"])
    return fig

def build_compare_bar(metric_key, metrics, cfg):
    fig = fig_base(cfg["metric_names"][metric_key])
    fig.add_trace(go.Bar(x=["Messy state", "Current view", "Controlled state"], y=[metrics[f"{metric_key}_chaos"], metrics[metric_key], metrics[f"{metric_key}_resolved"]], marker_color=[COLORS["danger"], COLORS["warn"], COLORS["accent3"]]))
    if metric_key == "billing":
        fig.update_yaxes(title_text="USD", tickprefix="$", separatethousands=True)
    else:
        fig.update_yaxes(title_text=cfg["units"][metric_key].strip() or "Count")
    return fig

def build_monthly_billing(before_df, after_df, alpha):
    current = before_df.copy()
    for c in ["backlog", "onboarding", "billing", "manual", "response"]:
        current[c] = before_df[c] + (after_df[c] - before_df[c]) * alpha
    for df in (before_df, after_df, current):
        df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)
    mb = before_df.groupby("month", as_index=False)["billing"].sum()
    ma = after_df.groupby("month", as_index=False)["billing"].sum()
    mc = current.groupby("month", as_index=False)["billing"].sum()
    fig = fig_base("Monthly missed revenue / charges")
    fig.add_trace(go.Bar(x=mb["month"], y=mb["billing"], name="Messy", marker_color=COLORS["danger"], opacity=0.30))
    fig.add_trace(go.Bar(x=mc["month"], y=mc["billing"], name="Current view", marker_color=tone_color(alpha)))
    fig.add_trace(go.Scatter(x=ma["month"], y=ma["billing"], name="Controlled", mode="lines+markers", line=dict(color=COLORS["accent3"], width=3)))
    fig.update_yaxes(title_text="USD", tickprefix="$", separatethousands=True)
    return fig

def calc_quote(destination, goods_type, weight, priority="Standard"):
    settings = ROCK_DESTINATIONS[destination]
    goods_mult = ROCK_GOODS_MULTIPLIERS[goods_type]
    priority_mult = 1.18 if priority == "Express" else 1.00
    weight = max(float(weight), 0.1)
    rate_per_kg = settings["rate_per_kg"] * goods_mult * priority_mult
    base_shipping = settings["base_shipping"] * priority_mult
    handling = settings["handling"] + (8 if weight > 25 else 0) + (18 if goods_type == "Electronics" else 0)
    subtotal = (rate_per_kg * weight) + base_shipping + handling
    vat = subtotal * settings["vat_rate"]
    total = subtotal + vat
    eta = settings["eta"] if priority == "Standard" else ("1-3 days" if destination != "Dubai" else "Same day / next day")
    return {"rate_per_kg": round(rate_per_kg, 2), "base_shipping": round(base_shipping, 2), "handling": round(handling, 2), "vat": round(vat, 2), "total": round(total, 2), "eta": eta}

def make_invoice(customer, email, shipment_ref, goods_type, destination, weight, priority, add_insurance, discount_pct):
    quote = calc_quote(destination, goods_type, weight, priority)
    insurance = round(25 if add_insurance else 0, 2)
    subtotal = quote["total"] + insurance
    discount_amt = subtotal * (discount_pct / 100.0)
    final_total = subtotal - discount_amt
    invoice_no = f"INV-{stable_seed(customer, shipment_ref, destination) % 90000 + 10000}"
    return {"invoice_no": invoice_no, "customer": customer, "email": email, "shipment_ref": shipment_ref, "destination": destination, "due_date": "2026-05-07", "total": round(final_total, 2), "line_items": [
        {"item": f"{goods_type} shipment", "amount": quote["base_shipping"] + (quote["rate_per_kg"] * float(weight))},
        {"item": "Handling", "amount": quote["handling"]},
        {"item": "VAT", "amount": quote["vat"]},
    ] + ([{"item": "Insurance", "amount": insurance}] if insurance else []) + ([{"item": f"Discount ({discount_pct:.0f}%)", "amount": -discount_amt}] if discount_amt else [])}

def default_rock_chat():
    return [{"role": "assistant", "text": f"Welcome to the Rock of Ages client workspace. {'Live Gemini connected.' if gemini_enabled() else 'Gemini is not configured yet.'} Ask about quotes, invoices, shipment updates, missing goods, or uploaded documents."}]

def parse_upload(contents, filename):
    if not contents or not filename:
        return "", 0, ""
    _, content_string = contents.split(",", 1)
    raw = base64.b64decode(content_string)
    size = len(raw)
    ext = filename.lower().split(".")[-1]
    text = ""
    try:
        if ext in ["txt", "csv", "json", "md"]:
            text = raw.decode("utf-8", errors="ignore")
        elif ext == "pdf":
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(io.BytesIO(raw))
                text = "\n".join([(p.extract_text() or "") for p in reader.pages[:8]])
            except Exception:
                text = ""
    except Exception:
        text = ""
    return text[:12000], size, ext

# ---------------- App ----------------
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "Datastruma Demo"
app.index_string = """
<!DOCTYPE html><html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}
<meta name='viewport' content='width=device-width, initial-scale=1'>
<style>
body{margin:0;color:#F4F7FB;font-family:Inter,Arial,sans-serif;background:radial-gradient(circle at top left, rgba(83,199,255,0.12), transparent 28%),radial-gradient(circle at top right, rgba(123,140,255,0.10), transparent 26%),linear-gradient(180deg,#06101d 0%,#071120 100%)}
*{box-sizing:border-box}.page{max-width:1500px;margin:0 auto;padding:20px}.panel,.hero,.metric-card,.story-card,.control-card,.info-card,.workspace-card,.module-card,.kpi-mini,.nav-shell,.nav-item-card,.doc-card,.case-card,.chat-bubble{background:linear-gradient(180deg, rgba(16,31,51,0.98), rgba(13,26,43,0.98));border:1px solid rgba(255,255,255,0.06);box-shadow:0 16px 60px rgba(0,0,0,0.28);border-radius:24px}.hero{display:grid;grid-template-columns:1.35fr .95fr;gap:18px;padding:24px}.hero-title{font-size:56px;line-height:.95;letter-spacing:-.04em;margin:8px 0 16px;max-width:950px}.hero-copy{color:#93A8C6;font-size:18px;line-height:1.65;max-width:860px}.eyebrow{display:inline-flex;align-items:center;gap:10px;padding:8px 12px;border-radius:999px;border:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.03);color:#93A8C6;font-size:13px}.hero-badges{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}.badge{padding:11px 15px;border-radius:999px;border:1px solid rgba(255,255,255,0.08);background:linear-gradient(90deg, rgba(83,199,255,0.16), rgba(123,140,255,0.16));font-size:13px;font-weight:700}.snapshot,.kpi-grid-client{display:grid;grid-template-columns:1fr 1fr;gap:12px}.snapshot-card,.kpi-mini{border:1px solid rgba(255,255,255,0.06);border-radius:18px;background:rgba(255,255,255,0.03);padding:16px}.snapshot-big,.kpi-mini .n{font-size:18px;font-weight:800;margin-bottom:6px}.snapshot-small,.small-muted,.story-copy,.module-subtitle{color:#93A8C6}.controls-grid,.workspace-grid{display:grid;grid-template-columns:1.12fr .88fr;gap:16px;margin-top:16px}.control-card,.story-card,.workspace-card,.module-card,.nav-shell{padding:18px}.control-title,.nav-header{font-size:12px;color:#93A8C6;text-transform:uppercase;letter-spacing:.14em;margin-bottom:12px}.control-row{display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:12px;align-items:end}.field-label{color:#93A8C6;font-size:13px;margin-bottom:8px}.metric-grid,.insight-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-top:16px}.metric-label,.mini-title{color:#93A8C6;font-size:13px;margin-bottom:12px}.metric-value{font-size:36px;font-weight:800;letter-spacing:-.03em}.metric-detail{color:#B1ECC0;font-size:13px;margin-top:8px;line-height:1.55}.explain-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:16px}.tabs-panel{margin-top:16px;padding:12px}.tabs .tab{background:transparent!important;border:none!important;color:#93A8C6!important;padding:16px 18px!important;font-weight:700!important;border-bottom:2px solid transparent!important}.tabs .tab--selected{color:#F4F7FB!important;border-bottom:2px solid #53C7FF!important}.chart-grid{display:grid;grid-template-columns:1.25fr .75fr;gap:16px;margin-top:16px}.stack,.doc-grid,.case-list,.nav-list{display:grid;gap:16px}.mini-card,.doc-card,.case-card,.chat-bubble{padding:16px;border-radius:18px;border:1px solid rgba(255,255,255,0.06);background:rgba(255,255,255,0.03)}.mini-copy,.story-copy,.info-copy{font-size:13px;line-height:1.65;color:#F4F7FB}.action-btn{height:44px;border:none;padding:0 18px;border-radius:14px;background:linear-gradient(90deg, rgba(83,199,255,0.25), rgba(123,140,255,0.25));color:#F4F7FB;font-weight:800;cursor:pointer}.secondary-btn{height:42px;border:1px solid rgba(255,255,255,0.14);padding:0 18px;border-radius:14px;background:rgba(255,255,255,0.02);color:#F4F7FB;font-weight:700;cursor:pointer}.route-topbar{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:18px}a.client-link{color:#9fd8ff;text-decoration:none;font-weight:700}.workspace-card-head,.module-header,.summary-line,.flex-row{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.workspace-pill,.case-chip{display:inline-block;padding:8px 12px;border-radius:999px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.07);font-size:12px}.module-layout{display:grid;grid-template-columns:270px 1fr;gap:18px;margin-top:18px}.nav-item-card{padding:14px 16px;cursor:pointer}.nav-item-card.active,.case-card.active{outline:2px solid rgba(83,199,255,0.45);background:linear-gradient(90deg, rgba(83,199,255,0.12), rgba(123,140,255,0.12))}.nav-label{font-size:15px;font-weight:800}.nav-sub{font-size:12px;color:#93A8C6;margin-top:4px;line-height:1.5}.form-grid-2{display:grid;grid-template-columns:1fr 1fr;gap:14px}.form-grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}.form-grid-4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.summary-box{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:18px;padding:16px}.summary-line{padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.07)}.summary-line:last-child{border-bottom:none}.case-layout{display:grid;grid-template-columns:360px 1fr;gap:16px}.chat-role{color:#93A8C6;font-size:12px;text-transform:uppercase;letter-spacing:.12em;margin-bottom:6px}.upload-box{border:1px dashed rgba(255,255,255,0.22);background:rgba(255,255,255,0.02);border-radius:18px;padding:28px 20px;text-align:center}.footer{text-align:center;color:#93A8C6;font-size:13px;padding:14px 0 28px}@media(max-width:1200px){.hero,.controls-grid,.chart-grid,.explain-grid,.workspace-grid,.module-layout,.case-layout{grid-template-columns:1fr}.metric-grid,.insight-grid,.kpi-grid-client,.form-grid-4{grid-template-columns:1fr 1fr}.control-row,.form-grid-3,.form-grid-2{grid-template-columns:1fr 1fr}.hero-title{font-size:42px}}@media(max-width:760px){.metric-grid,.insight-grid,.snapshot,.kpi-grid-client,.form-grid-2,.form-grid-3,.form-grid-4,.control-row{grid-template-columns:1fr}.page{padding:12px}}
</style></head><body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>
"""
app.layout = html.Div(className="page", children=[dcc.Location(id="url", refresh=False), dcc.Store(id="autoplay-store", data=False), dcc.Interval(id="autoplay-interval", interval=850, n_intervals=0, disabled=True), dcc.Store(id="rock-scenario-store", data="Standard Operations"), dcc.Store(id="rock-issues-store", data=ROCK_ISSUE_ROWS), dcc.Store(id="rock-docs-store", data=[]), dcc.Store(id="rock-selected-case-store", data=ROCK_ISSUE_ROWS[0]["case_id"]), dcc.Store(id="rock-ai-store", data=default_rock_chat()), dcc.Store(id="rock-module-store", data="shipping"), html.Div(id="page-router")])

# ---------------- Layout builders ----------------
def main_demo_layout():
    return html.Div(children=[html.Div(className="route-topbar", children=[html.Div(className="eyebrow", children=["Live demo: demo.datastruma.com"]), html.A("Open Rock of Ages client workspace →", href="/client/rockofages", className="client-link")]), html.Div(className="hero", children=[html.Div([html.Img(src=LOGO_SRC, style={"height": "54px", "marginBottom": "12px"}), html.Div("demo.datastruma.com", className="eyebrow"), html.Div(id="hero-title", className="hero-title"), html.Div(id="hero-subtitle", className="hero-copy"), html.Div(className="hero-badges", children=[html.Div("Industry-specific scenarios", className="badge"), html.Div("Chaos to resolution slider", className="badge"), html.Div("Plain-English explanations", className="badge")])]), html.Div([html.Div("Executive snapshot", className="control-title"), html.Div(id="snapshot-grid", className="snapshot")])]), html.Div(className="controls-grid", children=[html.Div(className="control-card", children=[html.Div("Scenario controls", className="control-title"), html.Div(className="control-row", children=[html.Div([html.Div("Industry", className="field-label"), dcc.Dropdown(id="industry-dropdown", options=[{"label": v["label"], "value": k} for k, v in INDUSTRIES.items()], value="home_services", clearable=False, style={"color": "#0B1220"})]), html.Div([html.Div("Company example", className="field-label"), dcc.Dropdown(id="client-dropdown", options=options_for_clients("home_services"), value=INDUSTRIES["home_services"]["clients"][0], clearable=False, style={"color": "#0B1220"})]), html.Div([html.Div("Current state", className="field-label"), html.Div(id="stage-badge", className="badge", style={"display": "inline-flex"})]), html.Button("Play story", id="play-button", n_clicks=0, className="action-btn")]), html.Div(style={"marginTop": "14px"}, children=[html.Div("From messy operations to controlled operations", className="field-label"), dcc.Slider(id="scenario-slider", min=0, max=100, step=1, value=100, marks={0: "Messy", 50: "Improving", 100: "Controlled"}, tooltip={"always_visible": False, "placement": "bottom"})])]), html.Div(className="control-card", children=[html.Div("What this page is showing", className="control-title"), html.Div(id="stage-copy", className="story-copy")])]), html.Div(id="metric-grid", className="metric-grid"), html.Div(id="insight-grid", className="insight-grid"), html.Div(className="explain-grid", children=[html.Div([html.Div("What the chaos looked like", className="story-title"), html.Div(id="chaos-story", className="story-copy")], className="story-card"), html.Div([html.Div("What changed", className="story-title"), html.Div(id="change-list", className="story-copy")], className="story-card"), html.Div([html.Div("Why a business owner should care", className="story-title"), html.Div(id="owner-impact", className="story-copy")], className="story-card")]), html.Div(className="tabs-panel panel", children=[dcc.Tabs(id="pain-tab", value="overview", className="tabs", children=[dcc.Tab(label="Overview", value="overview", className="tab", selected_className="tab--selected"), dcc.Tab(label="Backlog", value="backlog", className="tab", selected_className="tab--selected"), dcc.Tab(label="Onboarding", value="onboarding", className="tab", selected_className="tab--selected"), dcc.Tab(label="Billing", value="billing", className="tab", selected_className="tab--selected"), dcc.Tab(label="Manual Time", value="manual", className="tab", selected_className="tab--selected")]), html.Div(id="charts-content")]), html.Div("Datastruma demo • realistic operating scenarios • plain-English metrics • ready for demo.datastruma.com", className="footer")])

def rock_layout():
    return html.Div(children=[html.Div(className="route-topbar", children=[html.Div(className="eyebrow", children=["Client workspace: Rock of Ages Group"]), html.A("← Back to main demo", href="/", className="client-link")]), html.Div(className="hero", children=[html.Div([html.Img(src=LOGO_SRC, style={"height": "54px", "marginBottom": "12px"}), html.Div("Datastruma for Rock of Ages Group", className="eyebrow"), html.Div(ROCK_CLIENT["hero_title"], className="hero-title", style={"fontSize": "46px"}), html.Div(ROCK_CLIENT["hero_subtitle"], className="hero-copy"), html.Div(className="hero-badges", children=[html.Div("Logistics workspace", className="badge"), html.Div("Client-specific demo", className="badge"), html.Div("Datastruma design system", className="badge")]), html.Div(style={"marginTop": "16px"}, className="story-copy", children=ROCK_CLIENT["summary"])]), html.Div([html.Div("Workspace snapshot", className="control-title"), html.Div(id="rock-kpis", className="kpi-grid-client")])]), html.Div(className="workspace-grid", children=[html.Div(className="workspace-card", children=[html.Div("Rock of Ages scenario", className="control-title"), html.Div(className="form-grid-3", children=[html.Div([html.Div("Operating mode", className="field-label"), dcc.Dropdown(id="rock-scenario-dropdown", options=[{"label": k, "value": k} for k in ROCK_SCENARIOS.keys()], value="Standard Operations", clearable=False, style={"color": "#0B1220"})]), html.Div([html.Div("Client", className="field-label"), dcc.Dropdown(id="rock-customer-dropdown", options=[{"label": c["label"], "value": c["value"]} for c in ROCK_SAVED_CUSTOMERS], value=ROCK_SAVED_CUSTOMERS[0]["value"], clearable=False, style={"color": "#0B1220"})]), html.Div([html.Div("Workspace note", className="field-label"), html.Div("Built as a client-specific Datastruma logistics workspace", className="workspace-pill")])])]), html.Div(className="workspace-card", children=[html.Div("Business context", className="control-title"), html.Div("Rock of Ages handles freight coordination, customer updates, invoice processing, customs follow-up, and issue handling. This workspace turns those day-to-day tasks into a cleaner client-facing operating story.", className="story-copy")])]), html.Div(className="module-layout", children=[html.Div(className="nav-shell", children=[html.Div("Workspace modules", className="nav-header"), html.Div(id="rock-nav-list", className="nav-list")]), html.Div(id="rock-module-content")]), html.Div("Datastruma client workspace • Rock of Ages Group • logistics operations demo", className="footer")])

@app.callback(Output("page-router", "children"), Input("url", "pathname"))
def route_pages(path):
    return rock_layout() if path == "/client/rockofages" else main_demo_layout()

# ---------------- Main demo callbacks ----------------
@app.callback(Output("client-dropdown", "options"), Output("client-dropdown", "value"), Input("industry-dropdown", "value"))
def update_client_options(industry_key):
    opts = options_for_clients(industry_key)
    return opts, opts[0]["value"]

@app.callback(Output("autoplay-store", "data"), Output("autoplay-interval", "disabled"), Output("play-button", "children"), Input("play-button", "n_clicks"), State("autoplay-store", "data"), prevent_initial_call=True)
def toggle_autoplay(n_clicks, running):
    new = not running
    return new, (not new), ("Pause story" if new else "Play story")

@app.callback(Output("scenario-slider", "value"), Output("autoplay-store", "data", allow_duplicate=True), Output("autoplay-interval", "disabled", allow_duplicate=True), Output("play-button", "children", allow_duplicate=True), Input("autoplay-interval", "n_intervals"), State("scenario-slider", "value"), State("autoplay-store", "data"), prevent_initial_call=True)
def autoplay_step(n, value, running):
    if not running:
        return no_update, no_update, no_update, no_update
    new_value = max(0, int(value) - 5)
    return (new_value, False, True, "Play story") if new_value <= 0 else (new_value, True, False, "Pause story")

@app.callback(Output("hero-title", "children"), Output("hero-subtitle", "children"), Output("snapshot-grid", "children"), Output("stage-badge", "children"), Output("stage-badge", "style"), Output("stage-copy", "children"), Output("metric-grid", "children"), Output("insight-grid", "children"), Output("chaos-story", "children"), Output("change-list", "children"), Output("owner-impact", "children"), Output("charts-content", "children"), Input("industry-dropdown", "value"), Input("client-dropdown", "value"), Input("scenario-slider", "value"), Input("pain-tab", "value"))
def update_main_demo(industry_key, client_name, slider_value, tab_value):
    cfg = INDUSTRIES[industry_key]
    alpha = slider_value / 100.0
    before_df, after_df = generate_data(industry_key, client_name)
    current_df = before_df.copy()
    for c in ["backlog", "onboarding", "billing", "manual", "response"]:
        current_df[c] = before_df[c] + (after_df[c] - before_df[c]) * alpha
    metrics = {"backlog_chaos": cfg["base"]["backlog"], "backlog_resolved": cfg["resolved"]["backlog"], "backlog": current_df["backlog"].mean(), "onboarding_chaos": cfg["base"]["onboarding"], "onboarding_resolved": cfg["resolved"]["onboarding"], "onboarding": current_df["onboarding"].mean(), "billing_chaos": cfg["base"]["billing"], "billing_resolved": cfg["resolved"]["billing"], "billing": current_df["billing"].mean(), "manual_chaos": cfg["base"]["manual"], "manual_resolved": cfg["resolved"]["manual"], "manual": current_df["manual"].mean(), "response_chaos": cfg["base"]["response"], "response_resolved": cfg["resolved"]["response"], "response": current_df["response"].mean()}
    stage = current_stage(alpha)
    color = tone_color(alpha)
    snapshot_cards = [html.Div([html.Div(f"{((metrics['backlog_chaos'] - metrics['backlog']) / metrics['backlog_chaos']) * 100:.0f}% lower", className="snapshot-big", style={"color": color}), html.Div(f"Lower {cfg['metric_names']['backlog'].lower()} means less work is sitting around waiting.", className="snapshot-small")], className="snapshot-card"), html.Div([html.Div(f"{((metrics['onboarding_chaos'] - metrics['onboarding']) / metrics['onboarding_chaos']) * 100:.0f}% faster", className="snapshot-big", style={"color": color}), html.Div(f"Lower {cfg['metric_names']['onboarding'].lower()} means new people become productive faster.", className="snapshot-small")], className="snapshot-card"), html.Div([html.Div(f"{((metrics['billing_chaos'] - metrics['billing']) / metrics['billing_chaos']) * 100:.0f}% less missed revenue", className="snapshot-big", style={"color": color}), html.Div(f"Lower {cfg['metric_names']['billing'].lower()} means fewer valid charges are being missed.", className="snapshot-small")], className="snapshot-card"), html.Div([html.Div(f"{((metrics['manual_chaos'] - metrics['manual']) / metrics['manual_chaos']) * 100:.0f}% less manual time", className="snapshot-big", style={"color": color}), html.Div(f"Lower {cfg['metric_names']['manual'].lower()} means the team spends less time chasing work.", className="snapshot-small")], className="snapshot-card")]
    metric_cards = [metric_card(cfg["metric_names"]["backlog"], f"{metrics['backlog']:,.0f}", f"Messy state {cfg['base']['backlog']} → controlled state {cfg['resolved']['backlog']}", color), metric_card(cfg["metric_names"]["onboarding"], f"{metrics['onboarding']:.1f} hrs", f"Messy state {cfg['base']['onboarding']} hrs → controlled state {cfg['resolved']['onboarding']} hrs", color), metric_card(cfg["metric_names"]["billing"], f"${metrics['billing']:,.0f}", f"Messy state ${cfg['base']['billing']} → controlled state ${cfg['resolved']['billing']}", color), metric_card(cfg["metric_names"]["manual"], f"{metrics['manual']:,.0f} min", f"Messy state {cfg['base']['manual']} min → controlled state {cfg['resolved']['manual']} min", color), metric_card(cfg["metric_names"]["response"], f"{metrics['response']:,.0f} min", f"Messy state {cfg['base']['response']} min → controlled state {cfg['resolved']['response']} min", color)]
    insight_cards = [html.Div([html.Div(cfg["metric_names"][k], className="mini-title"), html.Div(f"{cfg['metric_names'][k]}: {metrics[k]:,.1f if k=='onboarding' else ''}", className="mini-copy")], className="mini-card") for k in ["backlog","onboarding","billing","manual","response"]]
    trend_fig = build_trend_fig(before_df.copy(), after_df.copy(), alpha, cfg)
    onboarding_fig = build_compare_bar("onboarding", metrics, cfg)
    response_fig = build_compare_bar("response", metrics, cfg)
    billing_fig = build_monthly_billing(before_df.copy(), after_df.copy(), alpha)
    manual_fig = build_compare_bar("manual", metrics, cfg)
    backlog_fig = build_compare_bar("backlog", metrics, cfg)
    charts = html.Div(className="chart-grid", children=[html.Div(className="stack", children=[html.Div(className="panel", children=[graph(trend_fig)]), html.Div(className="panel", children=[graph(response_fig)])]), html.Div(className="stack", children=[html.Div(className="panel", children=[graph(onboarding_fig if tab_value != 'billing' else billing_fig)]), html.Div(className="panel", children=[graph(billing_fig if tab_value == 'overview' else (manual_fig if tab_value == 'manual' else backlog_fig if tab_value == 'backlog' else response_fig))])])])
    copy = {"Messy": "The operation is in firefighting mode. Too much is being handled manually, work is stacking up, and customers feel the delay.", "Improving": "The operation is improving. Some bottlenecks are being reduced, but the business is still partway through the clean-up.", "Controlled": "The operation is more controlled. Work is moving faster, fewer items are waiting, and more revenue and time are being protected."}[stage]
    changes = ["Work is routed more clearly, so fewer items sit waiting without action.", "Repeated steps are handled in a more repeatable way, reducing delay.", "Billing checkpoints catch more missed charges before revenue is lost.", "The team spends less time firefighting and more time delivering work cleanly."] if stage == "Controlled" else ["Ownership is becoming clearer and repeated work is being handled more consistently.", "The most common handoffs are being tightened, so delays begin to shrink.", "Valid charges and missed revenue are becoming easier to spot.", "Manual coordination is dropping, but the business has not fully stabilized yet."] if stage == "Improving" else ["Work is landing in too many places and staff are spending time chasing updates.", "Repeated tasks are not standardized, so handoffs take longer than they should.", "Important billing details are easier to miss when the team is under pressure.", "The business feels busy, but too much of that busyness is manual rework."]
    return cfg["headline"], cfg["subheadline"], snapshot_cards, stage, {"display": "inline-flex", "background": "rgba(255,255,255,0.05)", "border": f"1px solid {color}", "color": COLORS["text"]}, copy, metric_cards, insight_cards, cfg["chaos_story"], html.Ul([html.Li(x) for x in changes], style={"margin": "0", "paddingLeft": "18px", "lineHeight": "1.85", "color": COLORS["muted"]}), cfg["owner_impact"], charts

# ---------------- Rock callbacks ----------------
@app.callback(Output("rock-kpis", "children"), Output("rock-scenario-store", "data"), Input("rock-scenario-dropdown", "value"))
def update_rock_kpis(scenario_name):
    cfg = ROCK_SCENARIOS[scenario_name]
    cards = [html.Div(className="kpi-mini", children=[html.Div(str(cfg[k]), className="n"), html.Div(lbl, className="l")]) for k, lbl in [("shipments", "Active shipments"), ("issues", "Open issues"), ("customers_saved", "Saved customers"), ("documents", "Documents processed")]]
    return cards, scenario_name

@app.callback(Output("rock-module-store", "data"), Input({"type": "rock-nav", "index": ALL}, "n_clicks"), State("rock-module-store", "data"), prevent_initial_call=True)
def change_rock_module(clicks, current):
    trig = ctx.triggered_id
    return current if not trig else trig["index"]

@app.callback(Output("rock-nav-list", "children"), Input("rock-module-store", "data"))
def render_nav(active):
    return [html.Div(className=f"nav-item-card {'active' if key == active else ''}", id={"type": "rock-nav", "index": key}, n_clicks=0, children=[html.Div(label, className="nav-label"), html.Div(sub, className="nav-sub")]) for key, label, sub in ROCK_MODULES]

def render_shipping(selected_customer):
    email = next((c["email"] for c in ROCK_SAVED_CUSTOMERS if c["value"] == selected_customer), ROCK_SAVED_CUSTOMERS[0]["email"])
    q = calc_quote("Dubai", "Fashion Items", 10, "Standard")
    return html.Div(className="module-card", children=[html.Div(className="module-header", children=[html.Div([html.Div("Shipping Calculator", className="module-title"), html.Div("Use saved customer details, shipment type, destination, and priority to generate a quick logistics estimate that looks client-ready.", className="module-subtitle")]), html.Div("Real estimate builder", className="workspace-pill")]), html.Div(className="form-grid-2", children=[html.Div(children=[html.Div([html.Div("Saved customer", className="field-label"), dcc.Dropdown(id="calc-customer", options=[{"label": c["label"], "value": c["value"]} for c in ROCK_SAVED_CUSTOMERS], value=selected_customer, clearable=False, style={"color": "#0B1220"})]), html.Div(style={"marginTop": "12px"}, children=[html.Div("Customer email", className="field-label"), dcc.Input(id="calc-email", value=email, type="email", style={"width": "100%", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"})]), html.Div(className="form-grid-2", style={"marginTop": "12px"}, children=[html.Div([html.Div("Goods type", className="field-label"), dcc.Dropdown(id="calc-goods", options=[{"label": k, "value": k} for k in ROCK_GOODS_MULTIPLIERS.keys()], value="Fashion Items", clearable=False, style={"color": "#0B1220"})]), html.Div([html.Div("Destination", className="field-label"), dcc.Dropdown(id="calc-destination", options=[{"label": k, "value": k} for k in ROCK_DESTINATIONS.keys()], value="Dubai", clearable=False, style={"color": "#0B1220"})])]), html.Div(className="form-grid-2", style={"marginTop": "12px"}, children=[html.Div([html.Div("Weight (kg)", className="field-label"), dcc.Input(id="calc-weight", type="number", value=10, min=1, style={"width": "100%", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"})]), html.Div([html.Div("Priority", className="field-label"), dcc.Dropdown(id="calc-priority", options=[{"label": "Standard", "value": "Standard"}, {"label": "Express", "value": "Express"}], value="Standard", clearable=False, style={"color": "#0B1220"})])]), html.Button("Generate estimate", id="calc-generate-btn", n_clicks=0, className="action-btn", style={"marginTop": "14px"})]), html.Div(children=[html.Div("Estimate summary", className="field-label"), html.Div(id="calc-summary", className="summary-box", children=[html.Div(className="summary-line", children=[html.Span("Rate per kg"), html.Strong(f"${q['rate_per_kg']:.2f}")]), html.Div(className="summary-line", children=[html.Span("Base shipping"), html.Strong(f"${q['base_shipping']:.2f}")]), html.Div(className="summary-line", children=[html.Span("Handling"), html.Strong(f"${q['handling']:.2f}")]), html.Div(className="summary-line", children=[html.Span("VAT"), html.Strong(f"${q['vat']:.2f}")]), html.Div(className="summary-line", children=[html.Span("Estimated ETA"), html.Strong(q['eta'])]), html.Div(className="summary-line", children=[html.Span("Total estimate"), html.Strong(f"${q['total']:.2f}", style={"fontSize": "28px"})])])])])])

def render_invoice(selected_customer):
    email = next((c["email"] for c in ROCK_SAVED_CUSTOMERS if c["value"] == selected_customer), ROCK_SAVED_CUSTOMERS[0]["email"])
    return html.Div(className="module-card", children=[html.Div(className="module-header", children=[html.Div([html.Div("Invoice Generator", className="module-title"), html.Div("Turn shipment details into a polished invoice view with line-item clarity, insurance, discount control, and a send-ready summary.", className="module-subtitle")]), html.Div("Client-ready invoice flow", className="workspace-pill")]), html.Div(className="form-grid-2", children=[html.Div(children=[html.Div(className="form-grid-2", children=[html.Div([html.Div("Customer", className="field-label"), dcc.Dropdown(id="inv-customer", options=[{"label": c["label"], "value": c["value"]} for c in ROCK_SAVED_CUSTOMERS], value=selected_customer, clearable=False, style={"color": "#0B1220"})]), html.Div([html.Div("Customer email", className="field-label"), dcc.Input(id="inv-email", value=email, type="email", style={"width": "100%", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"})])]), html.Div(style={"marginTop": "12px"}, children=[html.Div("Shipment reference", className="field-label"), dcc.Input(id="inv-shipment", value="ROA-NEW-001", style={"width": "100%", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"})]), html.Div(className="form-grid-2", style={"marginTop": "12px"}, children=[html.Div([html.Div("Goods type", className="field-label"), dcc.Dropdown(id="inv-goods", options=[{"label": k, "value": k} for k in ROCK_GOODS_MULTIPLIERS.keys()], value="Fashion Items", clearable=False, style={"color": "#0B1220"})]), html.Div([html.Div("Destination", className="field-label"), dcc.Dropdown(id="inv-destination", options=[{"label": k, "value": k} for k in ROCK_DESTINATIONS.keys()], value="Lagos", clearable=False, style={"color": "#0B1220"})])]), html.Div(className="form-grid-4", style={"marginTop": "12px"}, children=[html.Div([html.Div("Weight (kg)", className="field-label"), dcc.Input(id="inv-weight", type="number", value=12, min=1, style={"width": "100%", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"})]), html.Div([html.Div("Priority", className="field-label"), dcc.Dropdown(id="inv-priority", options=[{"label": "Standard", "value": "Standard"}, {"label": "Express", "value": "Express"}], value="Standard", clearable=False, style={"color": "#0B1220"})]), html.Div([html.Div("Insurance", className="field-label"), dcc.Dropdown(id="inv-insurance", options=[{"label": "No", "value": "No"}, {"label": "Yes", "value": "Yes"}], value="No", clearable=False, style={"color": "#0B1220"})]), html.Div([html.Div("Discount %", className="field-label"), dcc.Input(id="inv-discount", type="number", value=0, min=0, max=25, style={"width": "100%", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"})])]), html.Div(className="flex-row", style={"marginTop": "14px"}, children=[html.Button("Generate invoice", id="inv-generate-btn", n_clicks=0, className="action-btn"), html.Button("Send to customer", id="inv-send-btn", n_clicks=0, className="secondary-btn")]), html.Div(id="inv-send-status", className="small-muted", style={"marginTop": "10px"})]), html.Div([html.Div("Invoice preview", className="field-label"), html.Div(id="invoice-preview", className="summary-box")])])])

def render_tracking(shipments_data, scenario_name):
    shipment_df = pd.DataFrame(shipments_data)
    return html.Div(className="module-card", children=[html.Div(className="module-header", children=[html.Div([html.Div("Shipment Tracking", className="module-title"), html.Div("Track movement, identify bottlenecks, and show the client how operational visibility improves under different scenarios.", className="module-subtitle")]), html.Div(scenario_name, className="workspace-pill")]), html.Div(children=[dash_table.DataTable(data=shipments_data, columns=[{"name": c.replace("_", " ").title(), "id": c} for c in shipment_df.columns], style_as_list_view=True, style_table={"overflowX": "auto"}, style_cell={"backgroundColor": COLORS["panel"], "color": COLORS["text"], "border": "none", "padding": "12px", "textAlign": "left", "fontFamily": "Inter, Arial, sans-serif"}, style_header={"backgroundColor": COLORS["panel2"], "color": COLORS["text"], "fontWeight": "bold", "border": "none"}, page_size=8)])])

def render_missing(issues_data, selected_case_id, shipments_data):
    selected = next((r for r in issues_data if r["case_id"] == selected_case_id), issues_data[0])
    cards = [html.Div(className=f"case-card {'active' if row['case_id'] == selected_case_id else ''}", id={"type": "case-select", "index": row["case_id"]}, n_clicks=0, children=[html.Div(className="flex-row", children=[html.Strong(row["case_id"]), html.Span(row["status"], className="case-chip"), html.Span(row.get("priority", "Medium"), className="case-chip")]), html.Div(row["customer"], style={"marginTop": "10px", "fontWeight": "800"}), html.Div(row["issue"], className="small-muted", style={"marginTop": "6px"})]) for row in issues_data]
    return html.Div(className="module-card", children=[html.Div(className="module-header", children=[html.Div([html.Div("Missing Goods", className="module-title"), html.Div("Handle issue investigation in a cleaner, more client-friendly flow. Select a case, update it, and generate a customer update with Gemini.", className="module-subtitle")]), html.Div("Issue resolution workspace", className="workspace-pill")]), html.Div(className="case-layout", children=[html.Div(children=[html.Div("Active cases", className="field-label"), html.Div(className="case-list", children=cards), html.Div(style={"marginTop": "14px"}, className="summary-box", children=[html.Div("Add new issue", className="field-label"), dcc.Dropdown(id="issue-shipment", options=[{"label": r["shipment_id"], "value": r["shipment_id"]} for r in shipments_data], value=shipments_data[0]["shipment_id"], clearable=False, style={"color": "#0B1220"}), dcc.Input(id="issue-desc", value="1 carton missing", style={"width": "100%", "marginTop": "10px", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"}), html.Div(className="form-grid-3", style={"marginTop": "10px"}, children=[dcc.Input(id="issue-owner", value="Fatima", style={"width": "100%", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"}), dcc.Dropdown(id="issue-status", options=[{"label": s, "value": s} for s in ["New", "Investigating", "Waiting for supplier", "Customer updated", "Resolved"]], value="Investigating", clearable=False, style={"color": "#0B1220"}), dcc.Dropdown(id="issue-priority", options=[{"label": s, "value": s} for s in ["Low", "Medium", "High", "Critical"]], value="High", clearable=False, style={"color": "#0B1220"})]), dcc.Textarea(id="issue-update", value="Customer informed that container review is in progress.", style={"width": "100%", "height": "110px", "marginTop": "10px", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"}), html.Button("Add case", id="issue-add-btn", n_clicks=0, className="action-btn", style={"marginTop": "10px"})])]), html.Div(children=[html.Div(className="summary-box", children=[html.Div(className="summary-line", children=[html.Span("Case ID"), html.Strong(selected["case_id"])]), html.Div(className="summary-line", children=[html.Span("Shipment"), html.Strong(selected["shipment_id"])]), html.Div(className="summary-line", children=[html.Span("Customer"), html.Strong(selected["customer"])]), html.Div(className="summary-line", children=[html.Span("Owner"), html.Strong(selected["owner"])]), html.Div(className="summary-line", children=[html.Span("Priority"), html.Strong(selected.get("priority", "Medium"))]), html.Div(className="summary-line", children=[html.Span("Status"), html.Strong(selected["status"])]), ]), html.Div(className="form-grid-2", style={"marginTop": "14px"}, children=[html.Div([html.Div("Issue", className="field-label"), dcc.Input(id="edit-issue", value=selected["issue"], style={"width": "100%", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"})]), html.Div([html.Div("Status", className="field-label"), dcc.Dropdown(id="edit-status", options=[{"label": s, "value": s} for s in ["New", "Investigating", "Waiting for supplier", "Customer updated", "Resolved"]], value=selected["status"], clearable=False, style={"color": "#0B1220"})])]), html.Div(style={"marginTop": "12px"}, children=[html.Div("Latest internal update", className="field-label"), dcc.Textarea(id="edit-update", value=selected["last_update"], style={"width": "100%", "height": "110px", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"})]), html.Div(style={"marginTop": "12px"}, children=[html.Div("Customer-facing message", className="field-label"), dcc.Textarea(id="edit-customer-message", value=selected.get("customer_message", ""), style={"width": "100%", "height": "110px", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"})]), html.Div(className="flex-row", style={"marginTop": "12px"}, children=[html.Button("Save case updates", id="issue-save-btn", n_clicks=0, className="action-btn"), html.Button("Draft customer update with Gemini", id="issue-draft-btn", n_clicks=0, className="secondary-btn")]), html.Div(id="issue-status-output", className="small-muted", style={"marginTop": "10px"})])])])

def render_documents(docs_data):
    cards = [html.Div(className="doc-card", children=[html.Div("No document uploaded yet", className="nav-label"), html.Div("Upload an invoice copy, bill of lading, manifest, customs document, or packing list. The workspace will always register the upload and, when Gemini is configured, generate a real summary.", className="small-muted")])] if not docs_data else [html.Div(className="doc-card", children=[html.Div(className="flex-row", children=[html.Div(doc["name"], className="nav-label"), html.Div(doc["doc_type"], className="workspace-pill")]), html.Div(f"Size: {doc['size_kb']} KB • Type: {doc['extension'].upper()} • Uploaded: {doc['uploaded_at']}", className="small-muted"), html.Div(doc["summary"], className="story-copy", style={"marginTop": "8px"}), html.Div(f"Detected shipment reference: {doc.get('shipment_reference') or 'Not found'}", className="small-muted", style={"marginTop": "8px"}), html.Div(f"Customer: {doc.get('customer_name') or 'Not found'}", className="small-muted"), html.Div(f"Action needed: {doc.get('action_needed') or 'Review manually'}", className="small-muted")]) for doc in docs_data[::-1]]
    return html.Div(className="module-card", children=[html.Div(className="module-header", children=[html.Div([html.Div("Document Upload", className="module-title"), html.Div("Upload logistics documents and turn them into visible, structured summaries instead of leaving them buried in email or shared drives.", className="module-subtitle")]), html.Div("Live upload workflow", className="workspace-pill")]), html.Div(className="form-grid-2", children=[html.Div(children=[html.Div("Document type", className="field-label"), dcc.Dropdown(id="doc-type", options=[{"label": d, "value": d} for d in ["Invoice Copy", "Bill of Lading", "Goods Manifest", "Customer ID", "Customs Document", "Packing List"]], value="Invoice Copy", clearable=False, style={"color": "#0B1220"}), html.Div(className="upload-box", style={"marginTop": "12px"}, children=[dcc.Upload(id="doc-upload", children=html.Div(["Drag a file here or click to choose a file"]), multiple=False, style={"padding": "26px 12px"})]), html.Div(style={"marginTop": "12px"}, children=[html.Div("Document note", className="field-label"), dcc.Textarea(id="doc-note", value="Customer invoice received for shipment ROA-24021.", style={"width": "100%", "height": "110px", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"})]), html.Div(id="doc-upload-status", className="small-muted", style={"marginTop": "12px"})]), html.Div(children=[html.Div("Document summaries", className="field-label"), html.Div(className="doc-grid", children=cards)])])])

def render_assistant(chat_rows):
    return html.Div(className="module-card", children=[html.Div(className="module-header", children=[html.Div([html.Div("AI Assistant", className="module-title"), html.Div("Use Gemini to draft shipment updates, explain charges, summarize uploaded documents, and turn internal operations notes into polished customer-facing language.", className="module-subtitle")]), html.Div("Gemini connected" if gemini_enabled() else "Gemini not configured", className="workspace-pill")]), html.Div(className="stack", children=[html.Div(className="chat-bubble", children=[html.Div(msg["role"].title(), className="chat-role"), html.Div(msg["text"], className="story-copy")]) for msg in chat_rows]), dcc.Textarea(id="rock-ai-input", value="", placeholder="Ask about a shipment, invoice, customer message, missing-goods case, or uploaded document...", style={"width": "100%", "height": "110px", "marginTop": "12px", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"}), html.Div(className="flex-row", style={"marginTop": "12px"}, children=[html.Button("Ask assistant", id="rock-ai-send-btn", n_clicks=0, className="action-btn"), html.Button("Clear chat", id="rock-ai-clear-btn", n_clicks=0, className="secondary-btn")])])

def render_scenario(scenario_name):
    cfg = ROCK_SCENARIOS[scenario_name]
    return html.Div(className="module-card", children=[html.Div(className="module-header", children=[html.Div([html.Div("Scenario Builder", className="module-title"), html.Div("Switch the client story between standard flow, delay pressure, invoice cleanup, or issue escalation while keeping the same Datastruma shell.", className="module-subtitle")]), html.Div(cfg["badge"], className="workspace-pill")]), html.Div(className="form-grid-2", children=[html.Div(className="summary-box", children=[html.Div(className="summary-line", children=[html.Span("Active shipments"), html.Strong(str(cfg["shipments"]))]), html.Div(className="summary-line", children=[html.Span("Open issues"), html.Strong(str(cfg["issues"]))]), html.Div(className="summary-line", children=[html.Span("Documents processed"), html.Strong(str(cfg["documents"]))]), html.Div(className="summary-line", children=[html.Span("Story angle"), html.Strong(cfg["badge"])])]), html.Div(className="summary-box", children=[html.Div("How to narrate the scenario", className="field-label"), html.Div("Start with what the client is feeling, then show which workspace modules become most valuable under this operating condition.", className="story-copy")])])])

@app.callback(Output("rock-module-content", "children"), Input("rock-module-store", "data"), Input("rock-customer-dropdown", "value"), Input("rock-issues-store", "data"), Input("rock-selected-case-store", "data"), Input("rock-docs-store", "data"), Input("rock-ai-store", "data"), Input("rock-scenario-store", "data"))
def render_module(active, selected_customer, issues_data, selected_case_id, docs_data, chat_rows, scenario_name):
    if active == "shipping":
        return render_shipping(selected_customer)
    if active == "invoice":
        return render_invoice(selected_customer)
    if active == "tracking":
        return render_tracking(ROCK_TRACKING_ROWS, scenario_name)
    if active == "missing":
        return render_missing(issues_data, selected_case_id, ROCK_TRACKING_ROWS)
    if active == "documents":
        return render_documents(docs_data)
    if active == "assistant":
        return render_assistant(chat_rows)
    return render_scenario(scenario_name)

# Shipping
@app.callback(Output("calc-summary", "children"), Input("calc-generate-btn", "n_clicks"), State("calc-destination", "value"), State("calc-goods", "value"), State("calc-weight", "value"), State("calc-priority", "value"), prevent_initial_call=False)
def update_calc_summary(n_clicks, destination, goods_type, weight, priority):
    q = calc_quote(destination, goods_type, weight or 10, priority)
    return [html.Div(className="summary-line", children=[html.Span("Rate per kg"), html.Strong(f"${q['rate_per_kg']:.2f}")]), html.Div(className="summary-line", children=[html.Span("Base shipping"), html.Strong(f"${q['base_shipping']:.2f}")]), html.Div(className="summary-line", children=[html.Span("Handling"), html.Strong(f"${q['handling']:.2f}")]), html.Div(className="summary-line", children=[html.Span("VAT"), html.Strong(f"${q['vat']:.2f}")]), html.Div(className="summary-line", children=[html.Span("Estimated ETA"), html.Strong(q['eta'])]), html.Div(className="summary-line", children=[html.Span("Total estimate"), html.Strong(f"${q['total']:.2f}", style={"fontSize": "28px"})])]
# Invoice
@app.callback(Output("invoice-preview", "children"), Output("inv-send-status", "children"), Input("inv-generate-btn", "n_clicks"), Input("inv-send-btn", "n_clicks"), State("inv-customer", "value"), State("inv-email", "value"), State("inv-shipment", "value"), State("inv-goods", "value"), State("inv-destination", "value"), State("inv-weight", "value"), State("inv-priority", "value"), State("inv-insurance", "value"), State("inv-discount", "value"), prevent_initial_call=False)
def invoice_preview(generate, send, customer, email, shipment_ref, goods_type, destination, weight, priority, insurance, discount):
    inv = make_invoice(customer, email, shipment_ref, goods_type, destination, weight or 10, priority, insurance == "Yes", float(discount or 0))
    preview = [html.Div(className="summary-line", children=[html.Span("Invoice number"), html.Strong(inv["invoice_no"])]), html.Div(className="summary-line", children=[html.Span("Customer"), html.Strong(inv["customer"])]), html.Div(className="summary-line", children=[html.Span("Shipment reference"), html.Strong(inv["shipment_ref"])]), html.Div(className="summary-line", children=[html.Span("Due date"), html.Strong(inv["due_date"])]), *[html.Div(className="summary-line", children=[html.Span(item["item"]), html.Strong(f"${item['amount']:,.2f}")]) for item in inv["line_items"]], html.Div(className="summary-line", children=[html.Span("Total due"), html.Strong(f"${inv['total']:,.2f}", style={"fontSize": "28px"})])]
    status = f"Invoice {inv['invoice_no']} generated."
    if ctx.triggered_id == "inv-send-btn":
        status = f"Invoice {inv['invoice_no']} marked as sent to {email}."
    return preview, status
# Missing goods select/add/save/draft
@app.callback(Output("rock-selected-case-store", "data"), Input({"type": "case-select", "index": ALL}, "n_clicks"), State("rock-selected-case-store", "data"), prevent_initial_call=True)
def select_case(clicks, current):
    trig = ctx.triggered_id
    return current if not trig else trig["index"]

@app.callback(Output("rock-issues-store", "data", allow_duplicate=True), Output("rock-selected-case-store", "data", allow_duplicate=True), Input("issue-add-btn", "n_clicks"), State("rock-issues-store", "data"), State("issue-shipment", "value"), State("issue-desc", "value"), State("issue-owner", "value"), State("issue-status", "value"), State("issue-priority", "value"), State("issue-update", "value"), prevent_initial_call=True)
def add_case(n, rows, shipment_ref, desc, owner, status, priority, update):
    rows = rows or []
    customer = next((r["customer"] for r in ROCK_TRACKING_ROWS if r["shipment_id"] == shipment_ref), "Unknown")
    new = {"case_id": f"MG-{1040 + len(rows) + 1}", "shipment_id": shipment_ref, "customer": customer, "issue": desc, "status": status, "owner": owner, "priority": priority, "last_update": update, "customer_message": "We have logged your issue and our team is reviewing the latest confirmed handoff. We will send the next update shortly."}
    return rows + [new], new["case_id"]

@app.callback(Output("rock-issues-store", "data"), Output("issue-status-output", "children"), Input("issue-save-btn", "n_clicks"), Input("issue-draft-btn", "n_clicks"), State("rock-issues-store", "data"), State("rock-selected-case-store", "data"), State("edit-issue", "value"), State("edit-status", "value"), State("edit-update", "value"), State("edit-customer-message", "value"), prevent_initial_call=True)
def save_case(save, draft, rows, case_id, issue_text, status, update, cust_msg):
    out = ""
    new_rows = []
    for row in rows or []:
        if row["case_id"] == case_id:
            row = dict(row)
            row["issue"] = issue_text
            row["status"] = status
            row["last_update"] = update
            if ctx.triggered_id == "issue-draft-btn":
                row["customer_message"] = call_gemini(f"Write a short, polished customer update for a logistics missing-goods case. Shipment ID: {row['shipment_id']}. Customer: {row['customer']}. Issue: {row['issue']}. Status: {row['status']}. Latest internal note: {row['last_update']}. Return only the customer-facing message.", "You write polished logistics customer updates.") if gemini_enabled() else "We are actively reviewing the missing-goods issue and checking the last verified handoff. We will provide the next confirmed update within 24 hours."
                out = "Customer update drafted."
            else:
                row["customer_message"] = cust_msg
                out = "Case updated."
            new_rows.append(row)
        else:
            new_rows.append(row)
    return new_rows, out
# Documents
@app.callback(Output("rock-docs-store", "data"), Output("doc-upload-status", "children"), Input("doc-upload", "contents"), State("doc-upload", "filename"), State("doc-type", "value"), State("doc-note", "value"), State("rock-docs-store", "data"), prevent_initial_call=True)
def upload_doc(contents, filename, doc_type, note, rows):
    rows = rows or []
    if not contents or not filename:
        return rows, "No file received."
    extracted, size_bytes, ext = parse_upload(contents, filename)
    uploaded_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    size_kb = max(1, round(size_bytes / 1024))
    if gemini_enabled():
        summary_text = call_gemini(f"You are summarizing a logistics document for operations use. Document type: {doc_type}. Filename: {filename}. User note: {note}. Document text: {extracted[:6000] if extracted else '[No extractable text found. Use filename and note only.]'} Return JSON with keys summary, shipment_reference, customer_name, action_needed.", "Return concise structured logistics document summaries.")
    else:
        summary_text = f"{doc_type} uploaded. {note} This workspace registered the file successfully, but Gemini is not configured for live summarization."
    summary = summary_text.strip(); shipment_reference = customer_name = action_needed = None
    try:
        if summary.startswith("{"):
            parsed = json.loads(summary)
            summary = parsed.get("summary") or note
            shipment_reference = parsed.get("shipment_reference")
            customer_name = parsed.get("customer_name")
            action_needed = parsed.get("action_needed")
    except Exception:
        pass
    rows.append({"name": filename, "doc_type": doc_type, "summary": summary, "shipment_reference": shipment_reference, "customer_name": customer_name, "action_needed": action_needed, "size_kb": size_kb, "extension": ext, "uploaded_at": uploaded_at})
    return rows, f"{filename} uploaded and summarized."
# AI chat
@app.callback(Output("rock-ai-store", "data"), Input("rock-ai-send-btn", "n_clicks"), Input("rock-ai-clear-btn", "n_clicks"), State("rock-ai-input", "value"), State("rock-ai-store", "data"), State("rock-scenario-store", "data"), State("rock-customer-dropdown", "value"), State("rock-issues-store", "data"), State("rock-selected-case-store", "data"), prevent_initial_call=True)
def ai_chat(send, clear, message, chat_rows, scenario_name, selected_customer, issues, selected_case_id):
    if ctx.triggered_id == "rock-ai-clear-btn":
        return default_rock_chat()
    chat_rows = chat_rows or []
    msg = (message or "").strip()
    if not msg:
        return chat_rows
    issue = next((r for r in (issues or []) if r["case_id"] == selected_case_id), None)
    issue_text = f" Selected issue: {issue}" if issue else ""
    reply = call_gemini(f"You are the Datastruma AI assistant for a client demo workspace. Client: Rock of Ages Group. Industry: Logistics. Scenario: {scenario_name}. Selected customer: {selected_customer}.{issue_text} User request: {msg} Answer in polished plain business English. Be specific, operational, and useful.", "You are a logistics operations copilot inside a premium client demo workspace.") if gemini_enabled() else "Gemini is not configured yet. Add GEMINI_API_KEY or GOOGLE_API_KEY in Render to enable live responses."
    return chat_rows + [{"role": "user", "text": msg}, {"role": "assistant", "text": reply}]

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
