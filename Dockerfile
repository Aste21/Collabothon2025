FROM python:3.11-slim

# Ustawienia Pythona
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Katalog roboczy
WORKDIR /app

# Najpierw zależności
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Potem reszta kodu
COPY . .

# Port na którym będziemy słuchać w kontenerze
ENV PORT=8080

# Start FastAPI przez uvicorn (app.py zawiera `app = FastAPI(...)`)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
