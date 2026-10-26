FROM node:24.22.0-bookworm-slim@sha256:a5f4366e834695d5f363b920c104953a535d3a9864d1bdf74566a0ebe01daee5 AS web
WORKDIR /source
COPY package.json package-lock.json .npmrc ./
RUN npm ci
ENV PATH="/source/node_modules/.bin:${PATH}"
COPY web/ web/
COPY assets/brand/ assets/brand/
RUN node web/build.mjs /output/web

FROM rust:1.99.1-slim-bookworm@sha256:a24e292b4af7bdee351a31d3a6379972a5652f0ea22a1b6d6883324ac4f5097c AS server
WORKDIR /source
COPY Cargo.toml Cargo.lock ./
COPY server/ server/
COPY protocol/ protocol/
ARG RAICHO_COMMIT=unknown
RUN RAICHO_COMMIT="$RAICHO_COMMIT" cargo build --release --locked --package raicho-server

FROM debian:bookworm-slim@sha256:7c7b2c966bc9ee8cedfeef67e0e279108992c77681fa595db4a9d65c06ccc587
RUN rm /etc/apt/sources.list.d/debian.sources && \
    printf '%s\n' \
      'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20261018T000000Z/ bookworm main' \
      'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20261018T000000Z/ bookworm-updates main' \
      'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/20261018T000000Z/ bookworm-security main' \
      > /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends ca-certificates curl && \
    mkdir -p /opt/raicho && dpkg-query -W > /opt/raicho/packages.tsv && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd --gid 10001 raicho && useradd --uid 10001 --gid 10001 --no-create-home raicho && \
    install -d -o 10001 -g 10001 -m 0700 /var/lib/raicho
COPY --from=server /source/target/release/raicho-server /usr/local/bin/raicho-server
COPY --from=web /output/web /usr/share/raicho/web
ENV RAICHO_BIND=0.0.0.0:8080 RAICHO_DATA_DIR=/var/lib/raicho RAICHO_WEB_DIR=/usr/share/raicho/web
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD ["curl", "--fail", "--silent", "--max-time", "3", "http://127.0.0.1:8080/health/ready"]
ENTRYPOINT ["/usr/local/bin/raicho-server"]
