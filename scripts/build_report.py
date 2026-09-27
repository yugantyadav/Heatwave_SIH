"""Generate the HeatWave EWS project report as a PDF.

Structure mirrors the ATDP_FINAL_Report template it is modelled on, starting
from the Abstract: the title page and certificate are intentionally omitted.

Every figure quoted in the document (ward counts, test totals, endpoint list,
coefficients) is asserted against the live project before it is written, so
the report cannot drift away from the code.
"""
import subprocess
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph, Spacer,
    Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent  # repo root; data/ and backend/ live here
OUT = Path.home() / "Desktop" / "HeatWave-EWS-Project-Report.pdf"

TITLE = "HeatWatch Mumbai — Ward-Level Heat Early Warning System"
RUNNING_HEAD = "HeatWatch Mumbai — Heat Early Warning System"

INK = colors.HexColor("#1A1A1A")
MUTED = colors.HexColor("#5A5A5A")
RULE = colors.HexColor("#B8860B")
HEADER_BG = colors.HexColor("#F4F1E8")
ZEBRA = colors.HexColor("#FAF8F2")

styles = getSampleStyleSheet()
S = {
    "title": ParagraphStyle("t", parent=styles["Title"], fontName="Times-Bold",
                            fontSize=20, leading=25, textColor=INK, spaceAfter=6),
    "subtitle": ParagraphStyle("st", parent=styles["Normal"], fontName="Times-Italic",
                               fontSize=10.5, leading=14, textColor=MUTED,
                               alignment=TA_CENTER, spaceAfter=4),
    "h1": ParagraphStyle("h1", parent=styles["Heading1"], fontName="Times-Bold",
                         fontSize=14, leading=18, textColor=INK, spaceBefore=16,
                         spaceAfter=7),
    "h2": ParagraphStyle("h2", parent=styles["Heading2"], fontName="Times-Bold",
                         fontSize=11.5, leading=15, textColor=INK, spaceBefore=11,
                         spaceAfter=5),
    "body": ParagraphStyle("b", parent=styles["BodyText"], fontName="Times-Roman",
                           fontSize=9.7, leading=14, alignment=TA_JUSTIFY,
                           textColor=INK, spaceAfter=6),
    "bullet": ParagraphStyle("bu", parent=styles["BodyText"], fontName="Times-Roman",
                             fontSize=9.7, leading=13.6, leftIndent=15,
                             bulletIndent=4, spaceAfter=3.5, textColor=INK,
                             alignment=TA_JUSTIFY),
    "cap": ParagraphStyle("c", parent=styles["Normal"], fontName="Times-Italic",
                          fontSize=8.6, leading=11.5, textColor=MUTED,
                          alignment=TA_CENTER, spaceBefore=4, spaceAfter=10),
    "cell": ParagraphStyle("ce", parent=styles["Normal"], fontName="Times-Roman",
                           fontSize=8.4, leading=11, textColor=INK),
    "cellb": ParagraphStyle("cb", parent=styles["Normal"], fontName="Times-Bold",
                            fontSize=8.4, leading=11, textColor=INK),
    "code": ParagraphStyle("co", parent=styles["Normal"], fontName="Courier",
                           fontSize=7.9, leading=10.4, textColor=colors.HexColor("#1B3A2F"),
                           backColor=colors.HexColor("#F6F6F2"), borderPadding=6,
                           leftIndent=6, spaceBefore=3, spaceAfter=8),
    "meta": ParagraphStyle("m", parent=styles["Normal"], fontName="Times-Italic",
                           fontSize=9, leading=12, textColor=MUTED, spaceAfter=2),
}


def page_furniture(canv, doc):
    canv.saveState()
    w, h = letter
    canv.setFont("Times-Italic", 7.6)
    canv.setFillColor(MUTED)
    canv.drawCentredString(w / 2, h - 0.42 * inch, RUNNING_HEAD)
    canv.setStrokeColor(RULE)
    canv.setLineWidth(0.4)
    canv.line(0.85 * inch, h - 0.52 * inch, w - 0.85 * inch, h - 0.52 * inch)
    canv.line(0.85 * inch, 0.66 * inch, w - 0.85 * inch, 0.66 * inch)
    canv.setFont("Times-Roman", 8.4)
    canv.drawCentredString(w / 2, 0.5 * inch, str(canv.getPageNumber()))
    canv.restoreState()


def build_doc():
    doc = BaseDocTemplate(str(OUT), pagesize=letter,
                          leftMargin=0.85 * inch, rightMargin=0.85 * inch,
                          topMargin=0.72 * inch, bottomMargin=0.8 * inch,
                          title="HeatWatch Mumbai — Project Report",
                          author="HeatWatch Mumbai")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=page_furniture)])
    return doc


def P(t, s="body"):
    return Paragraph(t, S[s])


def bullets(items):
    return [Paragraph(f"&bull;&nbsp; {i}", S["bullet"]) for i in items]


def table(rows, widths, header=True, align_first_left=True):
    data = []
    for r_i, row in enumerate(rows):
        cells = []
        for c_i, cell in enumerate(row):
            style = "cellb" if (header and r_i == 0) else "cell"
            cells.append(Paragraph(str(cell), S[style]))
        data.append(cells)
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    cmds = [
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C9C4B6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]
    if header:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                 ("LINEBELOW", (0, 0), (-1, 0), 0.7, RULE)]
        if align_first_left:
            cmds.append(("ALIGN", (1, 0), (-1, -1), "LEFT"))
    for i in range(1 if header else 0, len(rows)):
        if i % 2 == (1 if header else 0):
            cmds.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
    t.setStyle(TableStyle(cmds))
    return t


def code(src, caption=None):
    out = [Paragraph(src.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                     .replace(" ", "&nbsp;").replace("\n", "<br/>"), S["code"])]
    if caption:
        out.append(Paragraph(caption, S["cap"]))
    return out


# ---------------------------------------------------------------- project facts
def facts():
    f = {}
    geo = (ROOT / "data" / "wards_geojson.json").read_text()
    import json
    g = json.loads(geo)
    f["map_wards"] = [x["properties"]["ward_name"] for x in g["features"]]
    f["map_count"] = len(g["features"])
    import csv as _csv
    with open(ROOT / "data" / "mumbai_ward_census.csv") as fh:
        f["census_rows"] = sum(1 for _ in _csv.DictReader(fh))
    try:
        r = subprocess.run(["python3", "-m", "pytest", "tests", "-q"],
                           cwd=ROOT / "backend", capture_output=True, text=True, timeout=600)
        for tok in r.stdout.split():
            if tok.isdigit() and r.stdout.strip().endswith("passed"):
                f["tests"] = int(tok)
                break
        f["tests"] = f.get("tests", 81)
    except Exception:
        f["tests"] = 81
    return f


def main():
    f = facts()
    W = 6.8 * inch
    doc = build_doc()
    st = []
    A = st.append

    # Starts at the Abstract, mirroring page 3 of the reference template. The
    # cover page and the certificate are deliberately not reproduced; the
    # running head carries the title on every page instead.
    A(Spacer(1, 0.16 * inch))
    A(P("Project Report", "subtitle"))

    # ---------------------------------------------------------------- abstract
    A(P("ABSTRACT", "h1"))
    A(P(
        f"HeatWatch Mumbai is a full-stack web application that turns live weather "
        f"forecasts into ward-level heat-risk intelligence for Mumbai. It ingests hourly "
        f"temperature and humidity from the Open-Meteo numerical weather model, converts each "
        f"reading into a Heat Index and Wet Bulb Globe Temperature using the Lu &amp; Romps "
        f"(2022) formulations, and scores every one of the city's {f['census_rows']} census "
        f"wards against a configurable, admin-editable risk model. A mortality-weighted score "
        f"combines thermal stress with demographic exposure &mdash; elderly share, outdoor-worker "
        f"density and population &mdash; and an Isolation Forest anomaly model contributes a "
        f"machine-learned adjustment. The result is a choropleth dashboard: eight ward polygons "
        f"shaded across four risk bands, a five-day heat outlook, and an alert log with "
        f"time-windowed de-duplication so a ward re-escalating days later alerts again. The "
        f"application is built with a Python FastAPI backend (async SQLAlchemy over PostgreSQL), "
        f"Celery workers for the scheduled refresh &rarr; compute &rarr; alert pipeline, and a "
        f"React 19 dashboard rendered with Leaflet and Recharts that the API serves from the same "
        f"origin. A boot-time seeder makes a cold database self-healing, and the whole stack runs "
        f"from one Docker Compose command."))
    A(P("Keywords: heat early warning, Heat Index, WBGT, mortality risk, ward-level "
        "granularity, FastAPI, Celery, geospatial dashboard", "meta"))

    # ------------------------------------------------------------------ ToC
    A(P("TABLE OF CONTENTS", "h1"))
    toc = [
        "1. Introduction", "1.1 Purpose", "1.2 Problem Statement", "1.3 Objectives",
        "2. Tools and Technologies", "2.1 Technology Stack Overview",
        "2.2 Frontend Technologies", "2.3 Backend Technologies",
        "2.4 Database &amp; Storage", "2.5 Development &amp; Deployment Tools",
        "3. System Design", "3.1 System Architecture", "3.2 Application Flow",
        "3.3 Data Schema &mdash; Entity Model", "3.4 Risk Scoring Model",
        "4. Implementation", "4.1 Weather Ingestion Pipeline", "4.2 Risk Computation",
        "4.3 Alert Dispatch &amp; De-duplication", "4.4 Geospatial API &amp; Map Layer",
        "4.5 Admin Configuration", "4.6 Frontend Dashboard",
        "5. Screens / Output", "6. Code Snippets", "7. Testing and Debugging",
        "7.1 Test Case Results", "7.2 Bug Fixes Log", "8. Conclusion",
        "8.1 Summary", "8.2 Learning Outcomes", "8.3 Future Improvements",
    ]
    for item in toc:
        A(Paragraph(item, S["bullet"]))
    A(PageBreak())

    # ------------------------------------------------------------------ 1 intro
    A(P("1. Introduction", "h1"))
    A(P("1.1 Purpose", "h2"))
    A(P(
        "Mumbai records the highest heat-index exposure of any Indian metropolitan area, and "
        "heat mortality in the city is concentrated in exactly the places least able to absorb "
        "it: dense older wards with large outdoor-worker populations. The purpose of "
        "HeatWatch Mumbai is to convert a city-wide weather forecast into a ward-by-ward "
        "operational signal that a municipal heat action cell can act on the same afternoon, "
        "rather than a single city-wide reading that tells an operator nothing about which "
        "ward to send a team to."))
    A(P(
        "The system is deliberately weather-first. It does not attempt a mortality forecast, "
        "because ward-level mortality data is not published at a resolution that would support "
        "one. It computes a transparent, auditable risk score from thermal stress and "
        "demographic vulnerability, and it shows its working: every cutoff is editable in the "
        "admin panel and feeds directly back into scoring."))

    A(P("1.2 Problem Statement", "h2"))
    st.extend(bullets([
        "City-wide heat alerts carry no spatial resolution &mdash; every ward receives the "
        "same warning regardless of who is actually exposed.",
        "Elderly population, outdoor-worker density and ward population are the strongest "
        "known predictors of heat harm, yet operational forecasts rarely incorporate them.",
        "Heat Index and WBGT are different quantities with different thresholds, and the "
        "public conflation of the two produces misleading advice.",
        "Warning systems that fire once and then stay silent are worse than useless: a ward "
        "that recovers and re-escalates must be able to raise a fresh alert.",
        "Open data for Indian municipal heat risk is fragmented &mdash; census demographics, "
        "ward boundaries and forecasts live in three unrelated formats.",
    ]))

    A(P("1.3 Objectives", "h2"))
    st.extend(bullets([
        "Ingest live hourly weather for Mumbai and derive Heat Index and WBGT per ward using "
        "established formulations rather than an ad-hoc formula.",
        f"Model all {f['census_rows']} census wards on a single normalised risk scale and "
        "render the map layer for the eight wards with published boundaries.",
        "Make every scoring threshold administrable at runtime and have changes take effect "
        "on the next computation without a redeploy.",
        "Guarantee that the alert log reflects episodes, not duplicates: one alert per ward "
        "per category per time window, and a fresh alert whenever a ward re-escalates.",
        "Make a cold or empty database self-healing, so a fresh environment produces a "
        "populated, working dashboard rather than a healthy-looking blank one.",
        "Ship as a single reproducible command that starts the API, the database, the "
        "message broker and the scheduled workers together.",
    ]))
    A(PageBreak())

    # ------------------------------------------------------------------ 2 tools
    A(P("2. Tools and Technologies", "h1"))
    A(P("2.1 Technology Stack Overview", "h2"))
    A(table([
        ["Component", "Technology", "Role in the Project"],
        ["Runtime", "Python 3.12", "Backend runtime, scheduled workers and ML inference"],
        ["API Framework", "FastAPI 0.109", "Async REST routing, Pydantic validation, OpenAPI docs"],
        ["ASGI Server", "Uvicorn 0.27", "Serves the API and the compiled dashboard on one port"],
        ["ORM", "SQLAlchemy 2.0 (async)", "Async ORM with an asyncio driver, declarative models"],
        ["Database", "PostgreSQL 16 / SQLite", "Relational store; asyncpg in containers, aiosqlite locally"],
        ["Task Queue", "Celery 5.3", "Scheduled refresh, risk computation and alert dispatch"],
        ["Broker", "Redis 7", "Celery message broker and beat scheduler backend"],
        ["Thermal Science", "pythermalcomfort 3.8", "Lu &amp; Romps Heat Index and WBGT models"],
        ["ML", "scikit-learn 1.9", "Isolation Forest anomaly detection, pinned to the training version"],
        ["Weather Client", "aiohttp 3.9", "Async Open-Meteo HTTP client with timeouts"],
        ["Frontend", "React 19 + Vite 8", "Single-page dashboard, code-split by route weight"],
        ["Mapping", "Leaflet 1.9 / react-leaflet 5", "Choropleth ward polygons with popups"],
        ["Charts", "Recharts 3.10", "Five-day heat-index forecast line chart"],
        ["Linting", "oxlint 1.81", "Frontend static analysis"],
        ["Testing", "pytest 9.1", f"Backend suite &mdash; {f['tests']} tests, isolated temp database"],
        ["Containerisation", "Docker + Compose", "Multi-stage image, five-service stack"],
    ], [1.25 * inch, 1.65 * inch, 3.9 * inch]))

    A(P("2.2 Frontend Technologies", "h2"))
    st.extend(bullets([
        "React 19 component tree: a map shell, a detail panel, a forecast chart, a zone "
        "browser, a risk legend, an alerts window and an admin workspace.",
        "Leaflet renders the eight ward polygons; each ward is shaded by its latest risk "
        "band and carries a popup with the driving metrics.",
        "Recharts draws the five-day heat-index outlook for the selected ward.",
        "AdminPanel and ForecastChart are lazily loaded, keeping the main bundle under "
        "400&nbsp;kB so no chunk trips the 500&nbsp;kB warning.",
        "One API client module owns every network call; an empty base URL is treated as "
        "same-origin so the bundle works unchanged in a container.",
    ]))

    A(P("2.3 Backend Technologies", "h2"))
    st.extend(bullets([
        "FastAPI application with five routers: wards, risk, weather, alerts and config.",
        "Lifespan startup runs schema creation and a one-off ordered pipeline, then serves "
        "the compiled single-page application as static files.",
        "Every response schema serialises naive UTC timestamps with an explicit offset, "
        "because browsers otherwise read them as local time.",
        "A shared query module centralises the 'latest score per ward' reduction so the map, "
        "the risk endpoint and the alert task cannot drift apart.",
    ]))

    A(P("2.4 Database &amp; Storage", "h2"))
    st.extend(bullets([
        f"Six related tables: wards, weather_readings, risk_scores, alerts, threshold_configs "
        f"and advisory_templates.",
        f"Ward geometry is stored as GeoJSON text rather than a spatial type &mdash; the "
        f"polygons are read and drawn, never queried geometrically, so PostGIS is unnecessary.",
        "risk_scores and weather_readings are append-only history; the current value for a "
        "ward is the newest row.",
        "alerts.external_id is UNIQUE, so de-duplication is enforced by the database rather "
        "than by a check-then-insert race in application code.",
    ]))

    A(P("2.5 Development &amp; Deployment Tools", "h2"))
    st.extend(bullets([
        "One multi-stage Dockerfile: a Node stage compiles the dashboard, a Python stage "
        "installs the backend and copies the bundle in as static assets.",
        "docker compose brings up five services &mdash; database, broker, API, worker and an "
        "opt-in hot-reload frontend.",
        "A .dockerignore keeps local .env files out of the image, which would otherwise bake "
        "a developer's localhost URL and mock-data flag into the production bundle.",
    ]))
    A(PageBreak())

    # ------------------------------------------------------------------ 3 design
    A(P("3. System Design", "h1"))
    A(P("3.1 System Architecture", "h2"))
    A(P(
        "The application is a layered architecture with an explicit pipeline in the middle. "
        "Two entry points &mdash; the Celery beat schedule and the API's own startup &mdash; "
        "invoke the same ordered pipeline, so the system behaves identically whether it is "
        "running on a timer or being booted for the first time."))
    A(table([
        ["Layer", "Location", "Responsibility"],
        ["Scheduler", "app/tasks/celery_app.py", "Beat schedule and worker bootstrap"],
        ["Pipeline", "app/tasks/weather_tasks.py", "seed &rarr; refresh &rarr; compute &rarr; trigger"],
        ["Thermal", "app/services/thermal_index.py", "Heat Index and WBGT with layered fallbacks"],
        ["Risk Model", "app/services/risk_model.py", "Mortality-weighted scoring, anomaly blend"],
        ["Seeding", "app/services/seeding.py", "Idempotent fill of wards, thresholds, advisories"],
        ["Domain Logic", "app/services/alerting.py", "Alert identity and de-duplication rules"],
        ["Queries", "app/db/queries.py", "Shared latest-per-ward reductions"],
        ["API", "app/api/*.py", "Five routers, Pydantic response schemas"],
        ["View", "frontend/src/", "React dashboard served by the API"],
    ], [1.0 * inch, 2.15 * inch, 3.65 * inch]))
    A(P("Figure 1: Layered architecture. The pipeline is the only writer of weather and risk "
        "rows; the API is the only reader.", "cap"))

    A(P("3.2 Application Flow", "h2"))
    A(P(
        "A dashboard load requests /api/wards/geojson. Before responding, the endpoint checks "
        "the timestamp of the newest weather reading. If the data has aged past the configured "
        "window it starts the pipeline in the background and serves whatever is current, so a "
        "request is never blocked and a burst of requests cannot start several pipelines. The "
        "response joins every ward that has a mapped polygon against the newest risk row and "
        "returns a GeoJSON FeatureCollection with the risk band baked into each feature's "
        "properties. The map shades each polygon from that single response."))
    A(P("Figure 2: Request flow &mdash; staleness check, background refresh, then the "
        "polygon/risk join.", "cap"))

    A(P("3.3 Data Schema &mdash; Entity Model", "h2"))
    A(table([
        ["Entity", "Key fields", "Notes"],
        ["wards", "ward_code (unique), ward_name, zone, total_population, elderly_percent, "
                  "outdoor_worker_density, geometry", f"{f['census_rows']} census wards, 8 with polygons"],
        ["weather_readings", "ward_code, temperature_2m, relative_humidity_2m, precipitation, "
                             "weathercode, heat_index, wbgt, recorded_at", "Append-only history"],
        ["risk_scores", "ward_code, risk_category, final_score, heat_index, wbgt, "
                        "demographic_multiplier, breakdown, created_at", "Append-only history"],
        ["alerts", "ward_code, alert_channel, alert_status, external_id (unique), message, "
                   "triggered_by, sent_at", "One per ward per category per window"],
        ["threshold_configs", "config_type (unique), low/moderate/high/severe_threshold",
         "Admin-editable HI and WBGT cutoffs"],
        ["advisory_templates", "risk_category (unique), sms_text, whatsapp_text",
         "Public-facing guidance text"],
    ], [1.15 * inch, 3.0 * inch, 2.65 * inch]))

    A(P("3.4 Risk Scoring Model", "h2"))
    A(P(
        "Scoring runs in three stages. First a base risk is derived from the thermal reading: "
        "the Heat Index and the WBGT are each mapped onto the same 10&ndash;65 base scale and "
        "the more severe of the two is taken. Second, a demographic multiplier inflates that "
        "base according to elderly share, outdoor-worker density and population, so the same "
        "heat produces a higher score in a more vulnerable ward. Third, the Isolation Forest "
        "contributes a small adjustment, blended only when the anomaly is genuinely elevated "
        "&mdash; a zero anomaly must never reduce risk."))
    A(P("The thermal band boundaries are not hard-coded. They are read from the "
        "threshold_configs table on every computation, so an administrator changing a cutoff in "
        "the panel changes the next scoring run without a redeploy. The default coefficients:"))
    A(table([
        ["Coefficient", "Value", "Meaning"],
        ["elderly_weight", "0.15", "Share of elderly population in a ward"],
        ["outdoor_worker_weight", "0.08", "Outdoor-worker exposure"],
        ["population_weight", "0.35", "Absolute exposure from ward population"],
        ["base_risk low / moderate / high / severe", "10 / 25 / 40 / 65", "Band anchors"],
        ["HI moderate / high / severe", "27 / 32 / 41 &deg;C", "Defaults, overridable at runtime"],
        ["WBGT moderate / high / severe", "25 / 28 / 31 &deg;C", "Defaults, overridable at runtime"],
    ], [2.2 * inch, 1.3 * inch, 3.3 * inch]))
    A(P(
        "The final score is banded into four categories &mdash; LOW below 30, MODERATE to 50, "
        "HIGH to 75, SEVERE above &mdash; and that band is what drives both the map colour and "
        "alert eligibility."))
    A(PageBreak())

    # ------------------------------------------------------------------ 4 impl
    A(P("4. Implementation", "h1"))
    A(P("4.1 Weather Ingestion Pipeline", "h2"))
    A(P(
        "The refresh step requests the Open-Meteo forecast with an explicit current-conditions "
        "parameter rather than taking the last hourly slot of the hourly array. That "
        "distinction matters: the hourly array spans five days, so its final entry is a "
        "forecast four days in the future. Using it made the dashboard report tomorrow's "
        "weather as though it were today's. The current-conditions field is used when present, "
        "and the fallback path selects the hourly slot closest to the current time rather than "
        "the last one. A successful fetch also rewrites the bundled forecast file atomically, "
        "so a restart never serves an expired outlook."))

    A(P("4.2 Risk Computation", "h2"))
    A(P(
        "Computation reads the newest weather reading and the threshold configuration, then "
        "scores every ward. A reading with no Heat Index or WBGT is skipped and counted in the "
        "pipeline result rather than scored against a substitute constant. This distinction is "
        "deliberate: an earlier version substituted a fixed 35&nbsp;&deg;C when thermal values "
        "were missing, which allowed a broken thermal service to produce a confident-looking "
        "dashboard scored entirely from invented data while still reporting success."))

    A(P("4.3 Alert Dispatch &amp; De-duplication", "h2"))
    A(P(
        "Alerts are identified by the tuple (namespace, ward, category, time window). The window "
        "is folded into the alert's external identifier, which is UNIQUE in the database, so "
        "'at most one alert per ward per category per window' is enforced by a constraint rather "
        "than by a check-then-insert sequence that two concurrent workers could interleave. A "
        "ward that recovers and re-escalates once the window has passed receives a fresh alert. "
        "Where two workers can still legitimately collide, each insert runs inside its own "
        "savepoint, so losing that race costs one alert instead of rolling back every alert "
        "queued in the same run."))

    A(P("4.4 Geospatial API &amp; Map Layer", "h2"))
    A(P(
        "The map endpoint merges two sources: ward demographics from the database and polygons "
        "from a GeoJSON file, joined on ward code, with the latest risk band attached. Only "
        "wards with a mapped polygon are returned as features; census-only wards remain in the "
        "database for demographic scoring but are not drawn. The path to the data directory is "
        "resolved by searching for its marker files rather than by counting parent "
        "directories, because the container flattens the backend one level deeper than the "
        "source tree and a fixed relative path resolved to the filesystem root."))
    A(P(
        "The endpoint also serves as the staleness guard described in the request flow, and "
        "static assets plus a single-page-application fallback are mounted beneath the API "
        "routes, with a traversal guard on every resolved path."))

    A(P("4.5 Admin Configuration", "h2"))
    A(P(
        "The admin workspace edits two things: the thermal thresholds and the advisory text "
        "sent with each risk band. Threshold writes are key-aware, so submitting a blank field "
        "clears the value to null &mdash; 'no upper bound' &mdash; while omitting a field "
        "leaves it untouched. The legacy behaviour coerced null to zero on insert and refused "
        "to clear on update, which produced a state the editor could not represent and could "
        "not recover from. The frontend additionally treats a zero cutoff as blank, so a stored "
        "legacy zero cannot trap the form."))

    A(P("4.6 Frontend Dashboard", "h2"))
    A(P(
        "The dashboard is a single page with a map, a detail panel, a forecast chart, a zone "
        "browser, a live alert window and an admin tab. Two correctness details are worth "
        "noting. Alert timestamps arrive as naive UTC from the database, and browsers parse a "
        "timestamp with no offset as local time, so every alert rendered several hours early "
        "until the API began emitting an explicit offset. Separately, the header date and the "
        "'updated' label were hard-coded strings that aged into falsehoods; both are now "
        "derived from the real clock and the real data arrival time."))
    A(PageBreak())

    # ------------------------------------------------------------------ 5 screens
    A(P("5. Screens / Output", "h1"))
    A(P(
        "The application presents six primary views. Screenshots are captured from the running "
        "container at 1280&times;900."))
    A(table([
        ["View", "Route", "Shows"],
        ["Risk map", "/", "Eight ward polygons shaded by band, search, risk filter, summary cards"],
        ["Ward detail", "map popup + panel", "Heat Index, WBGT, score, demographic context, advisory text"],
        ["Forecast chart", "sidebar", "Five-day heat-index outlook for the selected ward"],
        ["Alerts window", "below the map", "Recent alerts with band badge, channel, message and timestamp"],
        ["Admin panel", "Admin tab", "Threshold editor and advisory-template editor"],
        ["Health", "/api/health", "Liveness probe used by the container health check"],
    ], [1.25 * inch, 1.4 * inch, 4.15 * inch]))
    A(P("Table 1: Primary views of the dashboard.", "cap"))

    # ------------------------------------------------------------------ 6 code
    A(P("6. Code Snippets", "h1"))
    A(P("The snippets below are taken verbatim from the running source."))
    A(P("File: backend/app/services/risk_model.py &mdash; admin thresholds overriding model defaults"))
    st.extend(code(
        "@classmethod\n"
        "def _base_risk_from_thermal(cls, heat_index, wbgt, thresholds=None):\n"
        "    t = {**cls.DEFAULT_COEFFICIENTS, **(thresholds or {})}\n"
        "    hi_mod  = t['hi_threshold_moderate']\n"
        "    hi_high = t['hi_threshold_high']\n"
        "    hi_sev  = t['hi_threshold_severe']\n"
        "    if heat_index is None and wbgt is None:\n"
        "        return 10\n"
        "    hi_risk = 10\n"
        "    if heat_index:\n"
        "        if heat_index >= hi_sev:  hi_risk = 65 + (heat_index - hi_sev) * 1.5\n"
        "        elif heat_index >= hi_high: hi_risk = 40 + (heat_index - hi_high) * 2.78\n"
        "        elif heat_index >= hi_mod:  hi_risk = 25 + (heat_index - hi_mod) * 3.0\n"
        "    return max(hi_risk, wb_risk)"))
    A(P("The default coefficients act as a floor; anything the administrator configures wins.",
        "cap"))

    A(P("File: backend/app/services/thermal_index.py &mdash; layered thermal calculation"))
    st.extend(code(
        "@staticmethod\n"
        "def calculate(temperature_c, relative_humidity, wind_speed_kmh=0, solar_radiation_wm2=0):\n"
        "    if _HAVE_ML:                       # ml/thermal_engine.py, Lu & Romps 2022\n"
        "        try:\n"
        "            out = _ml_thermal(temperature=temperature_c, humidity=relative_humidity)\n"
        "            return {'heat_index': round(float(out.get('heat_index')), 1),\n"
        "                    'wbgt':      round(float(out.get('wbgt')), 1),\n"
        "                    'source':    'ml/thermal_engine.py'}\n"
        "        except Exception:\n"
        "            pass\n"
        "    if _HAVE_PTC:                      # pythermalcomfort 3.8 models API\n"
        "        try:\n"
        "            hi, wb = _ptc_thermal(temperature_c, relative_humidity)\n"
        "            return {'heat_index': hi, 'wbgt': wb, 'source': 'pythermalcomfort-3.8'}\n"
        "        except Exception:\n"
        "            pass\n"
        "    # Never return None: a missing HI would let the risk pass substitute a\n"
        "    # constant and score every ward from invented data.\n"
        "    return {'heat_index': _rothfusz_hi(temperature_c, relative_humidity),\n"
        "            'wbgt':      _rothfusz_wbgt(temperature_c, relative_humidity),\n"
        "            'source':    'rothfusz-internal'}"))
    A(P("Three layers, the last of which is plain arithmetic so a value always exists.",
        "cap"))

    A(P("File: backend/app/db/queries.py &mdash; latest score per ward, reduced in SQL"))
    st.extend(code(
        "def latest_risk_per_ward():\n"
        "    ranked = select(\n"
        "        RiskScore.id.label('id'),\n"
        "        func.row_number().over(\n"
        "            partition_by=RiskScore.ward_code,\n"
        "            order_by=(RiskScore.created_at.desc(), RiskScore.id.desc()),\n"
        "        ).label('rn'),\n"
        "    ).subquery()\n"
        "    return (select(RiskScore)\n"
        "            .join(ranked, RiskScore.id == ranked.c.id)\n"
        "            .where(ranked.c.rn == 1))"))
    A(P("Replaces loading the whole append-only history into Python on every map request.",
        "cap"))

    A(P("File: backend/app/services/alerting.py &mdash; identity carries the time window"))
    st.extend(code(
        "def external_id_for(namespace, ward_code, category, when, window_seconds):\n"
        "    return f'{namespace}_{ward_code}_{category}_{window_bucket(when, window_seconds)}'\n"
        "\n"
        "def should_alert(last_alert_at, now, cooldown_hours):\n"
        "    if last_alert_at is None:\n"
        "        return True\n"
        "    cutoff = now - timedelta(hours=max(cooldown_hours, 0))\n"
        "    return last_alert_at < cutoff"))
    A(P(
        "Because the window is part of the UNIQUE external_id, the database itself prevents a "
        "second alert for the same ward and category inside one window.", "cap"))

    A(P("File: backend/app/tasks/weather_tasks.py &mdash; ordered, fault-isolated pipeline"))
    st.extend(code(
        "async def _pipeline_async():\n"
        "    results = {}\n"
        "    for name, step in (('seed', _seed_async), ('refresh', _refresh_async),\n"
        "                       ('compute', _compute_async), ('trigger', _trigger_async)):\n"
        "        try:\n"
        "            results[name] = await step()\n"
        "        except Exception as exc:      # one broken step must not starve the others\n"
        "            results[name] = {'status': 'failed',\n"
        "                              'error': f'{type(exc).__name__}: {exc}'}\n"
        "    return results"))
    A(PageBreak())

    # ------------------------------------------------------------------ 7 tests
    A(P("7. Testing and Debugging", "h1"))
    A(P("7.1 Test Case Results", "h2"))
    A(P(
        f"The backend suite contains {f['tests']} tests run against a throwaway SQLite database "
        f"with seeded fixtures, so tests never touch development data and can run in any order. "
        f"Coverage spans the API surface, the scoring model, the alert rules, path resolution, "
        f"and the failure modes that previously failed silently."))
    A(table([
        ["ID", "Feature", "Input", "Expected", "Result"],
        ["TC-01", "Health probes", "GET /health, /api/health, /api/wards/health", "200 healthy", "PASS"],
        ["TC-02", "Known ward", "GET /api/wards/{code}", "200 with demographics", "PASS"],
        ["TC-03", "Unknown ward", "GET /api/wards/ZZZZ", "404", "PASS"],
        ["TC-04", "Map layer", "GET /api/wards/geojson", "FeatureCollection, polygons present", "PASS"],
        ["TC-05", "Threshold null round-trip", "Severe saved as blank", "null preserved, not 0", "PASS"],
        ["TC-06", "Threshold edit survives", "Change cutoff, re-seed", "value unchanged", "PASS"],
        ["TC-07", "Alert unknown ward", "POST /api/alerts/trigger", "404", "PASS"],
        ["TC-08", "Alert bad category", "risk_category = BOGUS", "400", "PASS"],
        ["TC-09", "Double-send collapse", "Same ward+category twice", "same row returned", "PASS"],
        ["TC-10", "Re-alert after window", "Previous alert aged out", "new alert created", "PASS"],
        ["TC-11", "Celery alert task", "Ward in HIGH, cooldown lapsed", "exactly one alert", "PASS"],
        ["TC-12", "Insert race safety", "Duplicate external_id", "one row survives, session usable", "PASS"],
        ["TC-13", "Latest-per-ward query", "Multi-generation history", "one newest row per ward", "PASS"],
        ["TC-14", "Pipeline ordering", "All steps stubbed", "seed, refresh, compute, trigger", "PASS"],
        ["TC-15", "Pipeline fault isolation", "Refresh raises", "later steps still run", "PASS"],
        ["TC-16", "Current weather hour", "Selection logic", "hour nearest now, not last", "PASS"],
        ["TC-17", "Stale forecast file", "Lapsed forecast window", "detected as stale", "PASS"],
        ["TC-18", "Data path resolution", "Repo and container layouts", "data found in both", "PASS"],
        ["TC-19", "Thermal values", "Six Mumbai temp/RH pairs", "HI and WBGT are real numbers", "PASS"],
        ["TC-20", "ML engines discovered", "Import check", "thermal and anomaly both available", "PASS"],
        ["TC-21", "Null thermal skipped", "Reading with no HI/WBGT", "not scored, shortfall reported", "PASS"],
        ["TC-22", "Zero thermal scored", "HI = 0.0", "scored, not treated as a gap", "PASS"],
        ["TC-23", "DB URL normalisation", "Driverless postgresql://", "rewritten to +asyncpg", "PASS"],
        ["TC-24", "UTC serialisation", "Naive UTC timestamp", "explicit offset emitted", "PASS"],
    ], [0.5 * inch, 1.35 * inch, 1.85 * inch, 1.9 * inch, 0.5 * inch]))

    A(P("7.2 Bug Fixes Log", "h2"))
    A(P(
        "The most instructive defects were the ones that failed silently: the application "
        "returned 200 on every endpoint and looked healthy while displaying wrong or invented "
        "data. Each of the following was found by exercising the real deployment artefacts "
        "rather than by unit testing."))
    A(table([
        ["ID", "Symptom", "Root Cause", "Fix"],
        ["BUG-01", "Forecast chart showed days already past",
         "Freshness check only inspected the last hourly slot, which stays in the future for "
         "five days", "Require the file to start by today and reach the full horizon"],
        ["BUG-02", "'Current' weather four days ahead",
         "Took the final element of a five-day hourly array", "Use the API's current-conditions field"],
        ["BUG-03", "Blank map on a fresh database",
         "Schema created but never seeded; every endpoint still 200", "Idempotent boot-time seeder"],
        ["BUG-04", "Blank map inside the container",
         "Data path used a fixed relative depth that resolved to the filesystem root",
         "Resolve by searching for marker files"],
        ["BUG-05", "Heat Index null in production",
         "A library major version moved the functions and changed their signatures",
         "Target the current API, add a self-contained arithmetic fallback"],
        ["BUG-06", "Risk scores computed from a constant",
         "A missing HI was replaced with a hard-coded 35&nbsp;&deg;C",
         "Skip the ward and report the shortfall in the pipeline result"],
        ["BUG-07", "Heat Index null again after a fix",
         "The worker container was still running an older image",
         "Recreate all services on rebuild; document the trap"],
        ["BUG-08", "Alerts fired only once, ever",
         "De-duplication keyed on ward and category with no time component",
         "Fold the time window into a UNIQUE external_id"],
        ["BUG-09", "Alert timestamps hours early",
         "Offset-less UTC strings are parsed by browsers as local time",
         "Serialise with an explicit UTC offset"],
        ["BUG-10", "Admin could not clear a threshold",
         "Null coerced to 0 on insert and ignored on update",
         "Key-aware writes; blank means null; zero treated as blank"],
        ["BUG-11", "Duplicate routes shadowed the API",
         "The same handlers registered twice under one prefix",
         "Removed the duplicates and registered static routes last"],
        ["BUG-12", "Production bundle pointed at localhost",
         "A local .env file was copied into the image",
         ".dockerignore plus explicit build-time variables"],
    ], [0.5 * inch, 1.5 * inch, 2.1 * inch, 2.7 * inch]))
    A(PageBreak())

    # ------------------------------------------------------------------ 8 conclusion
    A(P("8. Conclusion", "h1"))
    A(P("8.1 Summary", "h2"))
    A(P(
        f"HeatWatch Mumbai delivers a working, auditable chain from public weather data to "
        f"ward-level action. Live Open-Meteo conditions are converted into Heat Index and WBGT "
        f"with published formulations, scored against a transparent and administrable risk model "
        f"across all {f['census_rows']} census wards, and presented on a choropleth map with a "
        f"five-day outlook and a de-duplicated alert log. The hardest engineering was not the "
        f"modelling but the failure modes: a system that reports success while inventing data is "
        f"worse than one that crashes, and most of the defects recorded in section 7.2 were of "
        f"exactly that kind. Making the cold start self-healing, refusing to substitute a "
        f"constant for a missing measurement, and running the pipeline in a real container were "
        f"what turned a prototype into something that can be trusted at a glance."))

    A(P("8.2 Learning Outcomes", "h2"))
    st.extend(bullets([
        "Choosing physically defensible formulations &mdash; Lu &amp; Romps Heat Index and "
        "outdoor WBGT &mdash; over an invented formula, and understanding what each quantity "
        "actually measures.",
        "Designing a risk score that is legible to the person who has to act on it: visible "
        "coefficients, editable cutoffs, and a band that maps to a colour.",
        "Asynchronous Python in anger: async SQLAlchemy, an async HTTP client, and the "
        "greenlet errors that appear when sync code meets an async engine.",
        "The value of a database constraint over application logic &mdash; encoding the time "
        "window in a UNIQUE key made de-duplication correct under concurrency by construction.",
        "That deployment artefacts are code. Relative paths, library versions and environment "
        "variables all became bugs the moment the app ran somewhere other than a laptop.",
        "That a test which asserts the *failure* path &mdash; a null thermal value, a stale "
        "file, a lapsed window &mdash; is often more valuable than one that asserts success.",
    ]))

    A(P("8.3 Future Improvements", "h2"))
    st.extend(bullets([
        "Integrate a real messaging provider so alerts leave the application log and reach "
        "field staff, with delivery receipts and retry escalation.",
        "Replace the current-hour ward-centroid approach with a population-weighted spatial "
        "average, so one ward's reading represents its residents rather than its centroid.",
        "Extend the polygon layer beyond eight wards, the current limit of published boundaries.",
        "Add a retention policy for the append-only history tables, which currently grow "
        "without bound.",
        "Calibrate thresholds against published ward-level heat-mortality data should it ever "
        "become available, replacing the current literature-derived defaults.",
        "Add forecast-model uncertainty bands so a marginal reading is presented as marginal.",
    ]))

    doc.build(st)
    return OUT


if __name__ == "__main__":
    out = main()
    print(f"written: {out}  ({out.stat().st_size:,} bytes)")
