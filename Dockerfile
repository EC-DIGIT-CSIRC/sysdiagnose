# First stage: Build stage
FROM python:3.11-slim AS build_stage

WORKDIR /sysdiagnose/

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

RUN pip install hatch

COPY pyproject.toml ./
COPY src ./src

RUN hatch build

# Second stage: Runtime stage
FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y graphviz

COPY --from=build_stage /sysdiagnose/dist/sysdiagnose*.whl /tmp/

RUN pip install --no-cache-dir /tmp/sysdiagnose*.whl && \
    rm -rf /tmp/sysdiagnose*.whl

WORKDIR /cases

ENTRYPOINT ["saf"]