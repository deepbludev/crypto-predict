import json
from typing import Annotated, Any, cast

import comet_ml
import joblib
from pydantic import Field, computed_field
from xgboost import XGBRegressor

from domain.candles import CandleTimeframe
from domain.core import Schema
from domain.trades import Asset, Symbol
from price_predictions.core.settings import Settings
from price_predictions.fstore import PricePredictionsStore
from price_predictions.model.xgboost import XGBoostModel


class PricePrediction(Schema):
    symbol: Symbol
    timeframe: CandleTimeframe
    horizon: int = Field(..., description="The horizon of the prediction in seconds")
    close_time: int
    predicted: float

    @computed_field
    @property
    def key(self) -> str:
        return (
            f"{self.symbol.value}-"
            f"{self.timeframe.value}x{self.horizon}-"
            f"{self.prediction_timestamp}"
        )

    @computed_field
    @property
    def prediction_timestamp(self) -> int:
        return self.close_time + self.horizon * self.timeframe.to_sec()

    @computed_field
    @property
    def asset(self) -> Asset:
        return self.symbol.to_asset()


class PricePredictor:
    """
    Class to predict the price of an asset.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.symbol = settings.symbol
        self.timeframe = settings.timeframe
        self.target_horizon = settings.target_horizon
        self.model_name = XGBoostModel.model_name(
            symbol=self.symbol,
            timeframe=self.timeframe,
            target_horizon=self.target_horizon,
        )

        self.comet_api = comet_ml.api.API(api_key=self.settings.comet_ml_api_key)
        self.model, self.exp_key = self.get_model_from_registry()
        self.fstore = self.get_fstore()

    def get_model_from_registry(
        self,
    ) -> tuple[XGBRegressor, Annotated[str, "exp_key"]]:
        """
        Get the latest model from the registry and return it as a tuple of the model
        and the experiment key.
        """
        model = self.comet_api.get_model(
            workspace=self.settings.comet_ml_workspace,
            model_name=self.model_name,
        )
        latest_version: str = next(iter(sorted(model.find_versions(), reverse=True)))
        model.download(version=latest_version, output_folder="./")

        exp_key: str = model.get_details(latest_version)["experimentKey"]
        xgboost_model = joblib.load(filename=f"./{self.model_name}.joblib")

        return xgboost_model, exp_key

    def get_fstore(self) -> PricePredictionsStore:
        """
        Create the feature store using the parameters from the experiment,
        such as the feature view name, version, and TA features.
        """
        assert (exp := self.comet_api.get_experiment_by_key(self.exp_key))

        def get_param(param_name: str) -> str:
            return cast(dict[str, Any], exp.get_parameters_summary(param_name))[
                "valueCurrent"
            ]

        return PricePredictionsStore(
            settings=self.settings,
            fview_base_name=get_param("fview_name").split("__")[0],
            fview_version=int(get_param("fview_version")),
            ta_features=json.loads(get_param("ta_features")),
        )

    def predict(self) -> PricePrediction:
        """
        Predict the price of the asset using the latest feature vector,
        projecting it forward to the target horizon.
        """
        feature_vectors = self.fstore.get_inference_features()
        close_time = feature_vectors["close_time"].iloc[0]
        prediction = self.model.predict(feature_vectors)[0]

        return PricePrediction(
            symbol=self.symbol,
            timeframe=self.timeframe,
            horizon=self.target_horizon,
            close_time=close_time,
            predicted=prediction,
        )
