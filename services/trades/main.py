from loguru import logger
from trades.core.settings import trades_settings
from trades.kraken import KrakenWebsocketAPI


def main():
    settings = trades_settings()
    kraken = KrakenWebsocketAPI(settings.symbols)
    while True:
        trades = kraken.get_trades()
        for trade in trades:
            logger.info(trade)


if __name__ == "__main__":
    main()
