FROM python:3.13-slim
WORKDIR /app
COPY src/ /app/src/
COPY pyproject.toml ./
COPY uv.lock ./
RUN pip install uv
RUN uv sync --all-groups
CMD ["uv", "run", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
