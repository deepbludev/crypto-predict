# Crypto Price Predictor

This repository contains the code for the Crypto Price Predictor project.
It is a cluster of services following a FTI architecture.

## Services

- **Trades:** Ingest trades from Kraken and push them to the messagebus.
  - Spun up as a service using FastAPI.
  - Uses Quix SDK to connect to the messagebus.
  - Uses the Kraken websocket API to get the trades.
  - Supports only Kraken for now, but other exchanges can be added similarly.
