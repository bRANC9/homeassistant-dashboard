FROM almir/webhook:latest

LABEL org.opencontainers.image.source="https://github.com/bRANC9/homeassistant-dashboard"
LABEL org.opencontainers.image.description="Helios Dashboard webhook deployer"

USER root

RUN apk add --no-cache bash curl git python3 openssh-client

COPY deploy/deploy.sh /deploy/deploy.sh
COPY deploy/validate.sh /deploy/validate.sh
RUN chmod +x /deploy/deploy.sh /deploy/validate.sh

COPY deploy/hooks.json /etc/webhook/hooks.json

RUN mkdir -p /deploy/repo /deploy/.ssh && \
    chown -R webhook:webhook /deploy

USER webhook

EXPOSE 9000

ENTRYPOINT ["webhook"]
CMD ["-hooks", "/etc/webhook/hooks.json", "-verbose"]
