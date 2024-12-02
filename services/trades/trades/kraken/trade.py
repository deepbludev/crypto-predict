from typing import Any

from trades.trade import Trade


class KrakenTrade(Trade):
    @classmethod
    def from_api(cls, api_trade: dict[str, Any]) -> Trade:
        return Trade.model_validate(api_trade | dict(volume=api_trade["qty"]))
