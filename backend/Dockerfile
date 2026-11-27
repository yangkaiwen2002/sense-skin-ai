FROM python:3.12-slim
WORKDIR /app
COPY requirements-core.txt .
RUN pip install --no-cache-dir -r requirements-core.txt
COPY app ./app
COPY data ./data
COPY data_sources ./data_sources
COPY evaluation ./evaluation
COPY seed ./seed
RUN useradd --create-home app && mkdir -p /data && chown app:app /data
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
