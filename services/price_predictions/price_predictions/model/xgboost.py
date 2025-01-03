from typing import Any, Self, Sequence, cast

import numpy as np
import optuna
import pandas as pd
from loguru import logger
from numpy.typing import NDArray
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBRegressor

from domain.candles import CandleTimeframe
from domain.trades import Symbol

from .base import CryptoPricePredictionModel, ModelStatus


class XGBoostModel(CryptoPricePredictionModel):
    """
    XGBoost model for crypto price predictions with hyperparam tuning.
    """

    def __init__(
        self,
        symbol: Symbol,
        timeframe: CandleTimeframe,
        target_horizon: int,
        status: ModelStatus,
        objective: str = "reg:absoluteerror",
        eval_metric: str = "mae",
    ):
        """
        Initialize the XGBoost model.

        Args:
            objective: The objective function to use.
            eval_metric: The evaluation metric to use.
        """
        self.objective = objective
        self.eval_metric = eval_metric
        self.model = XGBRegressor(objective=objective, eval_metric=eval_metric)
        name_base = "price_predictor_xgboost"
        name = f"{name_base}_{symbol.value}_{timeframe.value}x{target_horizon}"
        super().__init__(name, status)

    def unpack_model(self) -> XGBRegressor:
        return self.model

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_search_trials: int = 0,
        n_splits: int = 5,
    ) -> Self:
        """
        Fit the XGBoost model with or without hyperparam tuning.

        Args:
            X (pd.DataFrame): The features dataframe.
            y (Sequence[float]): The target series.
            n_search_trials (int): The number of search trials for the hyperparam
                tuning. If 0, the model will be fitted without hyperparam tuning.
            n_splits (int): The number of splits for the cross-validation.
        """
        if not n_search_trials:
            logger.info("Fitting XGBoost model without hyperparam tuning")
            self.model = XGBRegressor(
                objective=self.objective, eval_metric=self.eval_metric
            )
        else:
            logger.info("Fitting XGBoost model with hyperparam tuning")
            hyperparams = optimize_hyperparams(X, y, n_search_trials, n_splits)
            self.model = XGBRegressor(
                objective=self.objective,
                eval_metric=self.eval_metric,
                **hyperparams,
            )

        self.model.fit(X, y)
        return self

    def predict(self, X: pd.DataFrame) -> Sequence[float]:
        return self.model.predict(X)


def optimize_hyperparams(
    X: pd.DataFrame,
    y: pd.Series,
    n_search_trials: int = 10,
    n_splits: int = 10,
) -> dict[str, Any]:
    """
    Optimize the hyperparams for the XGBoost model using the Optuna library.
    """
    study = optuna.create_study(
        direction="minimize",
        # add pruner to stop unpromising trials early
        pruner=optuna.pruners.MedianPruner(
            n_startup_trials=5,
            n_warmup_steps=5,
            interval_steps=3,
        ),
    )

    def mae_objective(trial: optuna.Trial) -> float:
        """
        Objective function for Optuna using the mean absolute error as the metric
        to minimize.
        """

        # get the next set of hyperparams to try using the previous trial results
        # TODO: There is room to improve the search space.
        # Find the complete list of hyperparameters here:
        # https://xgboost.readthedocs.io/en/stable/parameter.html
        next_candidates = {
            # More focused ranges based on common best practices
            "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
            "max_depth": trial.suggest_int("max_depth", 3, 10),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 7),
            "max_delta_step": trial.suggest_int("max_delta_step", 0, 10),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "colsample_bylevel": trial.suggest_float("colsample_bylevel", 0.5, 1.0),
            "alpha": trial.suggest_float("alpha", 1e-8, 1.0, log=True),
            "lambda": trial.suggest_float("lambda", 1e-8, 1.0, log=True),
            "grow_policy": trial.suggest_categorical(
                "grow_policy", ["depthwise", "lossguide"]
            ),
            "booster": trial.suggest_categorical("booster", ["gbtree", "dart"]),
        }
        try:
            # split X into `n_splits` folds for cross-validation
            mae_scores: list[float] = []
            tscv = TimeSeriesSplit(n_splits=n_splits)
            for train_idx, test_idx in tscv.split(X):
                # Split the data using typed indices
                X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

                model = XGBRegressor(
                    **next_candidates,
                    early_stopping_rounds=10,
                    eval_metric="mae",
                ).fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

                y_pred: NDArray[np.float64] = model.predict(X_test)

                mae = cast(float, mean_absolute_error(y_test, y_pred))
                mae_scores.append(mae)

            return float(np.mean(mae_scores))

        except Exception as e:
            logger.error(f"Trial failed: {e}")
            raise optuna.exceptions.TrialPruned() from e

    study.optimize(func=mae_objective, n_trials=n_search_trials)
    logger.info(f"Best trial: {study.best_trial.number}, value: {study.best_value:.4f}")

    return study.best_params
