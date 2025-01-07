from typing import Any, Self, Sequence

import numpy as np
import optuna
import pandas as pd
from loguru import logger
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBRegressor

from domain.candles import CandleTimeframe
from domain.trades import Symbol

from .base import CryptoPricePredictionModel, ModelStatus


class XGBoostModel(CryptoPricePredictionModel):
    """
    XGBoost model for crypto price predictions with hyperparam tuning.

    TODO: support multiple models with different lookback periods in order to
    improve the model's training results.
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
        self.target_horizon = target_horizon
        self.objective = objective
        self.eval_metric = eval_metric
        self.init_model()
        super().__init__(
            symbol=symbol,
            timeframe=timeframe,
            target_horizon=target_horizon,
            status=status,
        )

    def init_model(self, hyperparams: dict[str, Any] | None = None) -> Self:
        self.model = self.create_xgb(**(hyperparams or {}))
        return self

    def create_xgb(self, **kwargs: Any) -> XGBRegressor:
        return XGBRegressor(
            objective=self.objective,
            eval_metric=self.eval_metric,
            **kwargs,
        )

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

        self.init_model(
            hyperparams=self.optimize_hyperparams(X, y, n_search_trials, n_splits)
            if n_search_trials
            else None
        )
        self.model.fit(X, y)
        return self

    def predict(self, X: pd.DataFrame) -> Sequence[float]:
        return self.model.predict(X)

    def optimize_hyperparams(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_search_trials: int = 100,
        n_splits: int = 3,
    ) -> dict[str, Any]:
        """
        Optimize the hyperparams for the XGBoost model using the Optuna library.
        """
        study = optuna.create_study(
            direction="minimize",
            # add pruner to stop unpromising trials early
            pruner=optuna.pruners.MedianPruner(
                n_startup_trials=10,
                n_warmup_steps=10,
                interval_steps=5,
            ),
        )

        def mae_objective(trial: optuna.Trial) -> float:
            """
            Objective function for Optuna using the mean absolute error as the metric
            to minimize.
            """

            try:
                # split X into `n_splits` folds for cross-validation
                min_gap = self.target_horizon
                tscv = TimeSeriesSplit(
                    n_splits=n_splits,
                    gap=min_gap,
                    test_size=int(len(X) * 0.2),
                )

                mae_scores: list[float] = []
                for train_idx, test_idx in tscv.split(X):
                    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

                    # get the next candidates using the previous trial results
                    next_candidates = {
                        # core parameters
                        "n_estimators": trial.suggest_int("n_estimators", 200, 2000),
                        "max_depth": trial.suggest_int("max_depth", 3, 12),
                        "learning_rate": trial.suggest_float(
                            "learning_rate", 1e-4, 0.3, log=True
                        ),
                        # sampling parameters
                        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                        "colsample_bytree": trial.suggest_float(
                            "colsample_bytree", 0.6, 1.0
                        ),
                        # regularization parameters
                        "min_child_weight": trial.suggest_int(
                            "min_child_weight", 1, 10
                        ),
                        "gamma": trial.suggest_float("gamma", 1e-8, 1.0, log=True),
                        "alpha": trial.suggest_float("alpha", 1e-8, 1.0, log=True),
                        "lambda": trial.suggest_float("lambda", 1e-8, 1.0, log=True),
                        # performance optimization
                        "tree_method": "hist",  # much faster than default
                        "early_stopping_rounds": 50,
                    }

                    model = self.create_xgb(**next_candidates)
                    model.fit(
                        X_train,
                        y_train,
                        eval_set=[(X_test, y_test)],
                        verbose=False,
                    )
                    y_pred = model.predict(X_test)
                    fold_mae = float(mean_absolute_error(y_test, y_pred))
                    mae_scores.append(fold_mae)

                    # report intermediate objective value for pruning
                    trial.report(fold_mae, len(mae_scores) - 1)
                    if trial.should_prune():
                        raise optuna.exceptions.TrialPruned()

                return float(np.mean(mae_scores))

            except Exception as e:
                logger.error(f"Trial failed: {e}")
                raise optuna.exceptions.TrialPruned() from e

        study.optimize(func=mae_objective, n_trials=n_search_trials)
        logger.info(
            f"Best trial: {study.best_trial.number} "
            f"Best value: {study.best_value:.4f} "
            f"Best params: {study.best_params}"
        )

        return study.best_params
