FROM python:3.12-slim

# Debian's Node.js package provides a maintained system Node runtime without
# adding npm packages or changing the Python runtime image.
RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates coreutils nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 zeno \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/sh zeno

WORKDIR /workspace
USER 1000:1000
CMD ["sh"]
