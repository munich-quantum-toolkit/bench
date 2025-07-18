# syntax=docker/dockerfile:1.9

# Adapted from https://hynek.me/articles/docker-uv/
FROM ubuntu:noble AS build

SHELL ["sh", "-exc"]

### Start build prep.

RUN <<EOT
apt-get update -qy
apt-get install -qyy \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    python3.12-dev \
    git
EOT

# Install `uv`
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# - Silence uv complaining about not being able to use hard links,
# - tell uv to byte-compile packages for faster application startups,
# - prevent uv from accidentally downloading isolated Python builds,
# - pick a Python,
# - and finally declare `/mqt-bench` as the target for `uv sync`.
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python3.12 \
    UV_PROJECT_ENVIRONMENT=/mqt-bench

### End build prep.

# Synchronize DEPENDENCIES and install the APPLICATION from `/src`.
# `/src` will NOT be copied into the runtime container.
COPY . /src
RUN --mount=type=cache,target=/root/.cache \
    cd /src && uv sync --frozen --no-dev --no-editable

##########################################################################

FROM ubuntu:noble
SHELL ["sh", "-exc"]

# Add the application virtualenv to search path.
ENV PATH=/mqt-bench/bin:$PATH

# Run application as non-root user.
RUN <<EOT
groupadd -r mqt-bench
useradd -r -d /mqt-bench -g mqt-bench -N mqt-bench
EOT

ENTRYPOINT ["mqt-bench"]
STOPSIGNAL SIGINT

# Note how the runtime dependencies differ from build-time ones.
# Notably, there is no uv either!
RUN <<EOT
apt-get update -qy
apt-get install -qyy \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    python3.12 \
    libpython3.12

apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
EOT

# Copy the pre-built `/app` directory to the runtime container
# and change the ownership to user app and group app in one step.
COPY --from=build --chown=mqt-bench:mqt-bench /mqt-bench /mqt-bench

USER mqt-bench
WORKDIR /mqt-bench

RUN <<EOT
python -V
mqt-bench --help
EOT
