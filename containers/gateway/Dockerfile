FROM nginx:1.30.6-alpine@sha256:970364228b1e4f932abc22d321932816782cca8a20b85a77552a7cfe9acfb3b5

COPY runtime/gateway/nginx.conf /etc/nginx/nginx.conf
USER 10001:10001
HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=3 \
    CMD ["nginx", "-t"]
ENTRYPOINT ["nginx", "-g", "daemon off;"]
