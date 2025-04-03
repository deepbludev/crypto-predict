# Crypto Price Predictor

This repository contains the code for the Crypto Price Predictor project, a machine learning system designed to predict cryptocurrency price movements by combining real-time market data with news sentiment analysis.

![image]([files/Users/jzhang/Desktop/Isolated.png](https://i.postimg.cc/qBbGLkgB/059e3380-dddb-49ce-8419-e4ed520c4f6a.gif))

## Project Overview
The system ingests two main types of data:
1. Real-time cryptocurrency trades that are transformed into technical analysis features
2. Cryptocurrency news that are analyzed for sentiment signals

These features will be used to train machine learning models for price prediction (model training and inference components are planned but not yet implemented).

The project follows a FTI (Feature, Transform, Inference) architecture, implemented as a cluster of microservices that process data in real-time. Each component in the pipeline transforms raw data into increasingly refined features suitable for machine learning:

- Market Data Pipeline: Trades → Candles → Technical Indicators → Features
- News Pipeline: News Articles → Sentiment Analysis → Sentiment Signals → Features

## Services Overview
The project consists of several microservices that communicate through a message bus using the Quix SDK. Each service is implemented as a FastAPI application.

### Data Ingestion Services
- **Trades Service:** Ingests real-time cryptocurrency trades
  - Connects to Kraken websocket API for live trade data
  - Produces trade events to the message bus
  - Extensible design to support additional exchanges

- **News Signals Service:** Processes cryptocurrency news and sentiment
  - Analyzes news content for market sentiment
  - Produces sentiment signals to the message bus
  - Helps capture market sentiment impact on prices

### Processing Services
- **Candles Service:** Aggregates trades into candlestick data
  - Consumes raw trades from the message bus
  - Produces candlestick data at configurable timeframes
  - Supports multiple trading pairs

- **Technical Analysis Service:** Calculates market indicators
  - Processes candlestick data from the message bus
  - Computes various technical analysis indicators
  - Produces indicator data to the message bus

- **Features Service:** Generates model-ready features
  - Combines technical indicators and sentiment signals
  - Interfaces with the feature store
  - Prepares data for model training and inference

## Configuration
Each service can be configured through environment variables. Example configurations can be found in:
- `services/features/.env`
- `services/ta/.env`

## Running the Services

### Local Development
To run a service in development mode:
```bash
make dev svc=<service_name>
```
Available services: `trades`, `candles`, `ta`, `features`, `news_signals`

### Production Deployment
The project is organized into several clusters that can be deployed independently:

- **Message Bus**: Core messaging infrastructure (Redpanda)
- **Indicators**: Technical analysis pipeline (trades → candles → ta → features)
- **Sentiment Signals**: News sentiment pipeline (news → news_signals → features)

Build services:
```bash
make build cluster=<cluster_name>           # Build entire cluster
make build cluster=<cluster_name> svc=<service_name>  # Build single service
```

Manage deployments:
```bash
# Whole cluster operations
make up cluster=<cluster_name>     # Start cluster services
make down cluster=<cluster_name>   # Stop and remove cluster services
make stop cluster=<cluster_name>   # Stop cluster services

# Single service operations within a cluster
make up cluster=<cluster_name> svc=<service_name>     # Start service
make down cluster=<cluster_name> svc=<service_name>   # Stop and remove service
make stop cluster=<cluster_name> svc=<service_name>   # Stop service
```

Available clusters:
- `messagebus`: Core message broker infrastructure
- `indicators`: Technical analysis pipeline
- `indicators_historical`: Historical data processing pipeline
- `sentiment_signals`: News sentiment analysis pipeline

Example deployments:
```bash
# Full deployment
# 1. Start the message bus
make up cluster=messagebus

# 2. Deploy the technical analysis pipeline
make up cluster=indicators

# 3. Deploy the sentiment analysis pipeline
make up cluster=sentiment_signals

# Single service deployment example
make up cluster=indicators svc=trades    # Deploy only the trades service
```

## Prerequisites
- Docker and Docker Compose
- Kafka broker (for message bus)
- Python 3.12+
- Make

## Architecture
The services follow a streaming architecture pattern where:
1. Data is ingested from multiple sources (trades, news)
2. Processed through various transformations (candles, technical analysis)
3. Features are generated for downstream machine learning tasks

Each service is independently deployable and scalable, communicating through the message bus for resilience and decoupling.
