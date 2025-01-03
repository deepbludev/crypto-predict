from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Self, Sequence, cast

import pandas as pd

from domain.core import DeploymentEnv


class ModelStatus(str, Enum):
    NONE = "None"
    DEV = "Development"
    STAGING = "Staging"
    QA = "QA"
    PROD = "Production"

    @classmethod
    def from_deployment_env(cls, deployment_env: DeploymentEnv):
        match deployment_env:
            case DeploymentEnv.DEV:
                return cls.DEV
            case DeploymentEnv.STAGING:
                return cls.STAGING
            case DeploymentEnv.PROD:
                return cls.PROD


class CryptoPricePredictionModel(ABC):
    def __init__(self, name: str, status: ModelStatus = ModelStatus.NONE):
        self.name = name
        self.status = status

    @abstractmethod
    def unpack_model(self) -> Any:
        """
        Unpack the model object. It should return the internal model object, such as
        a `XGBRegressor` object.
        """
        ...

    @abstractmethod
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
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
    def predict(self, X: pd.DataFrame) -> Sequence[float]:
        """
        Predict the target.

        Args:
            X (pd.DataFrame): The features dataframe.

        Returns:
            pd.Series: The predicted target series.
        """
        ...


class DummyModel(CryptoPricePredictionModel):
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
        super().__init__(name="dummy", status=ModelStatus.NONE)
        self.feature = feature

    def unpack_model(self):
        return self

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_search_trials: int = 0,
        n_splits: int = 3,
    ) -> Self:
        return self

    def predict(self, X: pd.DataFrame) -> Sequence[float]:
        try:
            return cast(Sequence[float], X[self.feature])
        except KeyError as e:
            raise ValueError(
                f"Feature '{self.feature}' not found in the X dataframe. {e}"
            ) from e