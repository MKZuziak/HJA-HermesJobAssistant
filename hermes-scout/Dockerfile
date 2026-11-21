# Start from the official Hermes image
FROM nousresearch/hermes-agent:latest

# Build steps below need admin rights; at runtime Hermes still switches to uid 10000
USER root

# Install Claude Code with Anthropic's official installer (lands in /root/.local)
RUN curl -fsSL https://claude.ai/install.sh | bash

# Copy the real program to a system-wide location the Hermes user can reach
RUN cp -L /root/.local/bin/claude /usr/local/bin/claude

# Let every user run it
RUN chmod 755 /usr/local/bin/claude

# Stop Claude Code from trying to update itself; update by rebuilding instead
ENV DISABLE_AUTOUPDATER=1
