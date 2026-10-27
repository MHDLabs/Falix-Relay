# Falix-Relay v1 — official Xray-core, checksum-pinned release assets.
FROM alpine:3.22 AS xray-download
ARG TARGETARCH
ARG XRAY_VERSION=v26.10.21

RUN apk add --no-cache ca-certificates curl unzip
RUN set -eux; case "$TARGETARCH" in amd64) archive="Xray-linux-64.zip"; expected="0eec3ed4163c273d8c8bf821f7d219e257921cf584aa3fb970715e458e631978";; arm64) archive="Xray-linux-arm64-v8a.zip"; expected="d1304946c486d98e6b886e9b931eaaaebb23835b30e217638037b7f2721d4e9c";; *) echo "Unsupported TARGETARCH: $TARGETARCH (supported: amd64, arm64)" >&2; exit 1;; esac; curl --fail --location --silent --show-error --retry 3 "https://github.com/XTLS/Xray-core/releases/download/$XRAY_VERSION/$archive" -o /tmp/xray.zip; printf '%s  %s\n' "$expected" /tmp/xray.zip | sha256sum -c -; mkdir -p /tmp/xray-dist /out; unzip -q /tmp/xray.zip -d /tmp/xray-dist; test -x /tmp/xray-dist/xray; install -m 0755 /tmp/xray-dist/xray /out/xray

FROM alpine:3.22
LABEL org.opencontainers.image.title="Falix-Relay" org.opencontainers.image.description="Minimal, headless VLESS-WebSocket relay powered by official Xray-core" org.opencontainers.image.source="https://github.com/MHDLabs/Falix-Relay"
RUN addgroup -S -g 10001 relay && adduser -S -D -H -u 10001 -G relay relay && apk add --no-cache ca-certificates
COPY --from=xray-download /out/xray /usr/local/bin/xray
COPY --chown=0:0 entrypoint.sh /usr/local/bin/falix-relay
COPY --chown=0:0 config.template.json /etc/falix-relay/config.template.json
RUN chmod 0555 /usr/local/bin/falix-relay && chmod 0444 /etc/falix-relay/config.template.json
ENV PORT=8080
ENV WS_PATH=/relay
EXPOSE 8080/tcp
USER 10001:10001
ENTRYPOINT ["/usr/local/bin/falix-relay"]
