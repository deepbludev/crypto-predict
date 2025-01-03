from abc import ABC, abstractmethod
from typing import Self, cast

import pandas as pd
from pandera.typing import Series


class CryptoPricePredictionModel(ABC):
    @abstractmethod
    def fit(
        self,
        X: pd.DataFrame,
        y: Series[float],
        n_search_trials: int = 0,
        n_splits: int = 3,
    ) -> Self:
        """
        Train the model.

        Args:
            X (pd.DataFrame): The features dataframe.
            y (pd.Series): The target series.
            n_search_trials (int): The number of search trials for the hyperparam
                tuning.
            n_splits (int): The number of splits for the cross-validation.
        """
        ...

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> Series[float]:
        """
        Predict the target.

        Args:
            X (pd.DataFrame): The features dataframe.

        Returns:
            pd.Series: The predicted target series.
        """
        ...


class CryptoPricePredictionDummyModel(CryptoPricePredictionModel):
    """
    A dummy model that predicts the crypto price using the value of a given feature,
    defaulting to the 'close' feature, in order to simulate a dummy prediction based on
    the current price.
    """

    def __init__(self, feature: str = "close"):
        """
        Initialize the dummy model using the given feature name as the dummy prediction.

        Args:
            feature: The feature to use as the dummy prediction (default: 'close').
        """
        self.feature = feature

    def fit(
        self,
        X: pd.DataFrame,
        y: Series[float],
        n_search_trials: int = 0,
        n_splits: int = 3,
    ) -> Self:
        return self

    def predict(self, X: pd.DataFrame) -> Series[float]:
        try:
            return cast(Series[float], X[self.feature])
        except KeyError as e:
            raise ValueError(
                f"Feature '{self.feature}' not found in the X dataframe. {e}"
            ) from e
