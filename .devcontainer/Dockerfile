# fusesoc dev container
FROM mcr.microsoft.com/devcontainers/python:3.12

# extraneous package manifest:
#   subversion
#   openssh-client
#   iverilog
#   verilator
#   make
RUN apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends \
        subversion \
        openssh-client \
        iverilog \
        verilator \
        make \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# slang-server: (https://github.com/hudson-trading/slang-server)
# bump version as necessary
ARG SLANG_SERVER_VERSION=v0.3.0
RUN set -eu; \
    case "$(uname -m)" in \
        x86_64)  asset=slang-server-linux-x64 ;; \
        aarch64) asset=slang-server-linux-arm64 ;; \
        *) echo "unsupported architecture: $(uname -m)" >&2; exit 1 ;; \
    esac; \
    url="https://github.com/hudson-trading/slang-server/releases/download/${SLANG_SERVER_VERSION}/${asset}.tar.gz"; \
    curl -fsSL "$url" -o /tmp/slang-server.tar.gz; \
    tar -xzf /tmp/slang-server.tar.gz -C /usr/local/bin ./slang-server; \
    chmod 0755 /usr/local/bin/slang-server; \
    rm /tmp/slang-server.tar.gz; \
    slang-server --version

# Trust GitHub's SSH host keys system-wide so that git operations over SSH
# (e.g. pushing to a fork) don't stop at an interactive "authenticity of host"
# prompt on first use. The keys themselves are never copied into the image:
# VS Code forwards the host's ssh-agent into the container (see
# devcontainer.json), so private keys stay on the host.
RUN mkdir -p /etc/ssh \
    && ssh-keyscan -t rsa,ecdsa,ed25519 github.com >> /etc/ssh/ssh_known_hosts

# The workspace is bind-mounted from the host and its top-level directory can
# show up as owned by a different uid than the "vscode" user (this is the case
# with Docker Desktop on macOS). Git then refuses to operate on it with
# "detected dubious ownership", which also breaks pre-commit. Mark all
# directories as safe; inside a single-user dev container this is harmless.
RUN git config --system --add safe.directory '*'

# Keep pip quiet and skip the version nag inside the container.
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# The base image ships a pytest installed with pipx into an isolated venv, and
# puts that venv's bin dir ahead of /usr/local/bin on PATH (via
# /etc/profile.d/00-restore-env.sh). That pytest cannot import fusesoc or its
# dependencies. Remove it so that a bare "pytest" resolves to the one
# installed from dev-requirements.txt below, which shares the interpreter
# fusesoc is installed into.
RUN PIPX_HOME=/usr/local/py-utils PIPX_BIN_DIR=/usr/local/py-utils/bin \
    pipx uninstall pytest

# Install the Python packages needed to develop fusesoc (pre-commit, pytest,
# tox) at image build time so they are available immediately and don't have to
# be re-downloaded on every container creation. Only the requirements file is
# copied in; the source tree itself is bind-mounted by VS Code and installed in
# editable mode by postCreateCommand (see devcontainer.json).
COPY dev-requirements.txt /tmp/dev-requirements.txt
RUN pip install -r /tmp/dev-requirements.txt \
    && rm /tmp/dev-requirements.txt
