FROM python:3.10-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
COPY templates/ templates/
COPY demo/ demo/
COPY conftest.py .

RUN pip install -e ".[dev]"

ENV DEEPSEEK_API_KEY=""
ENV HARNESS_MOCK=1

EXPOSE 7860

CMD ["gunicorn", "harness.web:create_app", "--factory", "--bind", "0.0.0.0:7860"]
