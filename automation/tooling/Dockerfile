FROM node:24.22.0-bookworm-slim@sha256:a5f4366e834695d5f363b920c104953a535d3a9864d1bdf74566a0ebe01daee5 AS node
FROM rust:1.99.1-slim-bookworm@sha256:a24e292b4af7bdee351a31d3a6379972a5652f0ea22a1b6d6883324ac4f5097c AS rust
RUN rustup component add clippy rustfmt llvm-tools
FROM ghcr.io/astral-sh/ruff:0.16.8@sha256:ec3c84a063840fc9a678004f4d958ea4e1e79de1ee3f94dc0f0df3a4a3a1f1a7 AS ruff
FROM koalaman/shellcheck:v0.11.0@sha256:61862eba1fcf09a484ebcc6feea46f1782532571a34ed51fedf90dd25f925a8d AS shellcheck
FROM mvdan/shfmt:v3.14.1@sha256:8c06884a35683d8763fba6c0d9484d11a61a96da65f8d497d6f625825a6043f2 AS shfmt
FROM python:3.13.16-slim-bookworm@sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641

RUN rm /etc/apt/sources.list.d/debian.sources && \
    printf '%s\n' \
      'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20261018T000000Z/ bookworm main' \
      'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20261018T000000Z/ bookworm-updates main' \
      'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian-security/20261018T000000Z/ bookworm-security main' \
      > /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends bash git make gcc libc6-dev ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm
COPY --from=rust /usr/local/cargo/bin /usr/local/cargo/bin
COPY --from=rust /usr/local/rustup /usr/local/rustup
COPY --from=ruff /ruff /usr/local/bin/ruff
COPY --from=shellcheck /bin/shellcheck /usr/local/bin/shellcheck
COPY --from=shfmt /bin/shfmt /usr/local/bin/shfmt

WORKDIR /opt/quality
COPY automation/tooling/requirements.txt ./requirements.txt
RUN python3 -m pip install --no-cache-dir --only-binary=:all: --require-hashes -r requirements.txt
COPY package.json package-lock.json eslint.config.mjs ./
RUN npm ci --ignore-scripts --no-audit --no-fund && npm cache clean --force
COPY automation/tooling/entrypoint.bash /usr/local/bin/raicho-tooling
COPY mailprobe/tests/ /opt/raicho/mailprobe/tests/
RUN install -d -o 10001 -g 10001 -m 0700 /config /artifact

ENV PATH="/opt/quality/node_modules/.bin:/usr/local/cargo/bin:${PATH}" \
    RUSTUP_HOME=/usr/local/rustup CARGO_HOME=/tmp/cargo \
    CARGO_TARGET_DIR=/tmp/raicho-target CARGO_BUILD_WARNINGS=deny \
    PYTHONDONTWRITEBYTECODE=1 RUFF_CACHE_DIR=/tmp/ruff \
    npm_config_cache=/tmp/npm HOME=/tmp/home RAICHO_TOOLING_CONTAINER=1
WORKDIR /workspace
ENTRYPOINT ["bash", "/usr/local/bin/raicho-tooling"]
CMD ["make", "lint", "format-check", "typecheck", "test-python"]
