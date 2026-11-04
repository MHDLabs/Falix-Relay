# Falix-Relay, official Xray-core with verified release assets.
FROM alpine:3.24.3 AS xray-download

ARG TARGETARCH
ARG XRAY_VERSION=v26.10.31

RUN apk add --no-cache ca-certificates curl unzip

RUN set -eux; \
    case "$TARGETARCH" in \
      amd64) \
        archive="Xray-linux-64.zip"; \
        expected="e4bd9119f50ae7c41658b1abd0679ae06f98bd864a2907ff33f2f2cf7081b214" ;; \
      arm64) \
        archive="Xray-linux-arm64-v8a.zip"; \
        expected="1811c8f1da0c3b6dc707ebaf1c8390e987ba39859a8f0a7aadd8526157f2ec8d" ;; \
      *) \
        echo "Unsupported TARGETARCH: $TARGETARCH (supported: amd64, arm64)" >&2; \
        exit 1 ;; \
    esac; \
    curl --fail --location --silent --show-error --retry 3 \
      "https://github.com/XTLS/Xray-core/releases/download/$XRAY_VERSION/$archive" \
      -o /tmp/xray.zip; \
    printf '%s  %s\n' "$expected" /tmp/xray.zip | sha256sum -c -; \
    mkdir -p /tmp/xray-dist /out; \
    unzip -q /tmp/xray.zip -d /tmp/xray-dist; \
    test -x /tmp/xray-dist/xray; \
    install -m 0755 /tmp/xray-dist/xray /out/xray

FROM alpine:3.24.3

LABEL org.opencontainers.image.title="Falix-Relay" \
      org.opencontainers.image.description="Minimal VLESS-WebSocket relay powered by official Xray-core" \
      org.opencontainers.image.source="https://github.com/MHDLabs/Falix-Relay"

RUN addgroup -S -g 10001 relay \
    && adduser -S -D -H -u 10001 -G relay relay \
    && apk add --no-cache ca-certificates

COPY --from=xray-download /out/xray /usr/local/bin/xray
COPY --chown=0:0 entrypoint.sh /usr/local/bin/falix-relay
COPY --chown=0:0 config.template.json /etc/falix-relay/config.template.json

RUN chmod 0555 /usr/local/bin/falix-relay \
    && chmod 0444 /etc/falix-relay/config.template.json

ENV PORT=8080
ENV WS_PATH=/relay

EXPOSE 8080/tcp

USER 10001:10001
ENTRYPOINT ["/usr/local/bin/falix-relay"]
