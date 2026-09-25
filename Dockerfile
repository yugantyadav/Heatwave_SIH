FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY scripts/ ./scripts/
# data/ holds wards_geojson.json (the map polygons) and the fallback forecast.
# Without it the image boots into an empty map and the weather refresh cannot
# write its forecast file.
COPY data/ ./data/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
