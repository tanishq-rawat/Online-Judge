FROM gcc:12-bookworm

ARG HOST_UID=1000
ARG HOST_GID=1000

# Create non-root user with SAME UID/GID as host
RUN groupadd -g ${HOST_GID} runner \
    && useradd -m -u ${HOST_UID} -g ${HOST_GID} runner

WORKDIR /workspace

USER runner

CMD ["./main"]