# Trade Ingestor Service

This service is responsible for ingesting trade data from a multiple crypto exchanges, such as Kraken, and pushing them to the message bus.

It currently supports only Kraken.

## How to run
From the root of the project:

```bash
# Run in dev mode (with hot reloading)
make dev svc=trades

# Run in production mode (no hot reloading)
make run svc=trades
```
