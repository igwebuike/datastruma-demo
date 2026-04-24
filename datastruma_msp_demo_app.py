import base64
import hashlib

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html, no_update

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

INDUSTRIES = {
    "msp": {
        "label": "MSP",
        "headline": "See where service operations quietly break — and what better looks like.",
        "subheadline": "A realistic business demo showing how backlog, onboarding delays, missed billing, and manual admin drag hurt service delivery and customer experience.",
        "clients": ["Northwind Dental", "Apex Legal Group", "BrightPath Plumbing", "PrimeCare Clinic", "GreenLine Logistics"],
        "metric_names": {"backlog": "Unresolved service requests", "onboarding": "Average setup delay", "billing": "Daily missed billing", "manual": "Manual coordination time", "response": "Average first response time"},
        "units": {"backlog": "", "onboarding": " hrs", "billing": "$", "manual": " min", "response": " min"},
        "meanings": {
            "backlog": "how many client requests are still waiting to be completed.",
            "onboarding": "how long a new user or employee waits before access and setup are fully done.",
            "billing": "money slipping through because work, licenses, or changes were not billed correctly.",
            "manual": "time staff spend routing work, chasing updates, and handling repetitive admin.",
            "response": "how long clients wait before the team first reacts to a request.",
        },
        "chaos_story": "Requests were landing in different places, handoffs were unclear, routine work was being touched too many times, and billing updates were not always keeping up with service activity.",
        "owner_impact": "When this improves, clients feel faster service, staff recover time, and revenue leakage becomes easier to control.",
        "base": {"backlog": 430, "onboarding": 12.8, "billing": 318, "manual": 228, "response": 45},
        "resolved": {"backlog": 210, "onboarding": 6.8, "billing": 110, "manual": 119, "response": 30},
        "chart_title": "Service operations trend",
    },
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
    "legal": {
        "label": "Legal",
        "headline": "See where case operations slow down — and what better looks like.",
        "subheadline": "A realistic business demo for law firms dealing with request backlog, client intake delays, billing leakage, and manual admin work.",
        "clients": ["Apex Legal Group", "StoneBridge Law", "Harbor Counsel", "Crestview Litigation", "North Gate Advisory"],
        "metric_names": {"backlog": "Requests still waiting", "onboarding": "Client or staff setup delay", "billing": "Daily missed billing", "manual": "Manual admin time", "response": "Average response time"},
        "units": {"backlog": "", "onboarding": " hrs", "billing": "$", "manual": " min", "response": " min"},
        "meanings": {
            "backlog": "how many incoming matters, tasks, or client requests are still waiting to be handled.",
            "onboarding": "how long it takes to fully intake a client or set up a new internal team member.",
            "billing": "money lost when billable work, changes, or follow-up items do not make it cleanly into billing.",
            "manual": "time spent chasing approvals, status updates, intake details, and handoffs.",
            "response": "how long it takes before the firm gives a clear response.",
        },
        "chaos_story": "Intake was inconsistent, updates lived in emails, work moved through too many manual checkpoints, and some billable items were captured late or not at all.",
        "owner_impact": "When this improves, client communication feels stronger, admin drag drops, and more earned revenue is captured.",
        "base": {"backlog": 290, "onboarding": 10.5, "billing": 248, "manual": 210, "response": 31},
        "resolved": {"backlog": 135, "onboarding": 5.4, "billing": 96, "manual": 114, "response": 18},
        "chart_title": "Firm operations trend",
    },
    "professional_services": {
        "label": "Professional Services",
        "headline": "See where work coordination breaks — and what better looks like.",
        "subheadline": "A realistic business demo for consulting and service firms dealing with backlog, onboarding delays, missed revenue, and manual admin drag.",
        "clients": ["Datastruma Advisory", "Summit Strategy", "BlueRiver Consulting", "Northstar Creative", "Vertex Business Services"],
        "metric_names": {"backlog": "Work items still waiting", "onboarding": "New team setup delay", "billing": "Daily missed revenue", "manual": "Manual admin time", "response": "Average response time"},
        "units": {"backlog": "", "onboarding": " hrs", "billing": "$", "manual": " min", "response": " min"},
        "meanings": {
            "backlog": "how many active tasks or requests are waiting because work is not flowing cleanly.",
            "onboarding": "how long it takes to get a new team member fully ready to work.",
            "billing": "revenue lost when time, change requests, or work completion are not captured properly.",
            "manual": "time spent coordinating work manually instead of delivering value.",
            "response": "how long clients wait before getting a real answer.",
        },
        "chaos_story": "Work updates were fragmented, ownership was not always clear, setup tasks dragged, and too much admin time was spent stitching processes together.",
        "owner_impact": "When this improves, the firm feels more organized, delivery speeds up, and revenue becomes easier to trust.",
        "base": {"backlog": 240, "onboarding": 9.8, "billing": 221, "manual": 198, "response": 29},
        "resolved": {"backlog": 110, "onboarding": 5.1, "billing": 88, "manual": 102, "response": 16},
        "chart_title": "Service firm operations trend",
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
    "shipping": {
        "label": "Shipping",
        "headline": "See where shipping operations lose control — and what better looks like.",
        "subheadline": "A realistic business demo for shipping operators dealing with container or shipment backlog, onboarding delays, missed charges, and manual coordination overload.",
        "clients": ["BlueHarbor Shipping", "Meridian Port Services", "GulfWave Shipping", "AnchorLine Cargo", "OceanBridge Forwarding"],
        "metric_names": {"backlog": "Shipments still waiting", "onboarding": "Operations setup delay", "billing": "Daily missed charges", "manual": "Manual coordination time", "response": "Average customer update time"},
        "units": {"backlog": "", "onboarding": " hrs", "billing": "$", "manual": " min", "response": " min"},
        "meanings": {
            "backlog": "how many shipments, exceptions, or release-related tasks are still waiting to move forward.",
            "onboarding": "how long it takes to get a new team member fully working across shipping systems and procedures.",
            "billing": "money missed when detention, storage, route changes, or extra handling are not captured properly.",
            "manual": "time spent coordinating releases, status updates, paperwork corrections, and customer follow-up.",
            "response": "how long customers wait before receiving a useful update on shipment movement.",
        },
        "chaos_story": "Containers and shipment exceptions were getting stuck in manual follow-up, updates lived across calls and spreadsheets, and extra charges were easy to miss when the team was under pressure.",
        "owner_impact": "When this improves, fewer shipments stall, customers feel more informed, and the operation loses less money to missed charges.",
        "base": {"backlog": 690, "onboarding": 17.1, "billing": 710, "manual": 338, "response": 58},
        "resolved": {"backlog": 320, "onboarding": 8.9, "billing": 272, "manual": 171, "response": 31},
        "chart_title": "Shipping operations trend",
    },
    "courier": {
        "label": "Courier",
        "headline": "See where courier operations fall behind — and what better looks like.",
        "subheadline": "A realistic business demo for courier and last-mile operators dealing with parcel backlog, driver onboarding delays, missed billing, and manual dispatch overload.",
        "clients": ["SwiftDrop Courier", "MetroDash Express", "QuickRoute Delivery", "CityTrack Couriers", "GulfSprint Last Mile"],
        "metric_names": {"backlog": "Deliveries still waiting", "onboarding": "Driver setup delay", "billing": "Daily missed revenue", "manual": "Dispatch and admin time", "response": "Average customer update time"},
        "units": {"backlog": "", "onboarding": " hrs", "billing": "$", "manual": " min", "response": " min"},
        "meanings": {
            "backlog": "how many deliveries are still waiting because routing, exceptions, or proof-of-delivery issues are slowing the flow down.",
            "onboarding": "how long it takes to fully get a new driver or coordinator ready to operate.",
            "billing": "revenue missed when failed delivery fees, route changes, or extra handling are not captured properly.",
            "manual": "time spent rerouting drivers, handling delivery exceptions, chasing proof of delivery, and updating customers.",
            "response": "how long customers wait before they get a clear delivery update.",
        },
        "chaos_story": "Route changes were being handled manually, delivery exceptions were stacking up, proof-of-delivery follow-up was inconsistent, and dispatch staff were constantly firefighting.",
        "owner_impact": "When this improves, deliveries move with less confusion, drivers lose less time, customer updates improve, and fewer dollars get missed.",
        "base": {"backlog": 540, "onboarding": 11.6, "billing": 355, "manual": 296, "response": 41},
        "resolved": {"backlog": 235, "onboarding": 6.1, "billing": 138, "manual": 149, "response": 21},
        "chart_title": "Courier operations trend",
    },
}

def stable_seed(*parts):
    key = "|".join(str(p) for p in parts)
    return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)

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
            val = max(0.1, (start * weekend_factor * seasonal) + noise)
            vals.append(val)
        raw = np.array(vals)
        ratio = end / max(raw.mean(), 0.1)
        improved = raw * ratio
        return raw, improved

    b0, a0 = series_between(cfg["base"]["backlog"], cfg["resolved"]["backlog"], max(8, cfg["base"]["backlog"] * 0.04))
    b1, a1 = series_between(cfg["base"]["onboarding"], cfg["resolved"]["onboarding"], 0.6)
    b2, a2 = series_between(cfg["base"]["billing"], cfg["resolved"]["billing"], max(18, cfg["base"]["billing"] * 0.07))
    b3, a3 = series_between(cfg["base"]["manual"], cfg["resolved"]["manual"], 12)
    b4, a4 = series_between(cfg["base"]["response"], cfg["resolved"]["response"], 3.5)

    before = pd.DataFrame({"date": dates, "backlog": b0.round(0), "onboarding": b1.round(1), "billing": b2.round(0), "manual": b3.round(0), "response": b4.round(0)})
    after = pd.DataFrame({"date": dates, "backlog": a0.round(0), "onboarding": a1.round(1), "billing": a2.round(0), "manual": a3.round(0), "response": a4.round(0)})
    return before, after

def lerp(a, b, alpha):
    return a + (b - a) * alpha

def interpolate_frame(before_df, after_df, alpha):
    current = before_df.copy()
    for col in ["backlog", "onboarding", "billing", "manual", "response"]:
        current[col] = lerp(before_df[col], after_df[col], alpha)
    return current

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

def stage_copy(alpha):
    if alpha <= 0.15:
        return "The operation is in firefighting mode. Too much is being handled manually, work is stacking up, and customers feel the delay."
    if alpha < 0.85:
        return "The operation is improving. Some bottlenecks are being reduced, but the business is still partway through the clean-up."
    return "The operation is more controlled. Work is moving faster, fewer items are waiting, and more revenue and time are being protected."

def stage_changes(alpha):
    if alpha <= 0.15:
        return [
            "Work is landing in too many places and staff are spending time chasing updates.",
            "Repeated tasks are not standardized, so handoffs take longer than they should.",
            "Important billing details are easier to miss when the team is under pressure.",
            "The business feels busy, but too much of that busyness is manual rework.",
        ]
    if alpha < 0.85:
        return [
            "Ownership is becoming clearer and repeated work is being handled more consistently.",
            "The most common handoffs are being tightened, so delays begin to shrink.",
            "Valid charges and missed revenue are becoming easier to spot.",
            "Manual coordination is dropping, but the business has not fully stabilized yet.",
        ]
    return [
        "Work is routed more clearly, so fewer items sit waiting without action.",
        "Repeated steps are handled in a more repeatable way, reducing delay.",
        "Billing checkpoints catch more missed charges before revenue is lost.",
        "The team spends less time firefighting and more time delivering work cleanly.",
    ]

def format_value(metric_key, value, cfg):
    unit = cfg["units"][metric_key]
    if metric_key == "billing":
        return f"${value:,.0f}"
    if metric_key == "onboarding":
        return f"{value:.1f}{unit}"
    return f"{value:,.0f}{unit}"

def metric_summary_text(metric_key, current_value, chaos_value, resolved_value, cfg):
    return (
        f"{cfg['metric_names'][metric_key]}: {format_value(metric_key, current_value, cfg)}. "
        f"In plain English, this means {cfg['meanings'][metric_key]} "
        f"In the messy state it was {format_value(metric_key, chaos_value, cfg)}. "
        f"In the controlled state it comes down to {format_value(metric_key, resolved_value, cfg)}."
    )

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
    fig.add_trace(go.Bar(
        x=["Messy state", "Current view", "Controlled state"],
        y=[metrics[f"{metric_key}_chaos"], metrics[metric_key], metrics[f"{metric_key}_resolved"]],
        marker_color=[COLORS["danger"], COLORS["warn"], COLORS["accent3"]],
    ))
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

def build_metric_card(label, value, detail, accent):
    return html.Div(className="metric-card", children=[html.Div(label, className="metric-label"), html.Div(value, className="metric-value", style={"color": accent}), html.Div(detail, className="metric-detail")])

def options_for_clients(industry_key):
    return [{"label": c, "value": c} for c in INDUSTRIES[industry_key]["clients"]]

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "Datastruma Demo"

app.index_string = """
<!DOCTYPE html>
<html>
<head>
{%metas%}
<title>{%title%}</title>
{%favicon%}
{%css%}
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root { --text:#F4F7FB; --muted:#93A8C6; --accent:#53C7FF; --accent2:#7B8CFF; --accent3:#78F0A7; --warn:#FFB454; --danger:#FF7A90; }
* { box-sizing:border-box; }
body { margin:0; color:var(--text); font-family:Inter, Arial, sans-serif; background:radial-gradient(circle at top left, rgba(83,199,255,0.12), transparent 28%), radial-gradient(circle at top right, rgba(123,140,255,0.10), transparent 26%), linear-gradient(180deg, #06101d 0%, #071120 100%); }
.page { max-width:1500px; margin:0 auto; padding:20px; }
.panel, .hero, .metric-card, .story-card, .control-card, .info-card { background:linear-gradient(180deg, rgba(16,31,51,0.98), rgba(13,26,43,0.98)); border:1px solid rgba(255,255,255,0.06); box-shadow:0 16px 60px rgba(0,0,0,0.28); border-radius:24px; }
.hero { display:grid; grid-template-columns:1.35fr 0.95fr; gap:18px; padding:24px; }
.hero-title { font-size:56px; line-height:0.95; letter-spacing:-0.04em; margin:8px 0 16px; max-width:950px; }
.hero-copy { color:var(--muted); font-size:18px; line-height:1.65; max-width:860px; }
.eyebrow { display:inline-flex; align-items:center; gap:10px; padding:8px 12px; border-radius:999px; border:1px solid rgba(255,255,255,0.08); background:rgba(255,255,255,0.03); color:var(--muted); font-size:13px; }
.hero-badges { display:flex; flex-wrap:wrap; gap:10px; margin-top:18px; }
.badge { padding:11px 15px; border-radius:999px; border:1px solid rgba(255,255,255,0.08); background:linear-gradient(90deg, rgba(83,199,255,0.16), rgba(123,140,255,0.16)); font-size:13px; font-weight:700; }
.snapshot { display:grid; grid-template-columns:1fr 1fr; gap:12px; align-content:start; }
.snapshot-card { border:1px solid rgba(255,255,255,0.06); border-radius:18px; background:rgba(255,255,255,0.03); padding:16px; }
.snapshot-big { font-size:18px; font-weight:800; margin-bottom:6px; }
.snapshot-small { color:var(--muted); font-size:13px; line-height:1.55; }
.controls-grid { display:grid; grid-template-columns:1.12fr 0.88fr; gap:16px; margin-top:16px; }
.control-card { padding:18px; }
.control-title { font-size:12px; color:var(--muted); text-transform:uppercase; letter-spacing:0.14em; margin-bottom:12px; }
.control-row { display:grid; grid-template-columns:1fr 1fr 1fr auto; gap:12px; align-items:end; }
.field-label { color:var(--muted); font-size:13px; margin-bottom:8px; }
.metric-grid { display:grid; grid-template-columns:repeat(5, 1fr); gap:14px; margin-top:16px; }
.metric-card { padding:18px; }
.metric-label { color:var(--muted); font-size:13px; margin-bottom:12px; }
.metric-value { font-size:36px; font-weight:800; letter-spacing:-0.03em; }
.metric-detail { color:#B1ECC0; font-size:13px; margin-top:8px; line-height:1.55; }
.explain-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:16px; margin-top:16px; }
.story-card, .info-card { padding:18px; }
.story-title, .info-title { font-size:18px; font-weight:800; margin-bottom:8px; }
.story-copy, .info-copy { color:var(--muted); font-size:14px; line-height:1.72; }
.tabs-panel { margin-top:16px; padding:12px; }
.tabs .tab { background:transparent !important; border:none !important; color:var(--muted) !important; padding:16px 18px !important; font-weight:700 !important; border-bottom:2px solid transparent !important; }
.tabs .tab--selected { color:var(--text) !important; border-bottom:2px solid var(--accent) !important; }
.chart-grid { display:grid; grid-template-columns:1.25fr 0.75fr; gap:16px; margin-top:16px; }
.stack { display:grid; gap:16px; }
.chart-panel { padding:14px 14px 6px; }
.insight-grid { display:grid; grid-template-columns:repeat(5, 1fr); gap:14px; margin-top:16px; }
.mini-card { padding:16px; border-radius:18px; border:1px solid rgba(255,255,255,0.06); background:rgba(255,255,255,0.03); }
.mini-title { color:var(--muted); font-size:13px; margin-bottom:8px; }
.mini-copy { font-size:13px; line-height:1.65; color:var(--text); }
.footer { text-align:center; color:var(--muted); font-size:13px; padding:14px 0 28px; }
.action-btn { height:44px; border:none; padding:0 18px; border-radius:14px; background:linear-gradient(90deg, rgba(83,199,255,0.25), rgba(123,140,255,0.25)); color:var(--text); font-weight:800; cursor:pointer; }
@media (max-width:1200px) { .hero, .controls-grid, .chart-grid, .explain-grid { grid-template-columns:1fr; } .metric-grid, .insight-grid { grid-template-columns:1fr 1fr; } .control-row { grid-template-columns:1fr 1fr; } .hero-title { font-size:42px; } }
@media (max-width:760px) { .metric-grid, .insight-grid { grid-template-columns:1fr; } .snapshot { grid-template-columns:1fr; } .control-row { grid-template-columns:1fr; } .page { padding:12px; } }
</style>
</head>
<body>
{%app_entry%}
<footer>
{%config%}
{%scripts%}
{%renderer%}
</footer>
</body>
</html>
"""

app.layout = html.Div(className="page", children=[
    dcc.Store(id="autoplay-store", data=False),
    dcc.Interval(id="autoplay-interval", interval=850, n_intervals=0, disabled=True),
    html.Div(className="hero", children=[
        html.Div([
            html.Img(src=LOGO_SRC, style={"height": "54px", "marginBottom": "12px"}),
            html.Div("demo.datastruma.com", className="eyebrow"),
            html.Div(id="hero-title", className="hero-title"),
            html.Div(id="hero-subtitle", className="hero-copy"),
            html.Div(className="hero-badges", children=[
                html.Div("Industry-specific scenarios", className="badge"),
                html.Div("Chaos to resolution slider", className="badge"),
                html.Div("Plain-English explanations", className="badge"),
            ]),
        ]),
        html.Div([
            html.Div("Executive snapshot", className="control-title"),
            html.Div(id="snapshot-grid", className="snapshot"),
        ]),
    ]),
    html.Div(className="controls-grid", children=[
        html.Div(className="control-card", children=[
            html.Div("Scenario controls", className="control-title"),
            html.Div(className="control-row", children=[
                html.Div([html.Div("Industry", className="field-label"), dcc.Dropdown(id="industry-dropdown", options=[{"label": v["label"], "value": k} for k, v in INDUSTRIES.items()], value="home_services", clearable=False, style={"color": "#0B1220"})]),
                html.Div([html.Div("Company example", className="field-label"), dcc.Dropdown(id="client-dropdown", options=options_for_clients("home_services"), value=INDUSTRIES["home_services"]["clients"][0], clearable=False, style={"color": "#0B1220"})]),
                html.Div([html.Div("Current state", className="field-label"), html.Div(id="stage-badge", className="badge", style={"display": "inline-flex"})]),
                html.Button("Play story", id="play-button", n_clicks=0, className="action-btn"),
            ]),
            html.Div(style={"marginTop": "14px"}, children=[
                html.Div("From messy operations to controlled operations", className="field-label"),
                dcc.Slider(id="scenario-slider", min=0, max=100, step=1, value=100, marks={0: "Messy", 50: "Improving", 100: "Controlled"}, tooltip={"always_visible": False, "placement": "bottom"}),
            ]),
        ]),
        html.Div(className="control-card", children=[
            html.Div("What this page is showing", className="control-title"),
            html.Div(id="stage-copy", className="story-copy"),
        ]),
    ]),
    html.Div(id="metric-grid", className="metric-grid"),
    html.Div(id="insight-grid", className="insight-grid"),
    html.Div(className="explain-grid", children=[
        html.Div([html.Div("What the chaos looked like", className="story-title"), html.Div(id="chaos-story", className="story-copy")], className="story-card"),
        html.Div([html.Div("What changed", className="story-title"), html.Div(id="change-list", className="story-copy")], className="story-card"),
        html.Div([html.Div("Why a business owner should care", className="story-title"), html.Div(id="owner-impact", className="story-copy")], className="story-card"),
    ]),
    html.Div(className="tabs-panel panel", children=[
        dcc.Tabs(id="pain-tab", value="overview", className="tabs", children=[
            dcc.Tab(label="Overview", value="overview", className="tab", selected_className="tab--selected"),
            dcc.Tab(label="Backlog", value="backlog", className="tab", selected_className="tab--selected"),
            dcc.Tab(label="Onboarding", value="onboarding", className="tab", selected_className="tab--selected"),
            dcc.Tab(label="Billing", value="billing", className="tab", selected_className="tab--selected"),
            dcc.Tab(label="Manual Time", value="manual", className="tab", selected_className="tab--selected"),
        ]),
        html.Div(id="charts-content"),
    ]),
    html.Div("Datastruma demo • realistic operating scenarios • plain-English metrics • ready for demo.datastruma.com or /demo", className="footer"),
])

@app.callback(Output("client-dropdown", "options"), Output("client-dropdown", "value"), Input("industry-dropdown", "value"))
def update_client_options(industry_key):
    opts = options_for_clients(industry_key)
    return opts, opts[0]["value"]

@app.callback(Output("autoplay-store", "data"), Output("autoplay-interval", "disabled"), Output("play-button", "children"), Input("play-button", "n_clicks"), State("autoplay-store", "data"), prevent_initial_call=True)
def toggle_autoplay(n_clicks, running):
    new_state = not running
    return new_state, (not new_state), ("Pause story" if new_state else "Play story")

@app.callback(Output("scenario-slider", "value"), Output("autoplay-store", "data", allow_duplicate=True), Output("autoplay-interval", "disabled", allow_duplicate=True), Output("play-button", "children", allow_duplicate=True), Input("autoplay-interval", "n_intervals"), State("scenario-slider", "value"), State("autoplay-store", "data"), prevent_initial_call=True)
def autoplay_step(n, value, running):
    if not running:
        return no_update, no_update, no_update, no_update
    new_value = max(0, int(value) - 5)
    if new_value <= 0:
        return new_value, False, True, "Play story"
    return new_value, True, False, "Pause story"

@app.callback(
    Output("hero-title", "children"),
    Output("hero-subtitle", "children"),
    Output("snapshot-grid", "children"),
    Output("stage-badge", "children"),
    Output("stage-badge", "style"),
    Output("stage-copy", "children"),
    Output("metric-grid", "children"),
    Output("insight-grid", "children"),
    Output("chaos-story", "children"),
    Output("change-list", "children"),
    Output("owner-impact", "children"),
    Output("charts-content", "children"),
    Input("industry-dropdown", "value"),
    Input("client-dropdown", "value"),
    Input("scenario-slider", "value"),
    Input("pain-tab", "value"),
)
def update_page(industry_key, client_name, slider_value, tab_value):
    cfg = INDUSTRIES[industry_key]
    alpha = slider_value / 100.0
    before_df, after_df = generate_data(industry_key, client_name)
    current_df = interpolate_frame(before_df, after_df, alpha)

    metrics = {
        "backlog_chaos": cfg["base"]["backlog"], "backlog_resolved": cfg["resolved"]["backlog"], "backlog": current_df["backlog"].mean(),
        "onboarding_chaos": cfg["base"]["onboarding"], "onboarding_resolved": cfg["resolved"]["onboarding"], "onboarding": current_df["onboarding"].mean(),
        "billing_chaos": cfg["base"]["billing"], "billing_resolved": cfg["resolved"]["billing"], "billing": current_df["billing"].mean(),
        "manual_chaos": cfg["base"]["manual"], "manual_resolved": cfg["resolved"]["manual"], "manual": current_df["manual"].mean(),
        "response_chaos": cfg["base"]["response"], "response_resolved": cfg["resolved"]["response"], "response": current_df["response"].mean(),
    }
    stage = current_stage(alpha)
    color = tone_color(alpha)
    stage_style = {"display": "inline-flex", "background": "rgba(255,255,255,0.05)", "border": f"1px solid {color}", "color": COLORS["text"]}

    snapshot_cards = [
        html.Div([html.Div(f"{((metrics['backlog_chaos'] - metrics['backlog']) / metrics['backlog_chaos']) * 100:.0f}% lower", className="snapshot-big", style={"color": color}), html.Div(f"Lower {cfg['metric_names']['backlog'].lower()} means less work is sitting around waiting.", className="snapshot-small")], className="snapshot-card"),
        html.Div([html.Div(f"{((metrics['onboarding_chaos'] - metrics['onboarding']) / metrics['onboarding_chaos']) * 100:.0f}% faster", className="snapshot-big", style={"color": color}), html.Div(f"Lower {cfg['metric_names']['onboarding'].lower()} means new people become productive faster.", className="snapshot-small")], className="snapshot-card"),
        html.Div([html.Div(f"{((metrics['billing_chaos'] - metrics['billing']) / metrics['billing_chaos']) * 100:.0f}% less missed revenue", className="snapshot-big", style={"color": color}), html.Div(f"Lower {cfg['metric_names']['billing'].lower()} means fewer valid charges are being missed.", className="snapshot-small")], className="snapshot-card"),
        html.Div([html.Div(f"{((metrics['manual_chaos'] - metrics['manual']) / metrics['manual_chaos']) * 100:.0f}% less manual time", className="snapshot-big", style={"color": color}), html.Div(f"Lower {cfg['metric_names']['manual'].lower()} means the team spends less time chasing work.", className="snapshot-small")], className="snapshot-card"),
    ]

    metric_cards = [
        build_metric_card(cfg["metric_names"]["backlog"], format_value("backlog", metrics["backlog"], cfg), f"Messy state {format_value('backlog', metrics['backlog_chaos'], cfg)} → controlled state {format_value('backlog', metrics['backlog_resolved'], cfg)}", color),
        build_metric_card(cfg["metric_names"]["onboarding"], format_value("onboarding", metrics["onboarding"], cfg), f"Messy state {format_value('onboarding', metrics['onboarding_chaos'], cfg)} → controlled state {format_value('onboarding', metrics['onboarding_resolved'], cfg)}", color),
        build_metric_card(cfg["metric_names"]["billing"], format_value("billing", metrics["billing"], cfg), f"Messy state {format_value('billing', metrics['billing_chaos'], cfg)} → controlled state {format_value('billing', metrics['billing_resolved'], cfg)}", color),
        build_metric_card(cfg["metric_names"]["manual"], format_value("manual", metrics["manual"], cfg), f"Messy state {format_value('manual', metrics['manual_chaos'], cfg)} → controlled state {format_value('manual', metrics['manual_resolved'], cfg)}", color),
        build_metric_card(cfg["metric_names"]["response"], format_value("response", metrics["response"], cfg), f"Messy state {format_value('response', metrics['response_chaos'], cfg)} → controlled state {format_value('response', metrics['response_resolved'], cfg)}", color),
    ]

    insight_cards = [
        html.Div([html.Div(cfg["metric_names"]["backlog"], className="mini-title"), html.Div(metric_summary_text("backlog", metrics["backlog"], metrics["backlog_chaos"], metrics["backlog_resolved"], cfg), className="mini-copy")], className="mini-card"),
        html.Div([html.Div(cfg["metric_names"]["onboarding"], className="mini-title"), html.Div(metric_summary_text("onboarding", metrics["onboarding"], metrics["onboarding_chaos"], metrics["onboarding_resolved"], cfg), className="mini-copy")], className="mini-card"),
        html.Div([html.Div(cfg["metric_names"]["billing"], className="mini-title"), html.Div(metric_summary_text("billing", metrics["billing"], metrics["billing_chaos"], metrics["billing_resolved"], cfg), className="mini-copy")], className="mini-card"),
        html.Div([html.Div(cfg["metric_names"]["manual"], className="mini-title"), html.Div(metric_summary_text("manual", metrics["manual"], metrics["manual_chaos"], metrics["manual_resolved"], cfg), className="mini-copy")], className="mini-card"),
        html.Div([html.Div(cfg["metric_names"]["response"], className="mini-title"), html.Div(metric_summary_text("response", metrics["response"], metrics["response_chaos"], metrics["response_resolved"], cfg), className="mini-copy")], className="mini-card"),
    ]

    trend_fig = build_trend_fig(before_df.copy(), after_df.copy(), alpha, cfg)
    onboarding_fig = build_compare_bar("onboarding", metrics, cfg)
    response_fig = build_compare_bar("response", metrics, cfg)
    billing_fig = build_monthly_billing(before_df.copy(), after_df.copy(), alpha)
    manual_fig = build_compare_bar("manual", metrics, cfg)
    backlog_fig = build_compare_bar("backlog", metrics, cfg)

    def graph(fig):
        return dcc.Graph(figure=fig, config={"displayModeBar": False, "showSendToCloud": False, "displaylogo": False}, style={"height": "430px"})

    if tab_value == "overview":
        charts = html.Div(className="chart-grid", children=[
            html.Div(className="stack", children=[html.Div(className="chart-panel panel", children=[graph(trend_fig)]), html.Div(className="chart-panel panel", children=[graph(response_fig)])]),
            html.Div(className="stack", children=[html.Div(className="chart-panel panel", children=[graph(onboarding_fig)]), html.Div(className="chart-panel panel", children=[graph(billing_fig)])]),
        ])
    elif tab_value == "backlog":
        charts = html.Div(className="chart-grid", children=[
            html.Div(className="chart-panel panel", children=[graph(trend_fig)]),
            html.Div(className="stack", children=[html.Div(className="chart-panel panel", children=[graph(backlog_fig)]), html.Div(className="info-card", children=[html.Div("What this tells the owner", className="info-title"), html.Div("When this number is high, work is waiting longer than it should. That usually means customers feel delay even when the team feels busy all day.", className="info-copy")])]),
        ])
    elif tab_value == "onboarding":
        charts = html.Div(className="chart-grid", children=[
            html.Div(className="chart-panel panel", children=[graph(onboarding_fig)]),
            html.Div(className="stack", children=[html.Div(className="chart-panel panel", children=[graph(response_fig)]), html.Div(className="info-card", children=[html.Div("What this tells the owner", className="info-title"), html.Div("When this number is high, new people are taking too long to get fully ready. That slows productivity and increases confusion early.", className="info-copy")])]),
        ])
    elif tab_value == "billing":
        charts = html.Div(className="chart-grid", children=[
            html.Div(className="chart-panel panel", children=[graph(billing_fig)]),
            html.Div(className="stack", children=[html.Div(className="chart-panel panel", children=[graph(response_fig)]), html.Div(className="info-card", children=[html.Div("What this tells the owner", className="info-title"), html.Div("When this number is high, valid charges or revenue are quietly being missed. The business did the work but did not collect all the money it should have.", className="info-copy")])]),
        ])
    else:
        charts = html.Div(className="chart-grid", children=[
            html.Div(className="chart-panel panel", children=[graph(manual_fig)]),
            html.Div(className="stack", children=[html.Div(className="chart-panel panel", children=[graph(response_fig)]), html.Div(className="info-card", children=[html.Div("What this tells the owner", className="info-title"), html.Div("When this number is high, skilled people are spending too much time coordinating, checking, correcting, and chasing — instead of moving work forward.", className="info-copy")])]),
        ])

    return (
        cfg["headline"],
        cfg["subheadline"],
        snapshot_cards,
        stage,
        stage_style,
        stage_copy(alpha),
        metric_cards,
        insight_cards,
        cfg["chaos_story"],
        html.Ul([html.Li(x) for x in stage_changes(alpha)], style={"margin": "0", "paddingLeft": "18px", "lineHeight": "1.85", "color": COLORS["muted"]}),
        cfg["owner_impact"],
        charts,
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
