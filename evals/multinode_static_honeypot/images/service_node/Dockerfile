FROM python:3.11-slim
WORKDIR /app
COPY app.py /app/app.py
RUN pip install --no-cache-dir fastapi uvicorn && mkdir -p /telemetry && chmod 1777 /telemetry
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
