FROM python:3.12-slim
# Texterkennung für gescannte Skripte: ocrmypdf + Tesseract (deutsch), läuft lokal im Container.
# pngquant: verkleinert die Seitenbilder (ocrmypdf --optimize 2). Die genauen Sprachdaten (tessdata_best) ersetzen die
# schnellen aus dem Paket: erkennen Umlaute und Sonderzeichen besser, brauchen dafür etwas länger.
RUN apt-get update && apt-get install -y --no-install-recommends ocrmypdf tesseract-ocr-deu ghostscript pngquant curl ca-certificates \
    && curl -fsSL -o /usr/share/tesseract-ocr/5/tessdata/deu.traineddata \
       https://github.com/tesseract-ocr/tessdata_best/raw/main/deu.traineddata \
    && apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
