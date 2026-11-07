FROM python:3.12-slim
# Texterkennung für eine gescannte Bibel-PDF ohne eigene Textebene (z. B. ein altes Fraktur-Faksimile):
# ocrmypdf + Tesseract, lokal im Container (wie beim Skripte-Dienst). Zusätzlich zum modernen Deutsch (deu)
# zwei auf historischen Fraktur-/Schwabacher-Druck trainierte Sprachdaten aus tessdata_best: deu_latf (eigens
# für deutschen Fraktur-Text) und Fraktur (das allgemeinere Skript-Modell) – siehe fraktur_ocr.py.
RUN apt-get update && apt-get install -y --no-install-recommends ocrmypdf tesseract-ocr-deu ghostscript pngquant curl ca-certificates \
    && curl -fsSL -o /usr/share/tesseract-ocr/5/tessdata/deu.traineddata \
       https://github.com/tesseract-ocr/tessdata_best/raw/main/deu.traineddata \
    && curl -fsSL -o /usr/share/tesseract-ocr/5/tessdata/deu_latf.traineddata \
       https://github.com/tesseract-ocr/tessdata_best/raw/main/deu_latf.traineddata \
    && curl -fsSL -o /usr/share/tesseract-ocr/5/tessdata/Fraktur.traineddata \
       https://github.com/tesseract-ocr/tessdata_best/raw/main/script/Fraktur.traineddata \
    && apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
