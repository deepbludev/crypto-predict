from datetime import datetime

from trades.core.settings import trades_settings
from trades.trade import Trade


def main():
    print("Hello from trades!")
    settings = trades_settings()
    print(settings)

    trades = [
        Trade(
            symbol=symbol,
            price=1.0,
            volume=1.0,
            timestamp=datetime.now(),
        )
        for symbol in settings.symbols
    ]
    print(trades)


if __name__ == "__main__":
    main()
