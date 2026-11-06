# Development image: Python 3.12 (system) plus Node.js 22.12, pnpm and uv, pinned to the
# versions in .python-version, .nvmrc and frontend/package.json. pnpm is installed with npm
# because the corepack bundled with Node.js 22.12.0 cannot verify pnpm's signing keys.
FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

ARG NODE_VERSION=22.12.0
ARG PNPM_VERSION=10.33.0
ARG UV_VERSION=0.12.1
ARG GITLEAKS_VERSION=8.30.1
ARG SHELLCHECK_VERSION=0.11.0
ARG SHELLCHECK_SHA256_X64=8c3be12b05d5c177a04c29e3c78ce89ac86f1595681cab149b65b97c4e227198
ARG SHELLCHECK_SHA256_ARM64=12b331c1d2db6b9eb13cfca64306b1b157a86eb69db83023e261eaa7e7c14588

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
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in \
      amd64) sc_arch=x86_64; sc_sha="${SHELLCHECK_SHA256_X64}" ;; \
      arm64) sc_arch=aarch64; sc_sha="${SHELLCHECK_SHA256_ARM64}" ;; \
      *) echo "unsupported architecture: $arch" >&2; exit 1 ;; \
    esac; \
    file="shellcheck-v${SHELLCHECK_VERSION}.linux.${sc_arch}.tar.xz"; \
    cd /tmp; \
    curl -fsSLO "https://github.com/koalaman/shellcheck/releases/download/v${SHELLCHECK_VERSION}/${file}"; \
    echo "${sc_sha}  ${file}" | sha256sum -c -; \
    tar -xJf "${file}"; \
    install -m 0755 "shellcheck-v${SHELLCHECK_VERSION}/shellcheck" /usr/local/bin/shellcheck; \
    rm -rf /tmp/shellcheck-*

USER vscode
