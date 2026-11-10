FROM python:3.12-slim

RUN groupadd --gid 1000 zeno \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/sh zeno
WORKDIR /workspace
USER 1000:1000
CMD ["sh"]
