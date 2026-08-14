FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY simulator.py .

RUN addgroup --system --gid 10001 tidewatch \
    && adduser --system --uid 10001 --ingroup tidewatch tidewatch \
    && chown -R tidewatch:tidewatch /app

USER 10001:10001

CMD ["python", "simulator.py"]
