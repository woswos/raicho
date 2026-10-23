FROM node:24.22.0-bookworm-slim@sha256:a5f4366e834695d5f363b920c104953a535d3a9864d1bdf74566a0ebe01daee5 AS extension

RUN rm /etc/apt/sources.list.d/debian.sources && \
    printf '%s\n' \
      'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20261018T000000Z/ bookworm main' \
      'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/20261018T000000Z/ bookworm-security main' \
      > /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends python3 && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund
ENV PATH="/build/node_modules/.bin:${PATH}"
COPY extension/ extension/
COPY protocol/typescript/ protocol/typescript/
ARG RAICHO_EXTENSION_VERSION
ARG RAICHO_EXTENSION_SOURCE=extension
RUN if [ -n "${RAICHO_EXTENSION_VERSION}" ]; then \
      set -- --version "${RAICHO_EXTENSION_VERSION}"; \
    else set --; fi && \
    python3 -B -m extension.raicho_build_extension --source-root "${RAICHO_EXTENSION_SOURCE}" \
      --output-directory /artifact "${@}"

FROM debian:bookworm-slim@sha256:7c7b2c966bc9ee8cedfeef67e0e279108992c77681fa595db4a9d65c06ccc587 AS download

RUN rm /etc/apt/sources.list.d/debian.sources && \
    printf '%s\n' \
      'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20261018T000000Z/ bookworm main' \
      'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/20261018T000000Z/ bookworm-security main' \
      > /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends ca-certificates curl xz-utils && \
    rm -rf /var/lib/apt/lists/*

RUN test "$(dpkg --print-architecture)" = amd64 && \
    curl --fail --location --retry 3 \
      https://archive.mozilla.org/pub/thunderbird/releases/153.5.0esr/linux-x86_64/en-US/thunderbird-153.5.0esr.tar.xz \
      --output /tmp/thunderbird.tar.xz && \
    printf '%s\n' \
      '4b5c4a988307876f861b3e40ece13a8fac4707347d573332b35319bf1d4d9f45534076decc34e23fee6de8e75f65eead4620ca435a8ab0f20dfcc6e2a6ec5850  /tmp/thunderbird.tar.xz' \
      | sha512sum --check && \
    tar -xJf /tmp/thunderbird.tar.xz -C /opt && rm /tmp/thunderbird.tar.xz

RUN curl --fail --location --retry 3 \
      https://github.com/novnc/noVNC/archive/refs/tags/v1.7.0.tar.gz \
      --output /tmp/novnc.tar.gz && \
    printf '%s\n' \
      'b1003a11b6e6e8d8f7f5e5586daae7f8ca651d8aee0aa155ff9ac841c48f52c6  /tmp/novnc.tar.gz' \
      | sha256sum --check && \
    mkdir /opt/novnc && tar -xzf /tmp/novnc.tar.gz --strip-components=1 -C /opt/novnc && \
    rm /tmp/novnc.tar.gz

FROM debian:bookworm-slim@sha256:7c7b2c966bc9ee8cedfeef67e0e279108992c77681fa595db4a9d65c06ccc587

COPY --from=download /etc/apt/sources.list /etc/apt/sources.list
RUN rm /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates dbus fonts-dejavu-core libasound2 libdbus-glib-1-2 libgbm1 \
      libgtk-3-0 libpci3 libx11-xcb1 libxt6 openbox python3 tini \
      websockify x11-utils x11vnc xvfb && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd --gid 10001 raicho && \
    useradd --uid 10001 --gid 10001 --home-dir /config --no-create-home --shell /usr/sbin/nologin raicho && \
    install -d -o 10001 -g 10001 -m 0700 /config /config/profile && \
    mkdir -p /opt/raicho && \
    dpkg-query --show > /opt/raicho/packages.tsv

COPY --from=download /opt/thunderbird /opt/thunderbird
COPY --from=download /opt/novnc /usr/share/novnc
COPY --from=extension /artifact/ /opt/raicho/extension/
COPY runtime/thunderbird/runtime.py runtime/thunderbird/supervisor.py \
    runtime/thunderbird/healthcheck.py runtime/thunderbird/policy.py /opt/raicho/
RUN mkdir -p /opt/thunderbird/distribution && \
    ln -s /tmp/raicho-runtime/policies.json /opt/thunderbird/distribution/policies.json

ENV HOME=/config DISPLAY=:99 XDG_RUNTIME_DIR=/tmp/raicho-runtime \
    DBUS_SESSION_BUS_ADDRESS=unix:path=/tmp/raicho-runtime/bus \
    PYTHONDONTWRITEBYTECODE=1 MOZ_ENABLE_WAYLAND=0 RAICHO_ADMIN_ENABLED=false
USER 10001:10001
VOLUME ["/config"]
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python3", "/opt/raicho/healthcheck.py"]
ENTRYPOINT ["/usr/bin/tini", "--", "python3", "/opt/raicho/runtime.py"]
