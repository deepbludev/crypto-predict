from typing import Annotated

import comet_ml
import joblib
from xgboost import XGBRegressor

from price_predictions.core.settings import Settings
from price_predictions.model.xgboost import XGBoostModel


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

    def get_model_from_registry(
        self,
    ) -> tuple[XGBRegressor, Annotated[str, "experiment_key"]]:
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


if __name__ == "__main__":
    predictor = PricePredictor(settings=Settings())
