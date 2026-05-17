FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN pytest tests/ -v --tb=short

FROM python:3.12-slim
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app/app.py .
USER appuser
ENV DB_PATH=/data/healthbook.db
VOLUME ["/data"]
EXPOSE 5000
ENTRYPOINT ["python", "app.py"]
