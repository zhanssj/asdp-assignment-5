ARG PYTHON_IMAGE=python:3.13-slim-bookworm@sha256:281d39ff02e3b389401586134ff9e6572954687822a58055ec07a60ded4e0b7f
FROM ${PYTHON_IMAGE} AS dependencies
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /opt/analyzer
COPY infra/requirements.lock /tmp/requirements.lock
RUN python -m pip install --no-cache-dir -r /tmp/requirements.lock

FROM dependencies AS test
COPY infra/requirements-test.lock /tmp/requirements-test.lock
RUN python -m pip install --no-cache-dir -r /tmp/requirements-test.lock && mkdir /reports
COPY app ./app
COPY tests ./tests
CMD ["python", "-m", "pytest", "tests", "-q", "--junitxml=/reports/junit.xml"]

FROM dependencies AS runtime
ARG SOURCE_COMMIT=development
ENV SOURCE_COMMIT=${SOURCE_COMMIT}
LABEL org.opencontainers.image.title="Smart City Sensor Data Analyzer" \
      org.opencontainers.image.revision=${SOURCE_COMMIT}
COPY app ./app
RUN useradd --system --uid 10001 --no-create-home analyzer
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
