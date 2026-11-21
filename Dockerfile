# Hermes Job Assistant image: the official Hermes Agent image plus the Claude Code CLI.
#
# HERMES_TAG selects the upstream image. Set it in .env to a version (X.Y.Z) you have
# tested for reproducible builds; "stable" follows the upstream stable release gate.
ARG HERMES_TAG=stable
FROM nousresearch/hermes-agent:${HERMES_TAG}

# Fail a piped command if any stage of the pipe fails (e.g. a failed download).
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# The base image's entrypoint (s6-overlay) must start as root; it drops every
# Hermes process to the unprivileged `hermes` user itself.
# hadolint ignore=DL3002
USER 0

# Claude Code CLI, used by the Claude subscription provider plugin.
# The installer writes to /root/.local; copy the real binary to a system-wide
# path the `hermes` user can execute.
RUN curl -fsSL https://claude.ai/install.sh | bash \
 && cp -L /root/.local/bin/claude /usr/local/bin/claude \
 && chmod 755 /usr/local/bin/claude \
 && /usr/local/bin/claude --version

# Update Claude Code by rebuilding the image, not in place: the runtime user
# cannot write to /usr/local/bin.
ENV DISABLE_AUTOUPDATER=1

# Liveness: the supervised dashboard answers on 9119 (any HTTP status, including
# 401 from basic auth, means the service tree is up).
HEALTHCHECK --interval=60s --timeout=10s --start-period=120s --retries=3 \
  CMD ["sh", "-c", "curl -s -o /dev/null http://127.0.0.1:9119/ || exit 1"]
