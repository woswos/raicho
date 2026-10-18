ARG TOOLING_IMAGE=raicho-tools:local
ARG THUNDERBIRD_IMAGE=raicho-thunderbird:local
FROM ${TOOLING_IMAGE} AS probe
WORKDIR /build
COPY devbin/raicho_build_extension.py devbin/raicho_build_extension.py
COPY extension/mail_probe/ extension/mail_probe/
RUN python3 -B devbin/raicho_build_extension.py \
    --source-root /build/extension/mail_probe --output-directory /artifact

FROM ${THUNDERBIRD_IMAGE}
COPY --from=probe /artifact/ /opt/raicho/extension/
COPY containers/mail_profile/ /mail_profile/
ENV LD_LIBRARY_PATH=/opt/thunderbird
ENTRYPOINT ["/usr/bin/tini", "--", "python3", "-B", "/mail_profile/start.py"]
