import base64
import hashlib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html, no_update, dash_table, ctx

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
    "line": "#20344F",
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

def stable_seed(*parts):
    key = "|".join(str(p) for p in parts)
    return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)

def lerp(a, b, alpha):
    return a + (b - a) * alpha

def current_stage(alpha):
    if alpha <= 0.15:
        return "Messy"
    if alpha < 0.85:
        return "Improving"
    return "Controlled"

def tone_color(alpha):
    if alpha <= 0.15:
        return COLORS["danger"]
    if alpha < 0.85:
        return COLORS["warn"]
    return COLORS["accent3"]

def fig_base(title):
    fig = go.Figure()
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=COLORS["panel"],
        plot_bgcolor=COLORS["panel"],
        font=dict(color=COLORS["text"], family="Inter, Arial, sans-serif"),
        title=dict(text=title, x=0.02, xanchor="left", font=dict(size=21)),
        margin=dict(l=30, r=20, t=58, b=35),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.01),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)", zeroline=False)
    return fig

def graph(fig, height="430px"):
    return dcc.Graph(figure=fig, config={"displayModeBar": False, "showSendToCloud": False, "displaylogo": False}, style={"height": height})

def metric_card(label, value, detail, accent):
    return html.Div(className="metric-card", children=[html.Div(label, className="metric-label"), html.Div(value, className="metric-value", style={"color": accent}), html.Div(detail, className="metric-detail")])

INDUSTRIES = {
    "home_services": {
        "label": "Home Services",
        "headline": "See where dispatch chaos builds — and what better looks like.",
        "subheadline": "A realistic business demo for companies handling service calls, technician dispatch, onboarding, billing cleanup, and office coordination.",
        "clients": ["UrbanFix HVAC", "BluePeak Plumbing", "Metro Electric", "EverFlow Services", "RapidHome Repairs"],
        "metric_names": {"backlog": "Jobs still waiting", "onboarding": "Technician setup delay", "billing": "Daily missed billing", "manual": "Dispatch and office admin time", "response": "Average scheduling response time"},
        "units": {"backlog": "", "onboarding": " hrs", "billing": "$", "manual": " min", "response": " min"},
        "meanings": {"backlog": "how many jobs are still waiting because work is coming in faster than it is being scheduled or completed.", "onboarding": "how long it takes to fully set up a new technician with systems, schedules, tools, and permissions.", "billing": "money lost when trip fees, add-on work, or changes in scope do not get captured properly.", "manual": "time spent manually dispatching, calling, rescheduling, updating customers, and correcting paperwork.", "response": "how long it takes before the office gets back to the customer with a real scheduling update."},
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
        "meanings": {"backlog": "how many patient-related requests are still waiting to be handled.", "onboarding": "how long it takes to fully set up a new staff member across systems and processes.", "billing": "revenue lost when charge capture, coding follow-up, or process handoffs break down.", "manual": "time staff spend chasing information, updating status, and coordinating across teams.", "response": "how long patients wait before the clinic responds clearly."},
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
        "meanings": {"backlog": "how many shipments, jobs, or exceptions are still waiting to be processed or cleared.", "onboarding": "how long it takes to fully set up a new coordinator, warehouse staff member, or operations user.", "billing": "revenue missed when storage, handling, route changes, surcharges, or accessorials are not billed cleanly.", "manual": "time spent dispatching, correcting manifests, chasing proof of delivery, updating customers, and reconciling exceptions.", "response": "how long it takes before a customer gets a reliable status update."},
        "chaos_story": "Shipment exceptions were piling up, updates were being chased manually, proof-of-delivery and surcharge details were not always flowing cleanly into billing, and operations staff were spending too much time fixing status issues by hand.",
        "owner_impact": "When this improves, fewer shipments sit in limbo, customers get clearer updates, teams spend less time firefighting, and less revenue slips away.",
        "base": {"backlog": 620, "onboarding": 16.2, "billing": 640, "manual": 312, "response": 54},
        "resolved": {"backlog": 285, "onboarding": 8.4, "billing": 245, "manual": 158, "response": 28},
        "chart_title": "Logistics operations trend",
    },
    "legal": {
        "label": "Legal",
        "headline": "See where case operations slow down — and what better looks like.",
        "subheadline": "A realistic business demo for law firms dealing with request backlog, client intake delays, billing leakage, and manual admin work.",
        "clients": ["Apex Legal Group", "StoneBridge Law", "Harbor Counsel", "Crestview Litigation", "North Gate Advisory"],
        "metric_names": {"backlog": "Requests still waiting", "onboarding": "Client or staff setup delay", "billing": "Daily missed billing", "manual": "Manual admin time", "response": "Average response time"},
        "units": {"backlog": "", "onboarding": " hrs", "billing": "$", "manual": " min", "response": " min"},
        "meanings": {"backlog": "how many incoming matters, tasks, or client requests are still waiting to be handled.", "onboarding": "how long it takes to fully intake a client or set up a new internal team member.", "billing": "money lost when billable work, changes, or follow-up items do not make it cleanly into billing.", "manual": "time spent chasing approvals, status updates, intake details, and handoffs.", "response": "how long it takes before the firm gives a clear response."},
        "chaos_story": "Intake was inconsistent, updates lived in emails, work moved through too many manual checkpoints, and some billable items were captured late or not at all.",
        "owner_impact": "When this improves, client communication feels stronger, admin drag drops, and more earned revenue is captured.",
        "base": {"backlog": 290, "onboarding": 10.5, "billing": 248, "manual": 210, "response": 31},
        "resolved": {"backlog": 135, "onboarding": 5.4, "billing": 96, "manual": 114, "response": 18},
        "chart_title": "Firm operations trend",
    },
}

ROCK_CLIENT = {
    "client_name": "Rock of Ages Group",
    "hero_title": "Logistics operations, customer support, invoicing, and document processing in one connected workspace.",
    "hero_subtitle": "A Datastruma client workspace tailored for Rock of Ages Group to handle shipment estimates, invoice creation, shipment status updates, missing-goods follow-up, uploaded logistics documents, and AI-assisted support.",
    "summary": "Rock of Ages Group handles freight coordination, customer support, invoice processing, and issue resolution across a growing logistics operation.",
}
ROCK_SAVED_CUSTOMERS = [
    {"label": "Queen Esther Trading LLC", "value": "Queen Esther Trading LLC", "email": "operations@queenesthertrading.com"},
    {"label": "Blue Pearl General Trading", "value": "Blue Pearl General Trading", "email": "ops@bluepearltrade.com"},
    {"label": "Al Noor Fashion Hub", "value": "Al Noor Fashion Hub", "email": "support@alnoorfashion.ae"},
]
ROCK_DESTINATIONS = {
    "Dubai": {"rate_per_kg": 10.5, "base_shipping": 105, "handling": 15, "vat_rate": 0.05, "eta": "1-2 days"},
    "Lagos": {"rate_per_kg": 15.0, "base_shipping": 160, "handling": 25, "vat_rate": 0.05, "eta": "4-6 days"},
    "Abuja": {"rate_per_kg": 15.5, "base_shipping": 170, "handling": 25, "vat_rate": 0.05, "eta": "4-6 days"},
    "Port Harcourt": {"rate_per_kg": 16.0, "base_shipping": 180, "handling": 28, "vat_rate": 0.05, "eta": "5-7 days"},
}
ROCK_GOODS_MULTIPLIERS = {"Fashion Items": 1.00, "Electronics": 1.18, "Documents": 0.72, "Mixed Commercial Goods": 1.12}
ROCK_TRACKING_ROWS = [
    {"shipment_id": "ROA-24019", "customer": "Queen Esther Trading LLC", "status": "In transit", "origin": "Dubai", "destination": "Lagos", "eta": "2026-04-27", "issue": "None"},
    {"shipment_id": "ROA-24020", "customer": "Blue Pearl General Trading", "status": "Customs review", "origin": "Dubai", "destination": "Abuja", "eta": "2026-04-29", "issue": "Awaiting customs release"},
]
ROCK_ISSUE_ROWS = [
    {"case_id": "MG-1041", "shipment_id": "ROA-24020", "customer": "Blue Pearl General Trading", "issue": "2 cartons missing", "status": "Investigating", "owner": "Fatima", "last_update": "Container checked; supplier follow-up in progress"},
]
ROCK_DOC_TYPES = ["Invoice Copy", "Bill of Lading", "Goods Manifest", "Customs Document"]
ROCK_SCENARIOS = {
    "Standard Operations": {"shipments": 148, "issues": 2, "customers_saved": 3, "documents": 18, "badge": "Standard flow"},
    "High Shipment Volume": {"shipments": 226, "issues": 7, "customers_saved": 3, "documents": 31, "badge": "Peak volume"},
    "Delayed Shipments": {"shipments": 151, "issues": 11, "customers_saved": 3, "documents": 20, "badge": "Delay pressure"},
    "Missing Goods Escalation": {"shipments": 136, "issues": 15, "customers_saved": 3, "documents": 26, "badge": "Issue surge"},
}

def generate_data(industry_key, client_name, days=120):
    cfg = INDUSTRIES[industry_key]
    seed = stable_seed(industry_key, client_name)
    rng = np.random.default_rng(seed)
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

def interpolate_frame(before_df, after_df, alpha):
    current = before_df.copy()
    for col in ["backlog", "onboarding", "billing", "manual", "response"]:
        current[col] = lerp(before_df[col], after_df[col], alpha)
    return current

def format_value(metric_key, value, cfg):
    unit = cfg["units"][metric_key]
    if metric_key == "billing":
        return f"${value:,.0f}"
    if metric_key == "onboarding":
        return f"{value:.1f}{unit}"
    return f"{value:,.0f}{unit}"

def metric_summary_text(metric_key, current_value, chaos_value, resolved_value, cfg):
    return f"{cfg['metric_names'][metric_key]}: {format_value(metric_key, current_value, cfg)}. In plain English, this means {cfg['meanings'][metric_key]} In the messy state it was {format_value(metric_key, chaos_value, cfg)}. In the controlled state it comes down to {format_value(metric_key, resolved_value, cfg)}."

def build_trend_fig(before_df, after_df, alpha, cfg):
    current = interpolate_frame(before_df, after_df, alpha)
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
    current = interpolate_frame(before_df, after_df, alpha)
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
    priority_mult = 1.18 if priority == "Express" else 1.0
    weight = max(float(weight), 0.1)
    rate_per_kg = settings["rate_per_kg"] * goods_mult * priority_mult
    base_shipping = settings["base_shipping"] * priority_mult
    handling = settings["handling"] + (8 if weight > 25 else 0) + (18 if goods_type == "Electronics" else 0)
    subtotal = rate_per_kg * weight + base_shipping + handling
    vat = subtotal * settings["vat_rate"]
    total = subtotal + vat
    eta = settings["eta"] if priority == "Standard" else "1-3 days"
    return {"rate_per_kg": round(rate_per_kg, 2), "base_shipping": round(base_shipping, 2), "handling": round(handling, 2), "vat": round(vat, 2), "total": round(total, 2), "eta": eta}

def make_invoice(customer, email, shipment_ref, goods_type, destination, weight, priority, add_insurance, discount_pct):
    quote = calc_quote(destination, goods_type, weight, priority)
    insurance = 25 if add_insurance else 0
    subtotal = quote["total"] + insurance
    discount_amt = subtotal * (discount_pct / 100.0)
    total = subtotal - discount_amt
    invoice_no = f"INV-{stable_seed(customer, shipment_ref)%90000 + 10000}"
    items = [
        {"item": f"{goods_type} shipment", "amount": quote["base_shipping"] + quote["rate_per_kg"] * float(weight)},
        {"item": "Handling", "amount": quote["handling"]},
        {"item": "VAT", "amount": quote["vat"]},
    ]
    if insurance: items.append({"item": "Insurance", "amount": insurance})
    if discount_amt: items.append({"item": f"Discount ({discount_pct:.0f}%)", "amount": -discount_amt})
    return {"invoice_no": invoice_no, "customer": customer, "email": email, "shipment_ref": shipment_ref, "due_date": "2026-05-07", "line_items": items, "total": round(total,2)}

def assistant_reply(message, scenario):
    text = (message or "").lower().strip()
    if not text: return "Ask about a shipment, invoice, missing goods, customer update, or uploaded document."
    if "missing" in text or "damage" in text: return f"For {scenario}, start by confirming the shipment reference, the last verified handoff, and the exact quantity missing. Then send the customer a clear update with an owner and next timing."
    if "invoice" in text or "charge" in text or "billing" in text: return "Break the invoice into base shipping, handling, VAT, and any surcharge so the customer understands the total immediately."
    if "shipment" in text or "tracking" in text or "delivery" in text: return "Confirm current status, destination, ETA, and any blocker first. Then tell the customer exactly when the next update will be sent."
    if "document" in text or "upload" in text: return "Summarize the uploaded document into shipment reference, customer, amount, date, and any action still pending."
    return "Route the request through the closest flow: quote, invoice, tracking, missing goods, or document review. Give one clear next step and one promised update time."

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "Datastruma Demo"

app.index_string = """
<!DOCTYPE html><html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}<meta name='viewport' content='width=device-width, initial-scale=1'>
<style>
:root { --text:#F4F7FB; --muted:#93A8C6; --accent:#53C7FF; --accent2:#7B8CFF; --accent3:#78F0A7; --warn:#FFB454; --danger:#FF7A90; }
* { box-sizing:border-box; }
body { margin:0; color:var(--text); font-family:Inter, Arial, sans-serif; background:radial-gradient(circle at top left, rgba(83,199,255,0.12), transparent 28%), radial-gradient(circle at top right, rgba(123,140,255,0.10), transparent 26%), linear-gradient(180deg, #06101d 0%, #071120 100%); }
.page { max-width:1500px; margin:0 auto; padding:20px; }
.panel, .hero, .metric-card, .story-card, .control-card, .info-card, .workspace-card, .module-card, .snapshot-card, .mini-card, .kpi-mini { background:linear-gradient(180deg, rgba(16,31,51,0.98), rgba(13,26,43,0.98)); border:1px solid rgba(255,255,255,0.06); box-shadow:0 16px 60px rgba(0,0,0,0.28); border-radius:24px; }
.hero { display:grid; grid-template-columns:1.35fr 0.95fr; gap:18px; padding:24px; }
.hero-title { font-size:56px; line-height:0.95; letter-spacing:-0.04em; margin:8px 0 16px; max-width:950px; }
.hero-copy { color:var(--muted); font-size:18px; line-height:1.65; max-width:860px; }
.eyebrow { display:inline-flex; align-items:center; gap:10px; padding:8px 12px; border-radius:999px; border:1px solid rgba(255,255,255,0.08); background:rgba(255,255,255,0.03); color:var(--muted); font-size:13px; }
.hero-badges, .flex-row { display:flex; flex-wrap:wrap; gap:10px; align-items:center; }
.badge, .small-pill { padding:11px 15px; border-radius:999px; border:1px solid rgba(255,255,255,0.08); background:linear-gradient(90deg, rgba(83,199,255,0.16), rgba(123,140,255,0.16)); font-size:13px; font-weight:700; }
.snapshot, .metric-grid, .insight-grid, .explain-grid, .controls-grid, .workspace-grid, .module-shell, .chart-grid, .form-grid-2, .form-grid-3, .form-grid-4, .kpi-grid-client { display:grid; gap:16px; }
.snapshot { grid-template-columns:1fr 1fr; }
.controls-grid { grid-template-columns:1.12fr 0.88fr; margin-top:16px; }
.control-row { display:grid; grid-template-columns:1fr 1fr 1fr auto; gap:12px; align-items:end; }
.metric-grid, .insight-grid { grid-template-columns:repeat(5, 1fr); margin-top:16px; }
.explain-grid { grid-template-columns:repeat(3, 1fr); margin-top:16px; }
.chart-grid { grid-template-columns:1.25fr 0.75fr; margin-top:16px; }
.workspace-grid { grid-template-columns:0.9fr 1.7fr; margin-top:18px; }
.module-shell { grid-template-columns:260px 1fr; margin-top:18px; }
.form-grid-2 { grid-template-columns:1fr 1fr; }
.form-grid-3 { grid-template-columns:1fr 1fr 1fr; }
.form-grid-4 { grid-template-columns:1fr 1fr 1fr 1fr; }
.kpi-grid-client { grid-template-columns:repeat(4, 1fr); }
.control-card,.story-card,.info-card,.workspace-card,.module-card,.metric-card,.mini-card,.kpi-mini { padding:18px; }
.metric-label,.field-label,.mini-title,.control-title { color:var(--muted); font-size:13px; margin-bottom:8px; }
.control-title { text-transform:uppercase; letter-spacing:0.14em; font-size:12px; }
.metric-value { font-size:36px; font-weight:800; letter-spacing:-0.03em; }
.metric-detail { color:#B1ECC0; font-size:13px; margin-top:8px; line-height:1.55; }
.story-title,.info-title { font-size:18px; font-weight:800; margin-bottom:8px; }
.story-copy,.info-copy,.mini-copy,.nav-copy { color:var(--muted); font-size:14px; line-height:1.72; }
.tabs-panel { margin-top:16px; padding:12px; }
.tabs .tab { background:transparent !important; border:none !important; color:var(--muted) !important; padding:16px 18px !important; font-weight:700 !important; border-bottom:2px solid transparent !important; }
.tabs .tab--selected { color:var(--text) !important; border-bottom:2px solid var(--accent) !important; }
.action-btn,.secondary-btn { height:44px; padding:0 18px; border-radius:14px; color:var(--text); font-weight:800; cursor:pointer; }
.action-btn { border:none; background:linear-gradient(90deg, rgba(83,199,255,0.25), rgba(123,140,255,0.25)); }
.secondary-btn { border:1px solid rgba(255,255,255,0.14); background:rgba(255,255,255,0.02); }
.summary-box,.upload-box { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:16px; }
.summary-line { display:flex; justify-content:space-between; gap:12px; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.07); }
.summary-line:last-child { border-bottom:none; }
.route-topbar { display:flex; justify-content:space-between; align-items:center; gap:16px; margin-bottom:18px; }
a.client-link { color:#9fd8ff; text-decoration:none; }
.footer { text-align:center; color:var(--muted); font-size:13px; padding:14px 0 28px; }
@media (max-width:1200px) { .hero,.controls-grid,.chart-grid,.explain-grid,.module-shell { grid-template-columns:1fr; } .metric-grid,.insight-grid,.kpi-grid-client { grid-template-columns:1fr 1fr; } .control-row,.form-grid-3,.form-grid-4 { grid-template-columns:1fr 1fr; } .hero-title { font-size:42px; } }
@media (max-width:760px) { .metric-grid,.insight-grid,.snapshot,.form-grid-2,.form-grid-3,.form-grid-4,.control-row,.kpi-grid-client,.explain-grid { grid-template-columns:1fr; } .page { padding:12px; } }
</style></head><body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>
"""


def demo_home_layout():
    return html.Div(children=[
        html.Div(className="route-topbar", children=[html.Div(className="eyebrow", children=["Live demo: demo.datastruma.com"]), html.A("Open client workspace → /client/rockofages", href="/client/rockofages", className="client-link")]),
        html.Div(className="hero", children=[
            html.Div([html.Img(src=LOGO_SRC, style={"height": "54px", "marginBottom": "12px"}), html.Div("demo.datastruma.com", className="eyebrow"), html.Div(id="hero-title", className="hero-title"), html.Div(id="hero-subtitle", className="hero-copy"), html.Div(className="hero-badges", children=[html.Div("Industry-specific scenarios", className="badge"), html.Div("Chaos to resolution slider", className="badge"), html.Div("Plain-English explanations", className="badge")])]),
            html.Div([html.Div("Executive snapshot", className="control-title"), html.Div(id="snapshot-grid", className="snapshot")])]),
        html.Div(className="controls-grid", children=[
            html.Div(className="control-card", children=[html.Div("Scenario controls", className="control-title"), html.Div(className="control-row", children=[
                html.Div([html.Div("Industry", className="field-label"), dcc.Dropdown(id="industry-dropdown", options=[{"label": v["label"], "value": k} for k, v in INDUSTRIES.items()], value="home_services", clearable=False, style={"color": "#0B1220"})]),
                html.Div([html.Div("Company example", className="field-label"), dcc.Dropdown(id="client-dropdown", options=[{"label": c, "value": c} for c in INDUSTRIES["home_services"]["clients"]], value=INDUSTRIES["home_services"]["clients"][0], clearable=False, style={"color": "#0B1220"})]),
                html.Div([html.Div("Current state", className="field-label"), html.Div(id="stage-badge", className="badge", style={"display": "inline-flex"})]),
                html.Button("Play story", id="play-button", n_clicks=0, className="action-btn")]),
                html.Div(style={"marginTop": "14px"}, children=[html.Div("From messy operations to controlled operations", className="field-label"), dcc.Slider(id="scenario-slider", min=0, max=100, step=1, value=100, marks={0: "Messy", 50: "Improving", 100: "Controlled"})])]),
            html.Div(className="control-card", children=[html.Div("What this page is showing", className="control-title"), html.Div(id="stage-copy", className="story-copy")])]),
        html.Div(id="metric-grid", className="metric-grid"),
        html.Div(id="insight-grid", className="insight-grid"),
        html.Div(className="explain-grid", children=[html.Div([html.Div("What the chaos looked like", className="story-title"), html.Div(id="chaos-story", className="story-copy")], className="story-card"), html.Div([html.Div("What changed", className="story-title"), html.Div(id="change-list", className="story-copy")], className="story-card"), html.Div([html.Div("Why a business owner should care", className="story-title"), html.Div(id="owner-impact", className="story-copy")], className="story-card")]),
        html.Div(className="tabs-panel panel", children=[dcc.Tabs(id="pain-tab", value="overview", className="tabs", children=[dcc.Tab(label="Overview", value="overview", className="tab", selected_className="tab--selected"), dcc.Tab(label="Backlog", value="backlog", className="tab", selected_className="tab--selected"), dcc.Tab(label="Onboarding", value="onboarding", className="tab", selected_className="tab--selected"), dcc.Tab(label="Billing", value="billing", className="tab", selected_className="tab--selected"), dcc.Tab(label="Manual Time", value="manual", className="tab", selected_className="tab--selected")]), html.Div(id="charts-content")]),
        html.Div("Datastruma demo • realistic operating scenarios • plain-English metrics • ready for demo.datastruma.com or /demo", className="footer")])

def rockofages_layout():
    return html.Div(children=[
        html.Div(className="route-topbar", children=[html.Div(className="eyebrow", children=["Client workspace: Rock of Ages Group"]), html.A("← Back to main demo", href="/", className="client-link")]),
        html.Div(className="hero", children=[
            html.Div([html.Img(src=LOGO_SRC, style={"height": "54px", "marginBottom": "12px"}), html.Div("Datastruma for Rock of Ages Group", className="eyebrow"), html.Div(ROCK_CLIENT["hero_title"], className="hero-title", style={"fontSize": "46px"}), html.Div(ROCK_CLIENT["hero_subtitle"], className="hero-copy"), html.Div(className="hero-badges", children=[html.Div("Logistics workspace", className="badge"), html.Div("Client-specific demo", className="badge"), html.Div("Datastruma design system", className="badge")]), html.Div(style={"marginTop": "16px"}, className="story-copy", children=ROCK_CLIENT["summary"])]),
            html.Div([html.Div("Workspace snapshot", className="control-title"), html.Div(id="rock-kpis", className="kpi-grid-client")])]),
        html.Div(className="controls-grid", children=[html.Div(className="control-card", children=[html.Div("Rock of Ages scenario", className="control-title"), html.Div(className="form-grid-3", children=[html.Div([html.Div("Operating mode", className="field-label"), dcc.Dropdown(id="rock-scenario-dropdown", options=[{"label": k, "value": k} for k in ROCK_SCENARIOS], value="Standard Operations", clearable=False, style={"color": "#0B1220"})]), html.Div([html.Div("Client", className="field-label"), dcc.Dropdown(id="rock-customer-dropdown", options=[{"label": c["label"], "value": c["value"]} for c in ROCK_SAVED_CUSTOMERS], value=ROCK_SAVED_CUSTOMERS[0]["value"], clearable=False, style={"color": "#0B1220"})]), html.Div([html.Div("Workspace note", className="field-label"), html.Div("Built as a client-focused Datastruma logistics demo", className="eyebrow")])])]), html.Div(className="control-card", children=[html.Div("Business context", className="control-title"), html.Div("Rock of Ages handles freight coordination, customer updates, invoice processing, customs follow-up, and issue handling. This workspace shows how those activities can sit in one connected Datastruma client page.", className="story-copy")])]),
        html.Div(className="module-shell", children=[html.Div(className="workspace-card", children=[dcc.Tabs(id="rock-module-tabs", value="shipping", className="tabs", vertical=True, children=[dcc.Tab(label="Shipping Calculator", value="shipping", className="tab", selected_className="tab--selected"), dcc.Tab(label="Invoice Generator", value="invoice", className="tab", selected_className="tab--selected"), dcc.Tab(label="Shipment Tracking", value="tracking", className="tab", selected_className="tab--selected"), dcc.Tab(label="Missing Goods", value="issues", className="tab", selected_className="tab--selected"), dcc.Tab(label="Document Upload", value="docs", className="tab", selected_className="tab--selected"), dcc.Tab(label="AI Assistant", value="ai", className="tab", selected_className="tab--selected"), dcc.Tab(label="Scenario Builder", value="scenario", className="tab", selected_className="tab--selected")])]), html.Div(id="rock-module-content")]),
        html.Div("Datastruma client workspace • Rock of Ages Group • logistics operations demo", className="footer")])

app.layout = html.Div(className="page", children=[dcc.Location(id="url"), dcc.Store(id="autoplay-store", data=False), dcc.Interval(id="autoplay-interval", interval=850, n_intervals=0, disabled=True), dcc.Store(id="rock-scenario-store", data="Standard Operations"), dcc.Store(id="rock-issues-store", data=ROCK_ISSUE_ROWS), dcc.Store(id="rock-docs-store", data=[]), dcc.Store(id="rock-ai-store", data=[{"role": "assistant", "text": "Welcome to the Rock of Ages client workspace. Ask about quotes, invoices, shipment updates, missing goods, or uploaded documents."}]), html.Div(id="page-router")])

@app.callback(Output("page-router", "children"), Input("url", "pathname"))
def route_pages(path):
    return rockofages_layout() if path == "/client/rockofages" else demo_home_layout()

@app.callback(Output("client-dropdown", "options"), Output("client-dropdown", "value"), Input("industry-dropdown", "value"))
def update_clients(industry_key):
    opts = [{"label": c, "value": c} for c in INDUSTRIES[industry_key]["clients"]]
    return opts, opts[0]["value"]

@app.callback(Output("autoplay-store", "data"), Output("autoplay-interval", "disabled"), Output("play-button", "children"), Input("play-button", "n_clicks"), State("autoplay-store", "data"), prevent_initial_call=True)
def toggle_autoplay(n, running):
    new = not running
    return new, (not new), ("Pause story" if new else "Play story")

@app.callback(Output("scenario-slider", "value"), Output("autoplay-store", "data", allow_duplicate=True), Output("autoplay-interval", "disabled", allow_duplicate=True), Output("play-button", "children", allow_duplicate=True), Input("autoplay-interval", "n_intervals"), State("scenario-slider", "value"), State("autoplay-store", "data"), prevent_initial_call=True)
def autoplay_step(n, value, running):
    if not running: return no_update, no_update, no_update, no_update
    new_value = max(0, int(value)-5)
    if new_value <= 0: return new_value, False, True, "Play story"
    return new_value, True, False, "Pause story"

@app.callback(Output("hero-title", "children"), Output("hero-subtitle", "children"), Output("snapshot-grid", "children"), Output("stage-badge", "children"), Output("stage-badge", "style"), Output("stage-copy", "children"), Output("metric-grid", "children"), Output("insight-grid", "children"), Output("chaos-story", "children"), Output("change-list", "children"), Output("owner-impact", "children"), Output("charts-content", "children"), Input("industry-dropdown", "value"), Input("client-dropdown", "value"), Input("scenario-slider", "value"), Input("pain-tab", "value"))
def update_main(industry_key, client_name, slider_value, tab):
    cfg = INDUSTRIES[industry_key]
    alpha = slider_value / 100.0
    before_df, after_df = generate_data(industry_key, client_name)
    current_df = interpolate_frame(before_df, after_df, alpha)
    metrics = {k+"_chaos": cfg["base"][k] for k in ["backlog","onboarding","billing","manual","response"]}
    metrics.update({k+"_resolved": cfg["resolved"][k] for k in ["backlog","onboarding","billing","manual","response"]})
    metrics.update({"backlog": current_df["backlog"].mean(), "onboarding": current_df["onboarding"].mean(), "billing": current_df["billing"].mean(), "manual": current_df["manual"].mean(), "response": current_df["response"].mean()})
    stage = current_stage(alpha); color = tone_color(alpha)
    snapshot_cards = [html.Div([html.Div(f"{((metrics['backlog_chaos']-metrics['backlog'])/metrics['backlog_chaos'])*100:.0f}% lower", className="snapshot-big", style={"color": color}), html.Div(f"Lower {cfg['metric_names']['backlog'].lower()} means less work is sitting around waiting.", className="snapshot-small")], className="snapshot-card"), html.Div([html.Div(f"{((metrics['onboarding_chaos']-metrics['onboarding'])/metrics['onboarding_chaos'])*100:.0f}% faster", className="snapshot-big", style={"color": color}), html.Div(f"Lower {cfg['metric_names']['onboarding'].lower()} means new people become productive faster.", className="snapshot-small")], className="snapshot-card"), html.Div([html.Div(f"{((metrics['billing_chaos']-metrics['billing'])/metrics['billing_chaos'])*100:.0f}% less missed revenue", className="snapshot-big", style={"color": color}), html.Div(f"Lower {cfg['metric_names']['billing'].lower()} means fewer valid charges are being missed.", className="snapshot-small")], className="snapshot-card"), html.Div([html.Div(f"{((metrics['manual_chaos']-metrics['manual'])/metrics['manual_chaos'])*100:.0f}% less manual time", className="snapshot-big", style={"color": color}), html.Div(f"Lower {cfg['metric_names']['manual'].lower()} means the team spends less time chasing work.", className="snapshot-small")], className="snapshot-card")]
    metric_cards = [metric_card(cfg["metric_names"][k], format_value(k, metrics[k], cfg), f"Messy state {format_value(k, metrics[k+'_chaos'], cfg)} → controlled state {format_value(k, metrics[k+'_resolved'], cfg)}", color) for k in ["backlog","onboarding","billing","manual","response"]]
    insight_cards = [html.Div([html.Div(cfg["metric_names"][k], className="mini-title"), html.Div(metric_summary_text(k, metrics[k], metrics[k+"_chaos"], metrics[k+"_resolved"], cfg), className="mini-copy")], className="mini-card") for k in ["backlog","onboarding","billing","manual","response"]]
    trend_fig = build_trend_fig(before_df.copy(), after_df.copy(), alpha, cfg)
    onboarding_fig = build_compare_bar("onboarding", metrics, cfg)
    response_fig = build_compare_bar("response", metrics, cfg)
    billing_fig = build_monthly_billing(before_df.copy(), after_df.copy(), alpha)
    manual_fig = build_compare_bar("manual", metrics, cfg)
    backlog_fig = build_compare_bar("backlog", metrics, cfg)
    if tab == "overview": charts = html.Div(className="chart-grid", children=[html.Div(children=[html.Div(className="panel chart-panel", children=[graph(trend_fig)]), html.Div(className="panel chart-panel", children=[graph(response_fig)])]), html.Div(children=[html.Div(className="panel chart-panel", children=[graph(onboarding_fig)]), html.Div(className="panel chart-panel", children=[graph(billing_fig)])])])
    elif tab == "backlog": charts = html.Div(className="chart-grid", children=[html.Div(className="panel chart-panel", children=[graph(trend_fig)]), html.Div(children=[html.Div(className="panel chart-panel", children=[graph(backlog_fig)]), html.Div(className="info-card", children=[html.Div("What this tells the owner", className="info-title"), html.Div("When this number is high, work is waiting longer than it should. That usually means customers feel delay even when the team feels busy all day.", className="info-copy")])])])
    elif tab == "onboarding": charts = html.Div(className="chart-grid", children=[html.Div(className="panel chart-panel", children=[graph(onboarding_fig)]), html.Div(children=[html.Div(className="panel chart-panel", children=[graph(response_fig)]), html.Div(className="info-card", children=[html.Div("What this tells the owner", className="info-title"), html.Div("When this number is high, new people are taking too long to get fully ready. That slows productivity and increases confusion early.", className="info-copy")])])])
    elif tab == "billing": charts = html.Div(className="chart-grid", children=[html.Div(className="panel chart-panel", children=[graph(billing_fig)]), html.Div(children=[html.Div(className="panel chart-panel", children=[graph(response_fig)]), html.Div(className="info-card", children=[html.Div("What this tells the owner", className="info-title"), html.Div("When this number is high, valid charges or revenue are quietly being missed. The business did the work but did not collect all the money it should have.", className="info-copy")])])])
    else: charts = html.Div(className="chart-grid", children=[html.Div(className="panel chart-panel", children=[graph(manual_fig)]), html.Div(children=[html.Div(className="panel chart-panel", children=[graph(response_fig)]), html.Div(className="info-card", children=[html.Div("What this tells the owner", className="info-title"), html.Div("When this number is high, skilled people are spending too much time coordinating, checking, correcting, and chasing — instead of moving work forward.", className="info-copy")])])])
    return cfg["headline"], cfg["subheadline"], snapshot_cards, stage, {"display":"inline-flex","background":"rgba(255,255,255,0.05)","border":f"1px solid {color}","color":COLORS["text"]}, ("The operation is in firefighting mode. Too much is being handled manually, work is stacking up, and customers feel the delay." if alpha <= 0.15 else "The operation is improving. Some bottlenecks are being reduced, but the business is still partway through the clean-up." if alpha < 0.85 else "The operation is more controlled. Work is moving faster, fewer items are waiting, and more revenue and time are being protected."), metric_cards, insight_cards, cfg["chaos_story"], html.Ul([html.Li(x) for x in (["Work is landing in too many places and staff are spending time chasing updates.","Repeated tasks are not standardized, so handoffs take longer than they should.","Important billing details are easier to miss when the team is under pressure.","The business feels busy, but too much of that busyness is manual rework."] if alpha <= 0.15 else ["Ownership is becoming clearer and repeated work is being handled more consistently.","The most common handoffs are being tightened, so delays begin to shrink.","Valid charges and missed revenue are becoming easier to spot.","Manual coordination is dropping, but the business has not fully stabilized yet."] if alpha < 0.85 else ["Work is routed more clearly, so fewer items sit waiting without action.","Repeated steps are handled in a more repeatable way, reducing delay.","Billing checkpoints catch more missed charges before revenue is lost.","The team spends less time firefighting and more time delivering work cleanly."] )], style={"margin":"0","paddingLeft":"18px","lineHeight":"1.85","color":COLORS["muted"]}), cfg["owner_impact"], charts

@app.callback(Output("rock-scenario-store", "data"), Output("rock-kpis", "children"), Input("rock-scenario-dropdown", "value"))
def update_rock_kpis(s):
    cfg = ROCK_SCENARIOS[s]
    cards = [html.Div(className="kpi-mini", children=[html.Div(str(cfg[k]), className="metric-value", style={"fontSize":"32px","color":COLORS["accent3"]}), html.Div(lbl, className="metric-label")]) for k,lbl in [("shipments","Active shipments"),("issues","Open issues"),("customers_saved","Saved customers"),("documents","Documents processed")]]
    return s, cards

@app.callback(Output("rock-module-content", "children"), Input("rock-module-tabs", "value"), Input("rock-customer-dropdown", "value"), Input("rock-scenario-store", "data"), Input("rock-issues-store", "data"), Input("rock-docs-store", "data"), Input("rock-ai-store", "data"))
def render_module(tab, selected_customer, scenario, issues_data, docs_data, ai_rows):
    email = next((c["email"] for c in ROCK_SAVED_CUSTOMERS if c["value"] == selected_customer), "ops@client.com")
    if tab == "shipping":
        q = calc_quote("Dubai", "Fashion Items", 10)
        return html.Div(className="module-card", children=[html.Div("Shipping Calculator", className="story-title"), html.Div("Create a fast shipment estimate using saved customer details, goods type, destination, weight, and service priority.", className="story-copy"), html.Div(className="form-grid-2", children=[html.Div([html.Div("Customer", className="field-label"), dcc.Dropdown(id="calc-customer", options=[{"label": c["label"], "value": c["value"]} for c in ROCK_SAVED_CUSTOMERS], value=selected_customer, clearable=False, style={"color":"#0B1220"}), html.Div("Goods type", className="field-label", style={"marginTop":"12px"}), dcc.Dropdown(id="calc-goods", options=[{"label": k, "value": k} for k in ROCK_GOODS_MULTIPLIERS], value="Fashion Items", clearable=False, style={"color":"#0B1220"}), html.Div("Destination", className="field-label", style={"marginTop":"12px"}), dcc.Dropdown(id="calc-destination", options=[{"label": k, "value": k} for k in ROCK_DESTINATIONS], value="Dubai", clearable=False, style={"color":"#0B1220"}), html.Div(className="form-grid-2", style={"marginTop":"12px"}, children=[html.Div([html.Div("Weight (kg)", className="field-label"), dcc.Input(id="calc-weight", type="number", value=10, style={"width":"100%","padding":"12px","borderRadius":"14px"})]), html.Div([html.Div("Priority", className="field-label"), dcc.Dropdown(id="calc-priority", options=[{"label":"Standard","value":"Standard"},{"label":"Express","value":"Express"}], value="Standard", clearable=False, style={"color":"#0B1220"})])]), html.Button("Generate estimate", id="calc-btn", n_clicks=0, className="action-btn", style={"marginTop":"14px"})]), html.Div([html.Div("Estimate", className="field-label"), html.Div(id="calc-summary", className="summary-box", children=[html.Div(className="summary-line", children=[html.Span("Rate per kg"), html.Strong(f"${q['rate_per_kg']:.2f}")]), html.Div(className="summary-line", children=[html.Span("Base shipping"), html.Strong(f"${q['base_shipping']:.2f}")]), html.Div(className="summary-line", children=[html.Span("Handling"), html.Strong(f"${q['handling']:.2f}")]), html.Div(className="summary-line", children=[html.Span("VAT"), html.Strong(f"${q['vat']:.2f}")]), html.Div(className="summary-line", children=[html.Span("ETA"), html.Strong(q['eta'])]), html.Div(className="summary-line", children=[html.Span("Total estimate"), html.Strong(f"${q['total']:.2f}", style={"fontSize":"28px"})])])])])])
    if tab == "invoice":
        inv = make_invoice(selected_customer, email, "ROA-NEW-001", "Fashion Items", "Lagos", 12, "Standard", False, 0)
        return html.Div(className="module-card", children=[html.Div("Invoice Generator", className="story-title"), html.Div("Build a client-ready invoice using shipment details, service priority, insurance, and optional discount.", className="story-copy"), html.Div(className="form-grid-2", children=[html.Div([html.Div("Customer", className="field-label"), dcc.Dropdown(id="inv-customer", options=[{"label": c["label"], "value": c["value"]} for c in ROCK_SAVED_CUSTOMERS], value=selected_customer, clearable=False, style={"color":"#0B1220"}), html.Div("Customer email", className="field-label", style={"marginTop":"12px"}), dcc.Input(id="inv-email", value=email, type="email", style={"width":"100%","padding":"12px","borderRadius":"14px"}), html.Div("Shipment reference", className="field-label", style={"marginTop":"12px"}), dcc.Input(id="inv-shipment", value="ROA-NEW-001", style={"width":"100%","padding":"12px","borderRadius":"14px"}), html.Div(className="form-grid-4", style={"marginTop":"12px"}, children=[html.Div([html.Div("Goods type", className="field-label"), dcc.Dropdown(id="inv-goods", options=[{"label": k, "value": k} for k in ROCK_GOODS_MULTIPLIERS], value="Fashion Items", clearable=False, style={"color":"#0B1220"})]), html.Div([html.Div("Destination", className="field-label"), dcc.Dropdown(id="inv-destination", options=[{"label": k, "value": k} for k in ROCK_DESTINATIONS], value="Lagos", clearable=False, style={"color":"#0B1220"})]), html.Div([html.Div("Weight", className="field-label"), dcc.Input(id="inv-weight", type="number", value=12, style={"width":"100%","padding":"12px","borderRadius":"14px"})]), html.Div([html.Div("Discount %", className="field-label"), dcc.Input(id="inv-discount", type="number", value=0, style={"width":"100%","padding":"12px","borderRadius":"14px"})])]), html.Div(className="flex-row", style={"marginTop":"14px"}, children=[html.Button("Generate invoice", id="inv-generate-btn", n_clicks=0, className="action-btn"), html.Button("Send to customer", id="inv-send-btn", n_clicks=0, className="secondary-btn")]), html.Div(id="inv-send-status", className="story-copy", style={"marginTop":"8px"})]), html.Div([html.Div("Invoice preview", className="field-label"), html.Div(id="invoice-preview", className="summary-box", children=[html.Div(className="summary-line", children=[html.Span("Invoice number"), html.Strong(inv["invoice_no"])]), html.Div(className="summary-line", children=[html.Span("Customer"), html.Strong(inv["customer"])]), html.Div(className="summary-line", children=[html.Span("Shipment reference"), html.Strong(inv["shipment_ref"])]), html.Div(className="summary-line", children=[html.Span("Due date"), html.Strong(inv["due_date"])]), *[html.Div(className="summary-line", children=[html.Span(it["item"]), html.Strong(f"${it['amount']:,.2f}")]) for it in inv["line_items"]], html.Div(className="summary-line", children=[html.Span("Total due"), html.Strong(f"${inv['total']:,.2f}", style={"fontSize":"28px"})])])])])])
    if tab == "tracking":
        return html.Div(className="module-card", children=[html.Div("Shipment Tracking", className="story-title"), html.Div("View active logistics cases, customer destinations, current status, ETA, and issue notes in one place.", className="story-copy"), dash_table.DataTable(data=ROCK_TRACKING_ROWS, columns=[{"name": k.replace("_"," ").title(), "id": k} for k in ROCK_TRACKING_ROWS[0].keys()], style_cell={"backgroundColor":COLORS["panel"],"color":COLORS["text"],"border":"none","padding":"12px","textAlign":"left"}, style_header={"backgroundColor":COLORS["panel2"],"color":COLORS["text"],"fontWeight":"bold","border":"none"})])
    if tab == "issues":
        cols=[{"name": k.replace("_"," ").title(), "id": k} for k in issues_data[0].keys()]
        return html.Div(className="module-card", children=[html.Div("Missing Goods", className="story-title"), html.Div("Capture issue details, assign ownership, and track the latest customer-facing update.", className="story-copy"), html.Div(className="form-grid-2", children=[html.Div([html.Div("Shipment reference", className="field-label"), dcc.Dropdown(id="issue-shipment", options=[{"label": r["shipment_id"], "value": r["shipment_id"]} for r in ROCK_TRACKING_ROWS], value=ROCK_TRACKING_ROWS[0]["shipment_id"], clearable=False, style={"color":"#0B1220"}), html.Div("Issue description", className="field-label", style={"marginTop":"12px"}), dcc.Input(id="issue-desc", value="1 carton missing", style={"width":"100%","padding":"12px","borderRadius":"14px"}), html.Div(className="form-grid-2", style={"marginTop":"12px"}, children=[html.Div([html.Div("Owner", className="field-label"), dcc.Input(id="issue-owner", value="Fatima", style={"width":"100%","padding":"12px","borderRadius":"14px"})]), html.Div([html.Div("Status", className="field-label"), dcc.Dropdown(id="issue-status", options=[{"label": s, "value": s} for s in ["New","Investigating","Waiting for supplier","Customer updated","Resolved"]], value="Investigating", clearable=False, style={"color":"#0B1220"})])]), html.Div("Latest update", className="field-label", style={"marginTop":"12px"}), dcc.Textarea(id="issue-update", value="Customer informed that container review is in progress.", style={"width":"100%","height":"90px","padding":"12px","borderRadius":"14px"}), html.Button("Add case", id="issue-add-btn", n_clicks=0, className="action-btn", style={"marginTop":"12px"})]), html.Div([dash_table.DataTable(data=issues_data, columns=cols, style_cell={"backgroundColor":COLORS["panel"],"color":COLORS["text"],"border":"none","padding":"12px","textAlign":"left"}, style_header={"backgroundColor":COLORS["panel2"],"color":COLORS["text"],"fontWeight":"bold","border":"none"})])])])
    if tab == "docs":
        cards = docs_data or [{"name":"No document uploaded yet","doc_type":"-","summary":"Upload a bill of lading, invoice copy, manifest, or customs document to see a quick summary here."}]
        return html.Div(className="module-card", children=[html.Div("Document Upload", className="story-title"), html.Div("Collect logistics documents in one place and generate quick summaries for operations follow-up.", className="story-copy"), html.Div(className="form-grid-2", children=[html.Div([html.Div("Document type", className="field-label"), dcc.Dropdown(id="doc-type", options=[{"label": d, "value": d} for d in ROCK_DOC_TYPES], value=ROCK_DOC_TYPES[0], clearable=False, style={"color":"#0B1220"}), html.Div(className="upload-box", style={"marginTop":"12px"}, children=[dcc.Upload(id="doc-upload", children=html.Div(["Drag a file here or click to choose a file"]), multiple=False, style={"padding":"26px 12px"})]), html.Div("Document note", className="field-label", style={"marginTop":"12px"}), dcc.Textarea(id="doc-note", value="Customer invoice received for shipment ROA-24021.", style={"width":"100%","height":"90px","padding":"12px","borderRadius":"14px"})]), html.Div([html.Div(className="summary-box", style={"marginBottom":"10px"}, children=[html.Div(className="summary-line", children=[html.Strong(c["name"]), html.Span(c["doc_type"])]), html.Div(c["summary"], className="story-copy")]) for c in cards])])])
    if tab == "ai":
        return html.Div(className="module-card", children=[html.Div("AI Assistant", className="story-title"), html.Div("Use a business-friendly assistant to draft shipment updates, explain charges, summarize missing-goods next steps, and translate operational details into clear customer language.", className="story-copy"), html.Div(id="rock-ai-chat", children=[html.Div(className="summary-box", style={"marginBottom":"10px"}, children=[html.Div(msg["role"].title(), className="field-label"), html.Div(msg["text"], className="story-copy")]) for msg in ai_rows]), dcc.Textarea(id="rock-ai-input", value="", placeholder="Ask about a shipment, invoice, customer message, missing-goods case, or uploaded document...", style={"width":"100%","height":"110px","padding":"12px","borderRadius":"14px","marginTop":"12px"}), html.Div(className="flex-row", style={"marginTop":"12px"}, children=[html.Button("Ask assistant", id="rock-ai-send-btn", n_clicks=0, className="action-btn"), html.Button("Clear chat", id="rock-ai-clear-btn", n_clicks=0, className="secondary-btn")])])
    cfg = ROCK_SCENARIOS[scenario]
    return html.Div(className="module-card", children=[html.Div("Scenario Builder", className="story-title"), html.Div("Show the client how the operation changes under different business conditions while keeping the same Datastruma workspace shell.", className="story-copy"), html.Div(className="form-grid-2", children=[html.Div(className="summary-box", children=[html.Div(className="summary-line", children=[html.Span("Active shipments"), html.Strong(str(cfg["shipments"]))]), html.Div(className="summary-line", children=[html.Span("Open issues"), html.Strong(str(cfg["issues"]))]), html.Div(className="summary-line", children=[html.Span("Documents"), html.Strong(str(cfg["documents"]))]), html.Div(className="summary-line", children=[html.Span("Scenario note"), html.Strong(cfg["badge"])])]), html.Div(className="summary-box", children=[html.Div("How to tell the story", className="field-label"), html.Div("Start with active shipments and open issues, then show how quote speed, customer updates, invoices, and missing-goods visibility behave in this scenario.", className="story-copy")])])])

@app.callback(Output("calc-summary", "children"), Input("calc-btn", "n_clicks"), State("calc-destination", "value"), State("calc-goods", "value"), State("calc-weight", "value"), State("calc-priority", "value"), prevent_initial_call=False)
def calc_summary(n, destination, goods, weight, priority):
    q = calc_quote(destination, goods, weight or 10, priority)
    return [html.Div(className="summary-line", children=[html.Span("Rate per kg"), html.Strong(f"${q['rate_per_kg']:.2f}")]), html.Div(className="summary-line", children=[html.Span("Base shipping"), html.Strong(f"${q['base_shipping']:.2f}")]), html.Div(className="summary-line", children=[html.Span("Handling"), html.Strong(f"${q['handling']:.2f}")]), html.Div(className="summary-line", children=[html.Span("VAT"), html.Strong(f"${q['vat']:.2f}")]), html.Div(className="summary-line", children=[html.Span("ETA"), html.Strong(q['eta'])]), html.Div(className="summary-line", children=[html.Span("Total estimate"), html.Strong(f"${q['total']:.2f}", style={"fontSize":"28px"})])]

@app.callback(Output("invoice-preview", "children"), Output("inv-send-status", "children"), Input("inv-generate-btn", "n_clicks"), Input("inv-send-btn", "n_clicks"), State("inv-customer", "value"), State("inv-email", "value"), State("inv-shipment", "value"), State("inv-goods", "value"), State("inv-destination", "value"), State("inv-weight", "value"), State("inv-discount", "value"), prevent_initial_call=False)
def inv_preview(g, s, customer, email, ship, goods, dest, weight, discount):
    inv = make_invoice(customer, email, ship, goods, dest, weight or 12, "Standard", False, float(discount or 0))
    preview = [html.Div(className="summary-line", children=[html.Span("Invoice number"), html.Strong(inv["invoice_no"])]), html.Div(className="summary-line", children=[html.Span("Customer"), html.Strong(inv["customer"])]), html.Div(className="summary-line", children=[html.Span("Shipment reference"), html.Strong(inv["shipment_ref"])]), html.Div(className="summary-line", children=[html.Span("Due date"), html.Strong(inv["due_date"])]), *[html.Div(className="summary-line", children=[html.Span(it["item"]), html.Strong(f"${it['amount']:,.2f}")]) for it in inv["line_items"]], html.Div(className="summary-line", children=[html.Span("Total due"), html.Strong(f"${inv['total']:,.2f}", style={"fontSize":"28px"})])]
    status = f"Invoice {inv['invoice_no']} generated."
    if ctx.triggered_id == "inv-send-btn": status = f"Invoice {inv['invoice_no']} marked as sent to {email}."
    return preview, status

@app.callback(Output("rock-issues-store", "data"), Input("issue-add-btn", "n_clicks"), State("rock-issues-store", "data"), State("issue-shipment", "value"), State("issue-desc", "value"), State("issue-owner", "value"), State("issue-status", "value"), State("issue-update", "value"), prevent_initial_call=True)
def add_issue(n, rows, shipment, desc, owner, status, update):
    rows = rows or []
    rows.append({"case_id": f"MG-{1040+len(rows)+1}", "shipment_id": shipment, "customer": next((r["customer"] for r in ROCK_TRACKING_ROWS if r["shipment_id"]==shipment), "Unknown"), "issue": desc, "status": status, "owner": owner, "last_update": update})
    return rows

@app.callback(Output("rock-docs-store", "data"), Input("doc-upload", "filename"), State("rock-docs-store", "data"), State("doc-type", "value"), State("doc-note", "value"), prevent_initial_call=True)
def save_doc(filename, rows, doc_type, note):
    rows = rows or []
    if not filename: return rows
    rows.append({"name": filename, "doc_type": doc_type, "summary": f"{doc_type} added. Quick summary: {note}"})
    return rows

@app.callback(Output("rock-ai-store", "data"), Input("rock-ai-send-btn", "n_clicks"), Input("rock-ai-clear-btn", "n_clicks"), State("rock-ai-input", "value"), State("rock-ai-store", "data"), State("rock-scenario-store", "data"), prevent_initial_call=True)
def ai_chat(send, clear, message, rows, scenario):
    if ctx.triggered_id == "rock-ai-clear-btn":
        return [{"role": "assistant", "text": "Chat cleared. Ask about a shipment, invoice, missing goods, customer update, or uploaded document."}]
    rows = rows or []
    if not (message or "").strip(): return rows
    rows.extend([{"role":"user","text":message.strip()}, {"role":"assistant","text":assistant_reply(message, scenario)}])
    return rows

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
