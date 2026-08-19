FROM python:3.12-slim

ARG FORWARDER_UID=65532
ARG FORWARDER_GID=65532

RUN groupadd --gid "${FORWARDER_GID}" phantomnet && \
    useradd --uid "${FORWARDER_UID}" --gid phantomnet --no-create-home --shell /usr/sbin/nologin phantomnet

WORKDIR /opt/phantomnet
COPY integrations /opt/phantomnet/integrations

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/phantomnet

USER phantomnet:phantomnet
ENTRYPOINT ["python", "-m", "integrations.wazuh_pilot_forwarder.forwarder"]
