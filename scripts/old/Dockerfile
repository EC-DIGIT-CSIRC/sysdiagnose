# WARNING: This may not be the best way to run the sysdiagnose analysis framework.

# First stage: Build stage
FROM rust:slim AS build_stage

WORKDIR /sysdiagnose/

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

RUN apt-get update && \
    apt-get install -y git python3 python3-pip yara

RUN pip install --break-system-packages hatch

COPY pyproject.toml ./
COPY src ./src
COPY README.md ./
COPY LICENSE.txt ./

RUN hatch build

RUN find .

RUN git clone https://github.com/mandiant/macos-UnifiedLogs && \
    cd macos-UnifiedLogs/examples/unifiedlog_iterator/ && \
    cargo build --release && \
    cp ../target/release/unifiedlog_iterator /usr/local/bin/ && \
    rm -Rf macos-UnifiedLogs


# Second stage: Runtime stage
FROM python:3-slim

COPY --from=build_stage /usr/local/bin/unifiedlog_iterator /usr/local/bin/unifiedlog_iterator
COPY --from=build_stage /sysdiagnose/dist/sysdiagnose*.whl /tmp/

# install all and reduce image size, needs to be in one RUN
RUN apt-get update && \
    apt-get install -y graphviz yara build-essential && \
    pip install --no-cache-dir /tmp/sysdiagnose*.whl && \
    rm -rf /tmp/sysdiagnose*.whl && \
    apt-mark auto build-essential && \
    apt-get remove -y build-essential && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/archives/*

WORKDIR /cases

ENTRYPOINT ["saf"]