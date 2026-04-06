import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI()

# Sicherstellen, dass wir den absoluten Pfad zum Ordner 'templates' finden
base_dir = os.path.dirname(os.path.abspath(__file__))
template_path = os.path.join(base_dir, "templates")

# Kleiner Check für die Logs: Existiert der Ordner?
if not os.path.exists(template_path):
    print(f"FEHLER: Der Ordner {template_path} wurde nicht gefunden!")

templates = Jinja2Templates(directory=template_path)

# Dein bestehender Code für CATEGORIES...
CATEGORIES = [
    {"id": "zoom", "title": "Zoom & Technik", "text": "Kamera, Mikrofon und Meeting-Links."},
    {"id": "pruefung", "title": "Prüfungsablauf", "text": "Regeln, Ausweise und Zeitplan."},
    {"id": "zertifikat", "title": "Ergebnisse", "text": "Zertifikate und Punkteabfrage."},
    {"id": "buchung", "title": "Buchung & Zahlung", "text": "Stornierung und Umbuchung."}
]

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "categories": CATEGORIES
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)


