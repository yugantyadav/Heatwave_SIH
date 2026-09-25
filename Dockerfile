# Build both halves in one image so the API can serve the SPA itself: one
# public URL, no CORS, and VITE_API_BASE_URL never has to be baked per-env.
FROM node:20-alpine AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# VITE_USE_MOCK_DATA must be "false" or the bundle serves sample data instead
# of the live API — and frontend/.env is excluded by .dockerignore, so these
# two are the only source of truth for the build.
ENV VITE_USE_MOCK_DATA=false
ENV VITE_API_BASE_URL=
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY scripts/ ./scripts/
# The Isolation Forest blend changes risk scores, so omitting it would make
# production score differently from local. 2.7 MB is cheap for parity.
COPY ml/ ./ml/
# data/ holds wards_geojson.json (the map polygons) and the fallback forecast.
# Without it the image boots into an empty map.
COPY data/ ./data/
COPY --from=frontend /fe/dist ./static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
