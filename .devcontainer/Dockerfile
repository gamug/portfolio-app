# Development image: Python 3.12 (system) plus Node.js 22.12, pnpm and uv, pinned to the
# versions in .python-version, .nvmrc and frontend/package.json. pnpm is installed with npm
# because the corepack bundled with Node.js 22.12.0 cannot verify pnpm's signing keys.
FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

ARG NODE_VERSION=22.12.0
ARG PNPM_VERSION=10.33.0
ARG UV_VERSION=0.12.1
ARG GITLEAKS_VERSION=8.30.1

RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in amd64) node_arch=x64 ;; arm64) node_arch=arm64 ;; *) echo "unsupported architecture: $arch" >&2; exit 1 ;; esac; \
    curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${node_arch}.tar.xz" | tar -xJ -C /usr/local --strip-components=1; \
    npm install -g "pnpm@${PNPM_VERSION}"; \
    pip install --no-cache-dir "uv==${UV_VERSION}"

RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in amd64) gl_arch=x64 ;; arm64) gl_arch=arm64 ;; *) echo "unsupported architecture: $arch" >&2; exit 1 ;; esac; \
    base="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}"; \
    cd /tmp; \
    curl -fsSLO "${base}/gitleaks_${GITLEAKS_VERSION}_linux_${gl_arch}.tar.gz"; \
    curl -fsSLO "${base}/gitleaks_${GITLEAKS_VERSION}_checksums.txt"; \
    sha256sum --ignore-missing -c "gitleaks_${GITLEAKS_VERSION}_checksums.txt"; \
    tar -xzf "gitleaks_${GITLEAKS_VERSION}_linux_${gl_arch}.tar.gz" -C /usr/local/bin gitleaks; \
    rm -f /tmp/gitleaks_*

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends shellcheck; \
    rm -rf /var/lib/apt/lists/*

USER vscode
