FROM python:3.11-slim

WORKDIR /workspace
COPY client.py /workspace/client.py

RUN chmod 0555 /workspace/client.py && mkdir -p /telemetry && chmod 1777 /telemetry

USER 65532:65532
ENTRYPOINT ["sleep", "infinity"]
