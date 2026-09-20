# Mumbai Heatwave Early Warning — Frontend (R4)

React (Vite) + Leaflet + Recharts dashboard for Problem Statement 26083.
This is the R4 "Frontend Engineer" Day-9 deliverable: a live map, ward
popups, a forecast chart, and an admin panel — all built against mock
data so it runs today, with clearly marked seams for R3's real API.

## 1. Install prerequisites (one-time)

You need **Node.js** (which includes `npm`). If you don't already have it:

1. Go to https://nodejs.org and download the **LTS** version for your OS.
2. Run the installer (accept the defaults).
3. Confirm it worked — open a terminal and run:
   ```
   node -v
   npm -v
   ```
   Both should print a version number. If they don't, restart your
   terminal (and, on Windows, make sure "Add to PATH" was checked during
   install).

## 2. Get the project running

1. Unzip this project and open a terminal inside the `heatwave-frontend`
   folder.
2. Install dependencies (reads `package.json`, downloads everything into
   a `node_modules` folder — this step is required every time you unzip
   a fresh copy, since `node_modules` isn't included in the zip):
   ```
   npm install
   ```
3. Start the dev server:
   ```
   npm run dev
   ```
4. Open the URL it prints (usually `http://localhost:5173`).

Leave `npm run dev` running while you work — it auto-reloads the page
every time you save a file.

## 3. What you'll see

- **Live Dashboard tab**: a map of 8 Mumbai wards (Colaba, Dadar, Bandra
  West, Andheri West, Malad, Borivali, Kurla, Chembur), color-coded by
  risk. Click a ward (on the map, or from the "Browse by Zone" list) to
  open a popup and fill the sidebar with its Heat Index, WBGT, risk
  score, and a 3-5 day forecast chart.
- **Admin Panel tab**: view/edit the HI & WBGT thresholds that define
  each risk category, and the public advisory text shown for each one.

The UI also includes a city snapshot, live-model status, ward search and risk
filtering, a selected-ward score meter, a 5-day trend summary, and responsive
layouts for tablet and mobile screens. The selected ward's detail request is
owned by `App.jsx`; the API service caches it so the sidebar and Leaflet popup
do not issue duplicate requests.

## 4. Project structure

```
src/
├── App.jsx                    layout, tabs, and the one shared wards fetch
├── App.css / index.css        all styling — design tokens in index.css
├── data/
│   ├── mumbaiWardsSample.js   placeholder ward shapes, 8 wards, grouped into zones
│   └── adminDefaults.js       default thresholds + advisory text
├── utils/
│   └── riskConfig.js          risk category -> color/label (single source of truth)
├── services/
│   └── api.js                 every network call goes through here
└── components/
    ├── HeatMap.jsx             the Leaflet choropleth map + click popups
    ├── ZoneBrowser.jsx         ward list grouped by zone (South/Western/Central)
    ├── WardDetailPanel.jsx     selected ward's HI/WBGT/risk score
    ├── ForecastChart.jsx       Recharts line chart for the selected ward
    ├── RiskLegend.jsx          the color key
    ├── Spinner.jsx             shared loading indicator
    ├── ErrorBanner.jsx         shared error message + retry button
    └── admin/
        ├── AdminPanel.jsx      lays out the two editors below
        ├── ThresholdEditor.jsx  edit HI/WBGT cutoffs per category
        └── AdvisoryEditor.jsx   edit public advisory text per category
```

Every file has comments explaining what it does and why.

## 5. What's real vs. placeholder right now, and how to swap it

Everything runs on mock data today. The mode is controlled by environment
variables, so you can switch environments without editing source:

```bash
VITE_USE_MOCK_DATA=false VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

Two things need to happen to go live:

1. **Ward shapes**: `data/mumbaiWardsSample.js` has 8 hand-drawn squares
   standing in for real ward polygons. Swap for the real MCGM/OSM GeoJSON
   once R6 sources it — the file's comments explain exactly what
   properties (`id`, `name`, `zone`) the replacement needs to keep.
2. **Live API**: set `VITE_USE_MOCK_DATA=false` and point
   `VITE_API_BASE_URL` at R3's FastAPI server. The endpoints already
   match what R3 confirmed:
   - `GET /api/wards`
   - `GET /api/risk/wards/{id}`

   Two more are this project's best guess at a matching convention —
   confirm the exact path with R3 and adjust the one line in `api.js` if
   they differ:
   - Forecast: `GET /api/forecast/wards/{id}`
   - Admin: `GET`/`POST /api/thresholds` (this one *is* in the plan's
     confirmed route list), `GET`/`POST /api/advisories` (not yet
     confirmed — flag it to R3).

## 6. Roadmap — what's left (from the team plan)

- [ ] **Days 10-11**: Add the "trigger heat action plan" one-click button
      to the Admin Panel, wired to R5's alert dispatch.
- [ ] **Days 12-13**: Further UI polish and edge-case handling once
      real API responses (rather than mock data) are flowing in —
      e.g. what the map should show if a ward has no data yet.

Come back for help with either of these.
