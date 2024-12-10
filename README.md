# Crypto Price Predictor

This repository contains the code for the Crypto Price Predictor project.
It is a cluster of services following a FTI architecture.

## Feature Pipeline
The feature pipeline is composed of the following services. They are all spun up as FastAPI services
and process messages from the messagebus using the Quix SDK.

- **Trades:** Ingests trades from Kraken and produces them to the messagebus.
  - Uses the Kraken websocket API to get the trades.
  - Supports only Kraken for now, but other exchanges can be added similarly.
  
- **Candles:** Ingests trades and produces candles.
  - Consumes trades from the messagebus.
  - Produces candles to the messagebus.
  - Candle timeframe is configurable.
  
- **Technical Analysis:** Ingests candles and produces technical analysis.
  - Consumes candles from the messagebus.
  - Calculates technical analysis indicators.
  - Produces technical analysis to the messagebus.

- **Features:** Ingests technical analysis and produces features.
  - Consumes technical analysis from the messagebus.
  - Loads the features from the feature store.


## How to run
To run the services, you need to have a Kafka broker running.

Use the following command to run a service. The possible services are: `trades`, `candles`, `ta`, `features`.

```bash
make run svc=<service_name>
```
And in dev mode:
```bash
make dev svc=<service_name>
```

To build and run all the services using docker compose, use the following command:
```bash
make build
```

To up, down or stop the docker compose services, use the following commands:
```bash
make up
make down
make stop
```

A specific service option can be passed to the command to only run a specific service.
```bash
make build svc=<service_name>
make up svc=<service_name>
make down svc=<service_name>
make stop svc=<service_name>
```
