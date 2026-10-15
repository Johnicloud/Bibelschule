FROM python:3.12-slim
WORKDIR /app

# espeak-ng: Piper braucht es zum Aussprechen (Text -> Phoneme) bei den meisten Sprachen, auch Deutsch.
# curl: lädt das deutsche Stimmmodell unten herunter, danach nicht mehr nötig.
RUN apt-get update && apt-get install -y --no-install-recommends espeak-ng curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Deutsches Stimmmodell (Thorsten, mittlere Qualität, CC0/MIT) liegt dem Image bei: lokal und kostenlos,
# kein API-Key, kein Netzwerk zur Laufzeit nötig. Andere Stimme? PIPER_MODEL in docker-compose.override.yml setzen.
RUN mkdir -p /app/stimme \
    && curl -fL -o /app/stimme/de_DE-thorsten-medium.onnx \
         https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx \
    && curl -fL -o /app/stimme/de_DE-thorsten-medium.onnx.json \
         https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx.json

COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
