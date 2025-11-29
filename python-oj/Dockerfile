FROM python:3.11-slim

ARG HOST_UID=1000
ARG HOST_GID=1000

# Create non-root user with SAME UID/GID as host
RUN groupadd -g ${HOST_GID} runner \
    && useradd -m -u ${HOST_UID} -g ${HOST_GID} runner

WORKDIR /workspace

USER runner

CMD ["python", "main.py"]
