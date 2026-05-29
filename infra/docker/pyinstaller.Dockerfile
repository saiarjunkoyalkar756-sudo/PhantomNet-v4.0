# Dockerfile.pyinstaller
# This Dockerfile is used to create a build environment for PyInstaller
# to cross-compile Linux executables.

FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYINSTALLER_VERSION="5.13.2" # Use a specific version for reproducibility

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libz-dev \
        libssl-dev \
        zlib1g-dev \
        upx-ucl \
    && rm -rf /var/lib/apt/lists/*

# Install PyInstaller
RUN pip install --no-cache-dir "pyinstaller==$PYINSTALLER_VERSION"

# Set the working directory
WORKDIR /src

# By not adding a CMD or ENTRYPOINT, this image can be used by mounting
# the project directory and running pyinstaller commands directly.
# Example: docker run --rm -v $(pwd):/src pyinstaller-builder "pyinstaller phantomnet_agent/pyinstaller/agent-linux.spec"
