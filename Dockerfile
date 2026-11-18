# syntax=docker/dockerfile:1

FROM python:3.14-slim-trixie AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.13.5@sha256:32a7bb39b496babbd997b0a39a4d66c126bdaf5661b302bf6f06abda8deca6ff /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,id=mqt-bench,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY . .
RUN --mount=type=cache,id=mqt-bench,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

FROM python:3.14-slim-trixie AS runtime

COPY --from=build /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

RUN useradd --system --user-group --create-home --home-dir /mqt-bench mqt-bench
USER mqt-bench
WORKDIR /mqt-bench

ENTRYPOINT ["mqt-bench"]
STOPSIGNAL SIGINT
