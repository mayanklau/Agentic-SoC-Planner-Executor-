FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml README.md /app/
COPY src /app/src

RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "agentic_soc_planner_executor.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
