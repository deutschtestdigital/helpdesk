from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI()

# Verzeichnis für HTML-Dateien definieren
templates = Jinja2Templates(directory="templates")

# Beispieldaten für die Hilfethemen (Kacheln)
CATEGORIES = [
    {"id": "zoom", "title": "Zoom & Technik", "icon": "video", "text": "Kamera, Mikrofon und Meeting-Links."},
    {"id": "pruefung", "title": "Prüfungsablauf", "icon": "clipboard", "text": "Regeln, Ausweise und Zeitplan."},
    {"id": "zertifikat", "title": "Ergebnisse", "icon": "academic", "text": "Zertifikate und Punkteabfrage."},
    {"id": "buchung", "title": "Buchung & Zahlung", "icon": "credit-card", "text": "Stornierung und Umbuchung."}
]

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "categories": CATEGORIES
    })

if __name__ == "__main__":
    # Port 8080 ist Standard für Google Cloud Run
    uvicorn.run(app, host="0.0.0.0", port=8080)


