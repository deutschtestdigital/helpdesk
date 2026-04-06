# 1. Wir nutzen ein offizielles, leichtgewichtiges Python-Image
FROM python:3.11-slim

# 2. Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# 3. Kopiere die requirements-Datei und installiere die Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Kopiere den restlichen Code (app.py und den templates-Ordner)
COPY . .

# 5. Der Port, den Cloud Run erwartet (Standard 8080)
ENV PORT 8080

# 6. Befehl zum Starten der App mit uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
