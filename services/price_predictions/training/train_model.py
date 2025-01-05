from typing import Any

import comet_ml
import joblib
import numpy as np
import pandas as pd
from comet_ml import CometExperiment
from loguru import logger
from price_predictions.core.settings import Settings, price_predictions_settings
from price_predictions.fstore import PricePredictionsReader
from price_predictions.model.base import (
    CryptoPricePredictionModel,
    DummyModel,
    ModelStatus,
)
from price_predictions.model.xgboost import XGBoostModel
from sklearn.metrics import mean_absolute_error as mae
from sklearn.metrics import mean_squared_error as mse
from sklearn.metrics import r2_score

from domain.core import now_timestamp

TrainTestSplit = tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]


def train(s: Settings):
    """
    Train the Price Predictions model.

    This script will train the Price Predictions model using the feature view
    specified by the fview_name and fview_version.

    It has the following steps:
    1. Setup experiment
    2. Train test split with features/target from the feature store
    3. Evaluate baseline model
    4. Train the XGBoost model.
    5. Evaluate the XGBoost model.
    6. Log & register the model

    For experiment tracking and model registry, it uses CometML.

    Args:
        fstore_project (str): The name of the Hopsworks project.
        fstore_api_key (str): The API key for the Hopsworks project.
        fview_name (str): The name of the feature view.
        fview_version (int): The version of the feature view.
    """
    # 1. Setup experiment
    reader = PricePredictionsReader(s)
    exp, _ = setup_experiment(s, fview_name=reader.labeled_fview_name)

    # 2. Train test split with features/target from the feature store
    X_train, y_train, X_test, y_test = train_test_split(s, reader, exp)

    # 3. Evaluate baseline model
    evaluate_baseline(
        (X_train, y_train, X_test, y_test),
        model=DummyModel(),
        exp=exp,
    )

    # 4. Train the XGBoost model.
    model = XGBoostModel(
        symbol=s.symbol,
        timeframe=s.timeframe,
        target_horizon=s.target_horizon,
        status=ModelStatus.from_deployment_env(s.deployment_env),
    ).fit(
        X_train,
        y_train,
        n_search_trials=s.hyperparam_tuning_search_trials,
        n_splits=s.hyperparam_tuning_n_splits,
    )

    # 5. Evaluate the XGBoost model.
    evaluate_model(
        (X_train, y_train, X_test, y_test),
        model=model,
        exp=exp,
    )

    # 6. Log & register the model
    log_model(
        model=model,
        exp=exp,
        # TODO: modify to only register based on some condition, such as MAE < something
        should_register=True,
    )


def setup_experiment(s: Settings, fview_name: str):
    """
    Setups the experiment in the experiment tracker and logs base params.
    """
    now = now_timestamp()
    target_horizon_sec = s.timeframe.to_sec() * s.target_horizon
    exp_name = f"train_{s.symbol.value}_{s.timeframe.value}x{s.target_horizon}_{now}"
    params: dict[str, Any] = {
        "fview_name": fview_name,
        "fview_version": s.fview_version,
        "deployment_env": s.deployment_env.value,
        "days_back": s.days_back,
        "symbol": s.symbol.value,
        "timeframe": s.timeframe.value,
        "target_horizon": s.target_horizon,
        "target_horizon_sec": target_horizon_sec,
        "ta_features": [f.value for f in s.ta_features],
        "hyperparam_tuning_search_trials": s.hyperparam_tuning_search_trials,
        "hyperparam_tuning_n_splits": s.hyperparam_tuning_n_splits,
    }
    exp = comet_ml.start(
        api_key=s.comet_ml_api_key,
        workspace=s.comet_ml_workspace,
        project_name=s.comet_ml_project,
    )
    exp.set_name(exp_name)
    exp.log_parameters(params)

    logger.info(
        f"Training Price Predictions model: {exp_name} "
        f"target_horizon={s.target_horizon} ({target_horizon_sec} sec)"
    )

    return exp, params


def train_test_split(
    s: Settings,
    reader: PricePredictionsReader,
    exp: CometExperiment,
) -> TrainTestSplit:
    """
    Reads the features from the feature store and splits into train and test.
    """
    logger.info(f"Train data ({s.days_back} days back)")
    features = reader.get_features(
        days_back=s.days_back,
        target_horizon=s.target_horizon,
    )
    features.info()

    test_size = 0.2
    train_size = int(len(features) * (1 - test_size))
    train_df = features.iloc[:train_size]
    test_df = features.iloc[train_size:]

    X_train, y_train = train_df.drop(columns=["target"]), train_df["target"]
    X_test, y_test = test_df.drop(columns=["target"]), test_df["target"]

    shapes: dict[str, Any] = {
        "X_train": X_train.shape,
        "y_train": y_train.shape,
        "X_test": X_test.shape,
        "y_test": y_test.shape,
    }
    exp.log_parameters(shapes)

    return X_train, y_train, X_test, y_test


def evaluate_baseline(
    train_test_split: TrainTestSplit,
    model: CryptoPricePredictionModel,
    exp: CometExperiment,
):
    """
    Evaluate the baseline model using mean absolute error.
    TODO: use latest registered model from CometML as baseline
    """
    X_train, y_train, X_test, y_test = train_test_split
    exp.log_metrics(
        {
            "mae_dummy": mae(y_test, model.predict(X_test)),
            "mae_dummy_train": mae(y_train, model.predict(X_train)),
        }
    )


def evaluate_model(
    train_test_split: TrainTestSplit,
    model: CryptoPricePredictionModel,
    exp: CometExperiment,
):
    """
    Evaluate the model using mean absolute error, both on the test and training data.
    The training data is used to see if the model is overfitting.
    """
    X_train, y_train, X_test, y_test = train_test_split

    # Get predictions
    y_pred_test, y_pred_train = model.predict(X_test), model.predict(X_train)

    # Calculate various metrics
    metrics = {
        "mae": mae(y_test, y_pred_test),
        "mae_train": mae(y_train, y_pred_train),
        "mape": np.mean(np.abs((y_test - y_pred_test) / y_test)) * 100,
        "rmse": np.sqrt(mse(y_test, y_pred_test)),
        "r2": r2_score(y_test, y_pred_test),
    }

    exp.log_metrics(metrics)

    # Log feature importance
    xgb_model = model.unpack_model()
    if hasattr(xgb_model, "feature_importances_"):
        feature_imp = pd.DataFrame(
            {
                "feature": X_test.columns,
                "importance": xgb_model.feature_importances_,
            }
        ).sort_values("importance", ascending=False)
        exp.log_table("feature_importance.csv", feature_imp)


def log_model(
    model: CryptoPricePredictionModel,
    exp: CometExperiment,
    should_register: bool = True,
):
    """
    Dumps the model with joblib and logs it in the experiment tracker.
    """
    model_filepath = f"{model.name}.joblib"
    joblib.dump(model.unpack_model(), model_filepath)
    exp.log_model(name=model.name, file_or_folder=model_filepath)
    if should_register:
        exp.register_model(
            model_name=model.name,
            status=model.status.value,
        )


if __name__ == "__main__":
    settings = price_predictions_settings()
    train(settings)
