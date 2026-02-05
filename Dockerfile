FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    OPENROUTER_API_KEY=your_openrouter_api_key_here \
    OPENROUTER_MODEL=gpt5.2

COPY pyproject.toml README.md /app/
COPY src /app/src

RUN pip install --no-cache-dir uv \
    && uv pip install --system .

CMD ["python", "-m", "mafiagpt"]
