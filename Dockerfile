# syntax=docker/dockerfile:1

FROM python:3.14-slim-trixie AS base

FROM base AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl g++ git zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.13.5@sha256:32a7bb39b496babbd997b0a39a4d66c126bdaf5661b302bf6f06abda8deca6ff /uv /usr/local/bin/uv

# Native dependencies must run on CPUs other than the build runner.
ENV DEPLOY=ON \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /src

# Limit memory use in native dependency builds.
ARG CMAKE_BUILD_PARALLEL_LEVEL=2
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,id=mqt-bench-deploy,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY . .
RUN --mount=type=cache,id=mqt-bench-deploy,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

FROM base AS runtime

COPY --from=build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN useradd --system --user-group --create-home --home-dir /mqt-bench mqt-bench
USER mqt-bench
WORKDIR /mqt-bench

ENTRYPOINT ["mqt-bench"]
STOPSIGNAL SIGINT
