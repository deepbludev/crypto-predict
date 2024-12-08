#!/bin/bash
# Installs the dependencies for the given service
# Usage: ./install_service_deps.sh <service_name>

SERVICE_NAME=$1

if [ "$SERVICE_NAME" = "trades" ]; then
  :

elif [ "$SERVICE_NAME" = "candles" ]; then
  :

elif [ "$SERVICE_NAME" = "ta" ]; then
  # Install build dependencies
  apt-get update && apt-get install -y \
    gcc \
    build-essential \
    wget &&
    rm -rf /var/lib/apt/lists/*

  # Install ta-lib
  echo "Installing ta-lib"
  wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz &&
    tar -xzf ta-lib-0.4.0-src.tar.gz &&
    cd ta-lib/ &&
    ./configure --prefix=/usr --build=aarch64-unknown-linux-gnu &&
    make &&
    make install &&
    cd .. &&
    rm -rf ta-lib*

else
  echo "Unknown service: $SERVICE_NAME"
  exit 1
fi
