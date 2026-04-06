# 1. Basis-Image (Schlankes Python)
FROM python:3.10-slim

# 2. Arbeitsverzeichnis erstellen
WORKDIR /app

# 3. System-Pakete installieren
# libgomp1 ist die Lösung für den "libgomp.so.1"-Fehler
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 4. Python-Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Alle Projektdateien kopieren
COPY . .

# 6. Port für Cloud Run freigeben
EXPOSE 8080

# 7. Startbefehl
# Hinweis: Ich nutze hier Faktorenanalyse.py, da dein Log dies als Hauptdatei zeigt
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8080", "--server.address=0.0.0.0"]
