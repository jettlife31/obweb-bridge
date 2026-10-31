FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    XDG_STATE_HOME=/var/lib/obweb-bridge/state \
    OBWEB_RUNTIME_DIR=/var/lib/obweb-bridge/runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates iproute2 nftables procps util-linux \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin obweb \
    && mkdir -p /app /var/lib/obweb-bridge/state /run/netns \
    && chown -R obweb:obweb /var/lib/obweb-bridge

WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY gateway.py network.py wire.py dns_proxy.py login_web.py memory_card.py service.py select_interface.py container_interfaces.py container-entrypoint.sh ./
COPY third_party/ ./third_party/
COPY assets/ ./assets/
RUN chmod 0555 /app/container-entrypoint.sh

EXPOSE 53/udp 53/tcp
ENTRYPOINT ["/app/container-entrypoint.sh"]
