import base64
import hashlib
import io
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html, no_update, dash_table, ctx
from dash.dependencies import ALL
#main code
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

ROCK_CLIENT = {
    "client_name": "Rock of Ages Group",
    "hero_title": "Logistics operations, customer support, invoicing, and document processing in one connected workspace.",
    "hero_subtitle": "A Datastruma client workspace tailored for Rock of Ages Group to handle shipment estimates, invoice creation, shipment status updates, missing-goods follow-up, uploaded logistics documents, and AI-assisted support.",
}

ROCK_SCENARIOS = {
    "Standard Operations": {"shipments": 148, "issues": 2, "customers_saved": 4, "documents": 18, "badge": "Standard flow"},
    "High Shipment Volume": {"shipments": 226, "issues": 7, "customers_saved": 4, "documents": 31, "badge": "Peak volume"},
    "Delayed Shipments": {"shipments": 151, "issues": 11, "customers_saved": 4, "documents": 20, "badge": "Delay pressure"},
    "Invoice Leakage": {"shipments": 141, "issues": 4, "customers_saved": 4, "documents": 17, "badge": "Margin cleanup"},
    "Missing Goods Escalation": {"shipments": 136, "issues": 15, "customers_saved": 4, "documents": 26, "badge": "Issue surge"},
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
    {"case_id": "MG-1041", "shipment_id": "ROA-24020", "customer": "Blue Pearl General Trading", "issue": "2 cartons missing", "status": "Investigating", "priority": "High", "owner": "Fatima", "last_update": "Container checked. Supplier follow-up in progress.", "customer_message": "We are checking the last verified handoff and will send the next update within 24 hours."},
    {"case_id": "MG-1042", "shipment_id": "ROA-24021", "customer": "Al Noor Fashion Hub", "issue": "Damaged package", "status": "Customer updated", "priority": "Medium", "owner": "David", "last_update": "Images received and replacement discussion started.", "customer_message": "We received the images and are reviewing replacement options. We will confirm the next step shortly."},
]


def calc_quote(destination, goods_type, weight, priority="Standard"):
    settings = ROCK_DESTINATIONS[destination]
    goods_mult = ROCK_GOODS_MULTIPLIERS[goods_type]
    priority_mult = 1.18 if priority == "Express" else 1.0
    weight = max(float(weight or 1), 0.1)
    rate_per_kg = settings["rate_per_kg"] * goods_mult * priority_mult
    base_shipping = settings["base_shipping"] * priority_mult
    handling = settings["handling"] + (8 if weight > 25 else 0) + (18 if goods_type == "Electronics" else 0)
    subtotal = (rate_per_kg * weight) + base_shipping + handling
    vat = subtotal * settings["vat_rate"]
    total = subtotal + vat
    eta = settings["eta"] if priority == "Standard" else ("Same day / next day" if destination == "Dubai" else "1-3 days")
    return {
        "rate_per_kg": round(rate_per_kg, 2),
        "base_shipping": round(base_shipping, 2),
        "handling": round(handling, 2),
        "vat": round(vat, 2),
        "total": round(total, 2),
        "eta": eta,
    }


def make_invoice(customer, email, shipment_ref, goods_type, destination, weight, priority, add_insurance, discount_pct):
    quote = calc_quote(destination, goods_type, weight, priority)
    insurance = 25 if add_insurance else 0
    subtotal = quote["total"] + insurance
    discount_amt = subtotal * (float(discount_pct or 0) / 100.0)
    total = subtotal - discount_amt
    line_items = [
        {"item": f"{goods_type} shipment", "amount": quote["base_shipping"] + quote["rate_per_kg"] * float(weight or 0)},
        {"item": "Handling", "amount": quote["handling"]},
        {"item": "VAT", "amount": quote["vat"]},
    ]
    if insurance:
        line_items.append({"item": "Insurance", "amount": insurance})
    if discount_amt:
        line_items.append({"item": f"Discount ({float(discount_pct):.0f}%)", "amount": -discount_amt})
    return {
        "invoice_no": f"INV-{stable_seed(customer, shipment_ref, destination) % 90000 + 10000}",
        "customer": customer,
        "email": email,
        "shipment_ref": shipment_ref,
        "due_date": "2026-05-07",
        "line_items": line_items,
        "total": round(total, 2),
    }


def static_assistant(message, selected_issue=None):
    text = (message or "").lower().strip()
    if not text:
        return "Ask about a shipment, quote, invoice, missing-goods case, customer message, or uploaded document."
    if "how are you" in text:
        return "I am ready to help with shipment estimates, invoice explanations, missing-goods updates, and customer-facing logistics responses."
    if "quote" in text or "calculate" in text or "$10.50" in text or "kg" in text:
        return "For a shipping quote, capture destination, goods type, weight, and priority first. Then show base shipping, handling, VAT, ETA, and final total clearly so the customer sees exactly how the number was built."
    if "invoice" in text or "charge" in text or "billing" in text:
        return "Break the invoice into shipment amount, handling, tax, insurance, and discount. The goal is to make the commercial logic obvious, not just produce a number."
    if "where" in text or "shipment" in text or "tracking" in text or "delivery" in text:
        return "Start with current status, last confirmed handoff, destination, and ETA. Then give one promised next update time so the customer does not feel ignored."
    if "missing" in text or "lost" in text or "damage" in text:
        if selected_issue:
            return f"For case {selected_issue['case_id']}, the safest response is: confirm the issue, name the current investigation step, and promise the next update window. Current status is {selected_issue['status']} and owner is {selected_issue['owner']}."
        return "For missing-goods handling, confirm the shipment reference, isolate the last verified handoff, assign one owner, and send the customer a calm update with a clear next update window."
    if "document" in text or "upload" in text or "pdf" in text or "manifest" in text:
        return "After a document upload, show filename, type, date, a short summary, and what action the team should take next. The point is visible follow-up, not just storage."
    if "customer" in text or "reply" in text or "email" in text:
        return "Write customer updates in simple business English: what is confirmed, what is still being checked, who owns it internally, and when the next update will come."
    return "This workspace is designed to show cleaner logistics operations: faster quoting, clearer invoices, better shipment visibility, stronger issue handling, and less back-and-forth for the customer."


def parse_upload(contents, filename):
    if not contents or not filename:
        return None
    _, content_string = contents.split(",", 1)
    raw = base64.b64decode(content_string)
    ext = filename.lower().split(".")[-1]
    text = ""
    if ext in ["txt", "csv", "json", "md"]:
        text = raw.decode("utf-8", errors="ignore")[:6000]
    elif ext == "pdf":
        text = "PDF uploaded successfully. Full PDF text parsing is not enabled in this static client demo build."
    else:
        text = f"{filename} uploaded successfully."
    return {
        "name": filename,
        "extension": ext,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "size_kb": max(1, round(len(raw) / 1024)),
        "text": text,
    }


def route_pages(pathname):
    return pathname == "/client/rockofages"

app.layout = html.Div(className="page", children=[
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="autoplay-store", data=False),
    dcc.Interval(id="autoplay-interval", interval=850, n_intervals=0, disabled=True),
    dcc.Store(id="rock-module-store", data="shipping"),
    dcc.Store(id="rock-scenario-store", data="Standard Operations"),
    dcc.Store(id="rock-issues-store", data=ROCK_ISSUE_ROWS),
    dcc.Store(id="rock-selected-case-store", data=ROCK_ISSUE_ROWS[0]["case_id"]),
    dcc.Store(id="rock-docs-store", data=[]),
    dcc.Store(id="rock-chat-store", data=[{"role": "assistant", "text": "Welcome to the Rock of Ages client workspace. Ask about shipment estimates, invoices, tracking, missing goods, or uploaded documents."}]),
    html.Div(id="page-router")
])


def build_main_layout():
    return html.Div(children=[
        html.Div(className="hero", children=[
            html.Div([
                html.Img(src=LOGO_SRC, style={"height": "54px", "marginBottom": "12px"}),
                html.Div("demo.datastruma.com", className="eyebrow"),
                html.Div(id="hero-title", className="hero-title"),
                html.Div(id="hero-subtitle", className="hero-copy"),
                html.Div(className="hero-badges", children=[html.Div("Industry-specific scenarios", className="badge"), html.Div("Chaos to resolution slider", className="badge"), html.Div("Plain-English explanations", className="badge")]),
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
                html.Div(style={"marginTop": "14px"}, children=[html.Div("From messy operations to controlled operations", className="field-label"), dcc.Slider(id="scenario-slider", min=0, max=100, step=1, value=100, marks={0: "Messy", 50: "Improving", 100: "Controlled"}, tooltip={"always_visible": False, "placement": "bottom"})]),
            ]),
            html.Div(className="control-card", children=[html.Div("What this page is showing", className="control-title"), html.Div(id="stage-copy", className="story-copy")]),
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


def build_client_layout():
    return html.Div(children=[
        html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "18px"}, children=[
            html.Div("Client workspace: Rock of Ages Group", className="eyebrow"),
            html.A("← Back to main demo", href="/", style={"color": "#9fd8ff", "textDecoration": "none", "fontWeight": "700"}),
        ]),
        html.Div(className="hero", children=[
            html.Div([
                html.Img(src=LOGO_SRC, style={"height": "54px", "marginBottom": "12px"}),
                html.Div("Datastruma for Rock of Ages Group", className="eyebrow"),
                html.Div(ROCK_CLIENT["hero_title"], className="hero-title", style={"fontSize": "46px"}),
                html.Div(ROCK_CLIENT["hero_subtitle"], className="hero-copy"),
                html.Div(className="hero-badges", children=[html.Div("Logistics workspace", className="badge"), html.Div("Client-specific demo", className="badge"), html.Div("Static assistant build", className="badge")]),
                html.Div("Rock of Ages Group handles freight coordination, customer support, invoice processing, customs and delivery follow-up, and issue handling across a growing logistics operation.", className="story-copy", style={"marginTop": "14px"}),
            ]),
            html.Div([
                html.Div("Workspace snapshot", className="control-title"),
                html.Div(id="rock-kpis", style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"}),
            ])
        ]),
        html.Div(className="controls-grid", children=[
            html.Div(className="control-card", children=[
                html.Div("Rock of Ages scenario", className="control-title"),
                html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr", "gap": "12px"}, children=[
                    html.Div([html.Div("Operating mode", className="field-label"), dcc.Dropdown(id="rock-scenario-dropdown", options=[{"label": k, "value": k} for k in ROCK_SCENARIOS.keys()], value="Standard Operations", clearable=False, style={"color": "#0B1220"})]),
                    html.Div([html.Div("Client", className="field-label"), dcc.Dropdown(id="rock-customer-dropdown", options=[{"label": c["label"], "value": c["value"]} for c in ROCK_SAVED_CUSTOMERS], value=ROCK_SAVED_CUSTOMERS[0]["value"], clearable=False, style={"color": "#0B1220"})]),
                    html.Div([html.Div("Workspace note", className="field-label"), html.Div("Built as a clean client-specific Datastruma logistics workspace", className="eyebrow")]),
                ]),
            ]),
            html.Div(className="control-card", children=[html.Div("Business context", className="control-title"), html.Div("Rock of Ages handles freight coordination, customer updates, invoice processing, customs follow-up, and issue handling. This page shows how those day-to-day tasks can sit in one connected client workspace without breaking the main demo page.", className="story-copy")]),
        ]),
        html.Div(style={"display": "grid", "gridTemplateColumns": "270px 1fr", "gap": "16px", "marginTop": "16px"}, children=[
            html.Div(className="control-card", children=[html.Div("Workspace modules", className="control-title"), html.Div(id="rock-nav")]),
            html.Div(id="rock-module-content")
        ]),
        html.Div("Datastruma client workspace • Rock of Ages Group • logistics operations demo", className="footer")
    ])

@app.callback(Output("page-router", "children"), Input("url", "pathname"))
def render_route(pathname):
    return build_client_layout() if pathname == "/client/rockofages" else build_main_layout()

@app.callback(Output("client-dropdown", "options"), Output("client-dropdown", "value"), Input("industry-dropdown", "value"))
def update_client_dropdown(industry_key):
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
    Output("hero-title", "children"), Output("hero-subtitle", "children"), Output("snapshot-grid", "children"),
    Output("stage-badge", "children"), Output("stage-badge", "style"), Output("stage-copy", "children"),
    Output("metric-grid", "children"), Output("insight-grid", "children"), Output("chaos-story", "children"),
    Output("change-list", "children"), Output("owner-impact", "children"), Output("charts-content", "children"),
    Input("industry-dropdown", "value"), Input("client-dropdown", "value"), Input("scenario-slider", "value"), Input("pain-tab", "value"),
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
        charts = html.Div(className="chart-grid", children=[html.Div(className="stack", children=[html.Div(className="chart-panel panel", children=[graph(trend_fig)]), html.Div(className="chart-panel panel", children=[graph(response_fig)])]), html.Div(className="stack", children=[html.Div(className="chart-panel panel", children=[graph(onboarding_fig)]), html.Div(className="chart-panel panel", children=[graph(billing_fig)])])])
    elif tab_value == "backlog":
        charts = html.Div(className="chart-grid", children=[html.Div(className="chart-panel panel", children=[graph(trend_fig)]), html.Div(className="stack", children=[html.Div(className="chart-panel panel", children=[graph(backlog_fig)]), html.Div(className="info-card", children=[html.Div("What this tells the owner", className="info-title"), html.Div("When this number is high, work is waiting longer than it should. That usually means customers feel delay even when the team feels busy all day.", className="info-copy")])])])
    elif tab_value == "onboarding":
        charts = html.Div(className="chart-grid", children=[html.Div(className="chart-panel panel", children=[graph(onboarding_fig)]), html.Div(className="stack", children=[html.Div(className="chart-panel panel", children=[graph(response_fig)]), html.Div(className="info-card", children=[html.Div("What this tells the owner", className="info-title"), html.Div("When this number is high, new people are taking too long to get fully ready. That slows productivity and increases confusion early.", className="info-copy")])])])
    elif tab_value == "billing":
        charts = html.Div(className="chart-grid", children=[html.Div(className="chart-panel panel", children=[graph(billing_fig)]), html.Div(className="stack", children=[html.Div(className="chart-panel panel", children=[graph(response_fig)]), html.Div(className="info-card", children=[html.Div("What this tells the owner", className="info-title"), html.Div("When this number is high, valid charges or revenue are quietly being missed. The business did the work but did not collect all the money it should have.", className="info-copy")])])])
    else:
        charts = html.Div(className="chart-grid", children=[html.Div(className="chart-panel panel", children=[graph(manual_fig)]), html.Div(className="stack", children=[html.Div(className="chart-panel panel", children=[graph(response_fig)]), html.Div(className="info-card", children=[html.Div("What this tells the owner", className="info-title"), html.Div("When this number is high, skilled people are spending too much time coordinating, checking, correcting, and chasing — instead of moving work forward.", className="info-copy")])])])
    return cfg["headline"], cfg["subheadline"], snapshot_cards, stage, stage_style, stage_copy(alpha), metric_cards, insight_cards, cfg["chaos_story"], html.Ul([html.Li(x) for x in stage_changes(alpha)], style={"margin": "0", "paddingLeft": "18px", "lineHeight": "1.85", "color": COLORS["muted"]}), cfg["owner_impact"], charts

@app.callback(Output("rock-kpis", "children"), Input("rock-scenario-dropdown", "value"))
def rock_kpis(scenario):
    cfg = ROCK_SCENARIOS[scenario]
    cards = []
    for n, l in [(cfg["shipments"], "Active shipments"), (cfg["issues"], "Open issues"), (cfg["customers_saved"], "Saved customers"), (cfg["documents"], "Documents processed")]:
        cards.append(html.Div(style={"padding": "18px", "border": "1px solid rgba(255,255,255,0.06)", "borderRadius": "18px", "background": "rgba(255,255,255,0.03)"}, children=[html.Div(str(n), style={"fontSize": "28px", "fontWeight": "800", "color": COLORS["accent3"]}), html.Div(l, style={"marginTop": "6px"})]))
    return cards

@app.callback(Output("rock-nav", "children"), Input("rock-module-store", "data"))
def rock_nav(active):
    mods = [
        ("shipping", "Shipping Calculator", "Create fast, customer-ready estimates."),
        ("invoice", "Invoice Generator", "Generate a clean invoice breakdown."),
        ("tracking", "Shipment Tracking", "View shipment status and blockers."),
        ("missing", "Missing Goods", "Handle claims and customer updates cleanly."),
        ("documents", "Document Upload", "Upload and summarize logistics docs."),
        ("assistant", "AI Assistant", "Use a built-in static assistant."),
        ("scenario", "Scenario Builder", "Show alternate operating conditions."),
    ]
    return html.Div([html.Div(id={"type": "modbtn", "index": k}, n_clicks=0, style={"padding": "14px 16px", "marginBottom": "10px", "borderRadius": "18px", "cursor": "pointer", "outline": "2px solid rgba(83,199,255,0.45)" if active == k else "none", "background": "linear-gradient(90deg, rgba(83,199,255,0.12), rgba(123,140,255,0.12))" if active == k else "rgba(255,255,255,0.02)", "border": "1px solid rgba(255,255,255,0.06)"}, children=[html.Div(label, style={"fontWeight": "800", "fontSize": "15px"}), html.Div(sub, style={"fontSize": "12px", "color": COLORS["muted"], "marginTop": "4px"})]) for k, label, sub in mods])

@app.callback(Output("rock-module-store", "data"), Input({"type": "modbtn", "index": ALL}, "n_clicks"), State("rock-module-store", "data"), prevent_initial_call=True)
def switch_mod(clicks, current):
    trig = ctx.triggered_id
    return trig["index"] if trig else current

@app.callback(Output("rock-selected-case-store", "data"), Input({"type": "casepick", "index": ALL}, "n_clicks"), State("rock-selected-case-store", "data"), prevent_initial_call=True)
def select_case(clicks, current):
    trig = ctx.triggered_id
    return trig["index"] if trig else current

@app.callback(Output("rock-issues-store", "data", allow_duplicate=True), Output("rock-selected-case-store", "data", allow_duplicate=True), Input("issue-add-btn", "n_clicks"), State("rock-issues-store", "data"), State("issue-shipment", "value"), State("issue-desc", "value"), State("issue-owner", "value"), State("issue-status", "value"), State("issue-priority", "value"), State("issue-update", "value"), prevent_initial_call=True)
def add_case(n, rows, shipment, desc, owner, status, priority, update):
    rows = rows or []
    customer = next((r["customer"] for r in ROCK_TRACKING_ROWS if r["shipment_id"] == shipment), "Unknown")
    case = {"case_id": f"MG-{1040 + len(rows) + 1}", "shipment_id": shipment, "customer": customer, "issue": desc, "status": status, "priority": priority, "owner": owner, "last_update": update, "customer_message": "We have logged your issue and our team is reviewing the latest confirmed handoff. We will send the next update shortly."}
    rows.append(case)
    return rows, case["case_id"]

@app.callback(Output("rock-issues-store", "data"), Output("issue-status-output", "children"), Input("issue-save-btn", "n_clicks"), State("rock-issues-store", "data"), State("rock-selected-case-store", "data"), State("edit-issue", "value"), State("edit-status", "value"), State("edit-message", "value"), State("edit-update", "value"), prevent_initial_call=True)
def save_case(n, rows, selected, issue, status, message, update):
    out = "Case updated."
    new = []
    for row in rows:
        if row["case_id"] == selected:
            row = dict(row)
            row["issue"] = issue
            row["status"] = status
            row["customer_message"] = message
            row["last_update"] = update
        new.append(row)
    return new, out

@app.callback(Output("rock-docs-store", "data"), Output("doc-upload-status", "children"), Input("doc-upload", "contents"), State("doc-upload", "filename"), State("doc-type", "value"), State("doc-note", "value"), State("rock-docs-store", "data"), prevent_initial_call=True)
def upload_doc(contents, filename, doc_type, note, rows):
    rows = rows or []
    parsed = parse_upload(contents, filename)
    if not parsed:
        return rows, "No file received."
    summary = f"{doc_type} added. {note}"
    if parsed["text"]:
        summary += f" Preview: {parsed['text'][:180]}"
    rows.append({"name": parsed["name"], "doc_type": doc_type, "uploaded_at": parsed["uploaded_at"], "size_kb": parsed["size_kb"], "summary": summary})
    return rows, f"{filename} uploaded successfully."

@app.callback(Output("rock-chat-store", "data"), Input("chat-send-btn", "n_clicks"), Input("chat-clear-btn", "n_clicks"), State("chat-input", "value"), State("rock-chat-store", "data"), State("rock-issues-store", "data"), State("rock-selected-case-store", "data"), prevent_initial_call=True)
def update_chat(send_clicks, clear_clicks, message, rows, issues, selected_id):
    if ctx.triggered_id == "chat-clear-btn":
        return [{"role": "assistant", "text": "Welcome to the Rock of Ages client workspace. Ask about shipment estimates, invoices, tracking, missing goods, or uploaded documents."}]
    rows = rows or []
    selected_issue = next((r for r in (issues or []) if r["case_id"] == selected_id), None)
    reply = static_assistant(message, selected_issue)
    return rows + [{"role": "user", "text": message}, {"role": "assistant", "text": reply}]

@app.callback(Output("rock-module-content", "children"), Input("rock-module-store", "data"), Input("rock-customer-dropdown", "value"), Input("rock-scenario-dropdown", "value"), Input("rock-issues-store", "data"), Input("rock-selected-case-store", "data"), Input("rock-docs-store", "data"), Input("rock-chat-store", "data"))
def render_rock_module(module, customer, scenario, issues, selected_case_id, docs, chat_rows):
    customer_email = next((c["email"] for c in ROCK_SAVED_CUSTOMERS if c["value"] == customer), ROCK_SAVED_CUSTOMERS[0]["email"])
    if module == "shipping":
        q = calc_quote("Dubai", "Fashion Items", 10)
        return html.Div(className="control-card", children=[html.Div("Shipping Calculator", className="story-title"), html.Div("Create a fast, customer-ready estimate with clear commercial logic.", className="story-copy"), html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "14px", "marginTop": "14px"}, children=[html.Div([
            html.Div("Saved customer", className="field-label"), dcc.Dropdown(id="calc-customer", options=[{"label": c["label"], "value": c["value"]} for c in ROCK_SAVED_CUSTOMERS], value=customer, clearable=False, style={"color": "#0B1220"}),
            html.Div("Customer email", className="field-label", style={"marginTop": "12px"}), dcc.Input(id="calc-email", value=customer_email, style={"width": "100%", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"}),
            html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px", "marginTop": "12px"}, children=[
                html.Div([html.Div("Goods type", className="field-label"), dcc.Dropdown(id="calc-goods", options=[{"label": k, "value": k} for k in ROCK_GOODS_MULTIPLIERS.keys()], value="Fashion Items", clearable=False, style={"color": "#0B1220"})]),
                html.Div([html.Div("Destination", className="field-label"), dcc.Dropdown(id="calc-destination", options=[{"label": k, "value": k} for k in ROCK_DESTINATIONS.keys()], value="Dubai", clearable=False, style={"color": "#0B1220"})]),
            ]),
            html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px", "marginTop": "12px"}, children=[
                html.Div([html.Div("Weight (kg)", className="field-label"), dcc.Input(id="calc-weight", type="number", value=10, style={"width": "100%", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"})]),
                html.Div([html.Div("Priority", className="field-label"), dcc.Dropdown(id="calc-priority", options=[{"label": "Standard", "value": "Standard"}, {"label": "Express", "value": "Express"}], value="Standard", clearable=False, style={"color": "#0B1220"})]),
            ]),
            html.Button("Generate estimate", id="calc-btn", className="action-btn", n_clicks=0, style={"marginTop": "14px"})
        ]), html.Div(id="calc-summary", children=[
            html.Div(style={"padding": "14px", "background": "rgba(255,255,255,0.03)", "borderRadius": "18px", "border": "1px solid rgba(255,255,255,0.08)"}, children=[
                html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span("Rate per kg"), html.Strong(f"${q['rate_per_kg']:.2f}")]),
                html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span("Base shipping"), html.Strong(f"${q['base_shipping']:.2f}")]),
                html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span("Handling"), html.Strong(f"${q['handling']:.2f}")]),
                html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span("VAT"), html.Strong(f"${q['vat']:.2f}")]),
                html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span("ETA"), html.Strong(q['eta'])]),
                html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0", "fontSize": "26px", "fontWeight": "800"}, children=[html.Span("Total estimate"), html.Strong(f"${q['total']:.2f}")]),
            ])
        ])])])
    if module == "invoice":
        return html.Div(className="control-card", children=[html.Div("Invoice Generator", className="story-title"), html.Div("Turn shipment details into a clean invoice breakdown.", className="story-copy"), html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "14px", "marginTop": "14px"}, children=[html.Div([
            html.Div("Customer", className="field-label"), dcc.Dropdown(id="inv-customer", options=[{"label": c["label"], "value": c["value"]} for c in ROCK_SAVED_CUSTOMERS], value=customer, clearable=False, style={"color": "#0B1220"}),
            html.Div("Customer email", className="field-label", style={"marginTop": "12px"}), dcc.Input(id="inv-email", value=customer_email, style={"width": "100%", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"}),
            html.Div("Shipment reference", className="field-label", style={"marginTop": "12px"}), dcc.Input(id="inv-shipment", value="ROA-NEW-001", style={"width": "100%", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"}),
            html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px", "marginTop": "12px"}, children=[
                html.Div([html.Div("Goods type", className="field-label"), dcc.Dropdown(id="inv-goods", options=[{"label": k, "value": k} for k in ROCK_GOODS_MULTIPLIERS.keys()], value="Fashion Items", clearable=False, style={"color": "#0B1220"})]),
                html.Div([html.Div("Destination", className="field-label"), dcc.Dropdown(id="inv-destination", options=[{"label": k, "value": k} for k in ROCK_DESTINATIONS.keys()], value="Lagos", clearable=False, style={"color": "#0B1220"})]),
            ]),
            html.Div(style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": "12px", "marginTop": "12px"}, children=[
                html.Div([html.Div("Weight (kg)", className="field-label"), dcc.Input(id="inv-weight", type="number", value=12, style={"width": "100%", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"})]),
                html.Div([html.Div("Priority", className="field-label"), dcc.Dropdown(id="inv-priority", options=[{"label": "Standard", "value": "Standard"}, {"label": "Express", "value": "Express"}], value="Standard", clearable=False, style={"color": "#0B1220"})]),
                html.Div([html.Div("Insurance", className="field-label"), dcc.Dropdown(id="inv-insurance", options=[{"label": "No", "value": "No"}, {"label": "Yes", "value": "Yes"}], value="No", clearable=False, style={"color": "#0B1220"})]),
                html.Div([html.Div("Discount %", className="field-label"), dcc.Input(id="inv-discount", type="number", value=0, style={"width": "100%", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"})]),
            ]),
            html.Div(style={"display": "flex", "gap": "12px", "marginTop": "14px"}, children=[html.Button("Generate invoice", id="inv-btn", className="action-btn", n_clicks=0), html.Div(id="inv-status", style={"alignSelf": "center", "color": COLORS["muted"]})])
        ]), html.Div(id="inv-preview")])])
    if module == "tracking":
        df = pd.DataFrame(ROCK_TRACKING_ROWS)
        return html.Div(className="control-card", children=[html.Div("Shipment Tracking", className="story-title"), html.Div("View shipment status and blockers in one place.", className="story-copy"), dash_table.DataTable(data=ROCK_TRACKING_ROWS, columns=[{"name": c.replace("_", " ").title(), "id": c} for c in df.columns], style_as_list_view=True, style_table={"overflowX": "auto", "marginTop": "14px"}, style_cell={"backgroundColor": COLORS["panel"], "color": COLORS["text"], "border": "none", "padding": "12px", "textAlign": "left"}, style_header={"backgroundColor": COLORS["panel2"], "color": COLORS["text"], "fontWeight": "bold", "border": "none"}, page_size=8)])
    if module == "missing":
        selected = next((r for r in issues if r["case_id"] == selected_case_id), issues[0])
        return html.Div(className="control-card", children=[html.Div("Missing Goods", className="story-title"), html.Div("Handle claims and customer updates in a clearer workflow.", className="story-copy"), html.Div(style={"display": "grid", "gridTemplateColumns": "320px 1fr", "gap": "16px", "marginTop": "14px"}, children=[
            html.Div([
                html.Div([html.Div(r["case_id"], style={"fontWeight": "800"}), html.Div(r["customer"], style={"marginTop": "6px"}), html.Div(r["issue"], style={"color": COLORS["muted"], "marginTop": "6px"})], id={"type": "casepick", "index": r["case_id"]}, n_clicks=0, style={"padding": "14px", "marginBottom": "10px", "cursor": "pointer", "borderRadius": "16px", "background": "rgba(255,255,255,0.03)", "outline": "2px solid rgba(83,199,255,0.45)" if r["case_id"] == selected_case_id else "none", "border": "1px solid rgba(255,255,255,0.06)"}) for r in issues
            ]),
            html.Div([
                html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"}, children=[html.Div([html.Div("Issue", className="field-label"), dcc.Input(id="edit-issue", value=selected["issue"], style={"width": "100%", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"})]), html.Div([html.Div("Status", className="field-label"), dcc.Dropdown(id="edit-status", options=[{"label": s, "value": s} for s in ["New", "Investigating", "Waiting for supplier", "Customer updated", "Resolved"]], value=selected["status"], clearable=False, style={"color": "#0B1220"})])]),
                html.Div("Internal update", className="field-label", style={"marginTop": "12px"}), dcc.Textarea(id="edit-update", value=selected["last_update"], style={"width": "100%", "height": "110px", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"}),
                html.Div("Customer message", className="field-label", style={"marginTop": "12px"}), dcc.Textarea(id="edit-message", value=selected["customer_message"], style={"width": "100%", "height": "110px", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"}),
                html.Div(style={"display": "flex", "gap": "12px", "marginTop": "12px"}, children=[html.Button("Save case updates", id="issue-save-btn", className="action-btn", n_clicks=0), html.Div(id="issue-status-output", style={"alignSelf": "center", "color": COLORS["muted"]})]),
                html.Hr(style={"borderColor": "rgba(255,255,255,0.08)", "margin": "20px 0"}),
                html.Div("Add new issue", className="field-label"),
                dcc.Dropdown(id="issue-shipment", options=[{"label": r["shipment_id"], "value": r["shipment_id"]} for r in ROCK_TRACKING_ROWS], value=ROCK_TRACKING_ROWS[0]["shipment_id"], clearable=False, style={"color": "#0B1220"}),
                dcc.Input(id="issue-desc", value="1 carton missing", style={"width": "100%", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white", "marginTop": "12px"}),
                html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr", "gap": "12px", "marginTop": "12px"}, children=[dcc.Input(id="issue-owner", value="Fatima", style={"width": "100%", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"}), dcc.Dropdown(id="issue-status", options=[{"label": s, "value": s} for s in ["New", "Investigating", "Waiting for supplier", "Customer updated", "Resolved"]], value="Investigating", clearable=False, style={"color": "#0B1220"}), dcc.Dropdown(id="issue-priority", options=[{"label": s, "value": s} for s in ["Low", "Medium", "High", "Critical"]], value="High", clearable=False, style={"color": "#0B1220"})]),
                dcc.Textarea(id="issue-update", value="Customer informed that container review is in progress.", style={"width": "100%", "height": "100px", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white", "marginTop": "12px"}),
                html.Button("Add case", id="issue-add-btn", className="action-btn", n_clicks=0, style={"marginTop": "12px"})
            ])
        ])])
    if module == "documents":
        cards = docs or []
        return html.Div(className="control-card", children=[html.Div("Document Upload", className="story-title"), html.Div("Upload logistics documents and make the follow-up visible.", className="story-copy"), html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "14px", "marginTop": "14px"}, children=[
            html.Div([
                html.Div("Document type", className="field-label"), dcc.Dropdown(id="doc-type", options=[{"label": d, "value": d} for d in ["Invoice Copy", "Bill of Lading", "Goods Manifest", "Customer ID", "Customs Document", "Packing List"]], value="Invoice Copy", clearable=False, style={"color": "#0B1220"}),
                html.Div(style={"marginTop": "12px", "border": "1px dashed rgba(255,255,255,0.22)", "background": "rgba(255,255,255,0.02)", "borderRadius": "18px", "padding": "28px 20px", "textAlign": "center"}, children=[dcc.Upload(id="doc-upload", children=html.Div(["Drag a file here or click to choose a file"]), multiple=False)]),
                html.Div("Document note", className="field-label", style={"marginTop": "12px"}), dcc.Textarea(id="doc-note", value="Customer invoice received for shipment ROA-24021.", style={"width": "100%", "height": "110px", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white"}),
                html.Div(id="doc-upload-status", style={"marginTop": "12px", "color": COLORS["muted"]})
            ]),
            html.Div([
                html.Div("Uploaded documents", className="field-label"),
                html.Div([html.Div(style={"padding": "14px", "border": "1px solid rgba(255,255,255,0.08)", "borderRadius": "18px", "background": "rgba(255,255,255,0.03)", "marginBottom": "10px"}, children=[html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[html.Strong(card["name"]), html.Span(card["doc_type"])]), html.Div(f"Size: {card['size_kb']} KB • Uploaded: {card['uploaded_at']}", style={"fontSize": "12px", "color": COLORS["muted"], "marginTop": "4px"}), html.Div(card["summary"], style={"marginTop": "8px", "lineHeight": "1.6"})]) for card in cards] if cards else [html.Div("No document uploaded yet.", style={"color": COLORS["muted"]})])
            ])
        ])])
    if module == "assistant":
        return html.Div(className="control-card", children=[html.Div("AI Assistant", className="story-title"), html.Div("Use the built-in static assistant to answer common logistics questions in a clean client demo flow.", className="story-copy"), html.Div([html.Div(style={"padding": "14px 16px", "borderRadius": "18px", "background": "rgba(255,255,255,0.03)", "border": "1px solid rgba(255,255,255,0.08)", "marginTop": "12px"}, children=[html.Div(r["role"].upper(), style={"fontSize": "12px", "letterSpacing": "0.12em", "color": COLORS["muted"], "marginBottom": "6px"}), html.Div(r["text"], style={"lineHeight": "1.7"})]) for r in chat_rows]), dcc.Textarea(id="chat-input", placeholder="Ask about a shipment, invoice, customer message, missing-goods case, or uploaded document...", style={"width": "100%", "height": "110px", "padding": "12px", "borderRadius": "14px", "border": "1px solid #d9e1ef", "background": "white", "marginTop": "12px"}), html.Div(style={"display": "flex", "justifyContent": "space-between", "marginTop": "12px"}, children=[html.Button("Ask assistant", id="chat-send-btn", className="action-btn", n_clicks=0), html.Button("Clear chat", id="chat-clear-btn", className="action-btn", n_clicks=0, style={"background": "rgba(255,255,255,0.02)", "border": "1px solid rgba(255,255,255,0.12)"})])])
    return html.Div(className="control-card", children=[html.Div("Scenario Builder", className="story-title"), html.Div("Show the client how the same workspace behaves under different business conditions.", className="story-copy"), html.Div(style={"marginTop": "14px", "padding": "14px", "borderRadius": "18px", "background": "rgba(255,255,255,0.03)", "border": "1px solid rgba(255,255,255,0.08)"}, children=[html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span("Scenario"), html.Strong(scenario)]), html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span("Active shipments"), html.Strong(str(ROCK_SCENARIOS[scenario]['shipments']))]), html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span("Open issues"), html.Strong(str(ROCK_SCENARIOS[scenario]['issues']))]), html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span("Story angle"), html.Strong(ROCK_SCENARIOS[scenario]['badge'])])])])

@app.callback(Output("calc-summary", "children"), Input("calc-btn", "n_clicks"), State("calc-destination", "value"), State("calc-goods", "value"), State("calc-weight", "value"), State("calc-priority", "value"), prevent_initial_call=False)
def calc_summary(n, dest, goods, weight, priority):
    q = calc_quote(dest, goods, weight, priority)
    return html.Div(style={"padding": "14px", "background": "rgba(255,255,255,0.03)", "borderRadius": "18px", "border": "1px solid rgba(255,255,255,0.08)"}, children=[
        html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span("Rate per kg"), html.Strong(f"${q['rate_per_kg']:.2f}")]),
        html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span("Base shipping"), html.Strong(f"${q['base_shipping']:.2f}")]),
        html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span("Handling"), html.Strong(f"${q['handling']:.2f}")]),
        html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span("VAT"), html.Strong(f"${q['vat']:.2f}")]),
        html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span("ETA"), html.Strong(q['eta'])]),
        html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0", "fontSize": "26px", "fontWeight": "800"}, children=[html.Span("Total estimate"), html.Strong(f"${q['total']:.2f}")]),
    ])

@app.callback(Output("inv-preview", "children"), Output("inv-status", "children"), Input("inv-btn", "n_clicks"), State("inv-customer", "value"), State("inv-email", "value"), State("inv-shipment", "value"), State("inv-goods", "value"), State("inv-destination", "value"), State("inv-weight", "value"), State("inv-priority", "value"), State("inv-insurance", "value"), State("inv-discount", "value"), prevent_initial_call=False)
def inv_preview(n, customer, email, shipment, goods, destination, weight, priority, insurance, discount):
    inv = make_invoice(customer, email, shipment, goods, destination, weight, priority, insurance == "Yes", discount)
    return html.Div(style={"padding": "14px", "background": "rgba(255,255,255,0.03)", "borderRadius": "18px", "border": "1px solid rgba(255,255,255,0.08)"}, children=[
        html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span("Invoice number"), html.Strong(inv["invoice_no"])]),
        html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span("Customer"), html.Strong(inv["customer"])]),
        html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span("Shipment reference"), html.Strong(inv["shipment_ref"])]),
        html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span("Due date"), html.Strong(inv["due_date"])]),
        *[html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0"}, children=[html.Span(item["item"]), html.Strong(f"${item['amount']:,.2f}")]) for item in inv["line_items"]],
        html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "8px 0", "fontSize": "26px", "fontWeight": "800"}, children=[html.Span("Total due"), html.Strong(f"${inv['total']:,.2f}")]),
    ]), f"Invoice {inv['invoice_no']} generated."

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
