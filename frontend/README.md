# Frontend

React + Vite + Leaflet dashboard for the Heatwave Early Warning System.

## Structure

```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Page components (Dashboard, AdminPanel, WardDetail)
│   ├── services/       # API client (axios instance with localhost proxy)
│   ├── types/          # TypeScript interfaces
│   ├── App.tsx         # Main router entry point
│   └── main.tsx        # Root rendering
├── index.html          # HTML template
├── vite.config.ts      # Vite config with API proxy
├── tsconfig.json       # TypeScript config
└── package.json        # Dependencies (react, leaflet, recharts, axios)
```

## Development

```bash
# Install dependencies
cd frontend
npm install

# Start development server (with API proxy to localhost:8000)
npm run dev

# Build for production
npm run build
```

## Key Features

- **Interactive choropleth map** of Mumbai wards using Leaflet
- **Risk-based coloring** (Low/Moderate/High/Severe)
- **Ward popup** with thermal indices (HI, WBGT), risk score, demographics
- **3-5 day forecast** chart (Recharts) showing HI & WBGT trends
- **Admin panel** for threshold configuration and advisory templates
- **Responsive design** - works mobile to desktop
- **API proxy** configured in vite.config.ts: `/api` → `localhost:8000`

## API Integration

All frontend calls proxy through Vite:
- `VITE_API_BASE_URL=http://localhost:8000/api` (in .env or vite config)
- Endpoints: `/api/wards`, `/api/risk/wards`, `/api/weather/...`, `/api/alerts/...`, `/api/config/...`

## Components

- `Dashboard` - Main map view with risk legend and forecast timeline
- `AdminPanel` - Threshold config editor, advisory template editor, alert trigger
- `WardDetail` - Full ward breakdown with demographics, risk assessment, hourly weather
- `RiskLegend` - Color key and threshold references
- `WardPopup` - Modal with ward information and risk breakdown
- `ForecastTimeline` - 24hr chart and ward risk comparison table
- `LoadingSpinner` - Loading state visualizer