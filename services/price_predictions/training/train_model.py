from typing import Any, Sequence, cast

import comet_ml
import pandas as pd
from comet_ml import CometExperiment
from loguru import logger
from price_predictions.core.settings import Settings, price_predictions_settings
from price_predictions.fstore import PricePredictionsReader
from price_predictions.model.base import CryptoPricePredictionDummyModel
from sklearn.metrics import mean_absolute_error as mae

from domain.core import now_timestamp

TrainTestSplit = tuple[pd.DataFrame, Sequence[float], pd.DataFrame, Sequence[float]]


def train(s: Settings):
    """
    Train the Price Predictions model.

    This script will train the Price Predictions model using the feature view
    specified by the fview_name and fview_version.

    It has the following steps:
    1. Setup experiment
    2. Train test split with features/target from the feature store
    3. Evaluate baseline model
    4. Evaluate the XGBoost model.
    5. Save the model to the Model Registry.

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
    evaluate_baseline((X_train, y_train, X_test, y_test), exp=exp)

    # 4. Evaluate the XGBoost model.
    # TODO: implement this step

    # 5. Save the model to the Model Registry.
    # TODO: implement this step


def setup_experiment(s: Settings, fview_name: str):
    """
    Setups the experiment in the experiment tracker and logs base params.
    """
    now = now_timestamp()
    target_horizon_sec = s.timeframe.to_sec() * s.target_horizon
    exp_name = f"train_{s.symbol.value}_{s.timeframe.value}x{s.target_horizon}_{now}"
    params = {
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
    train_data = reader.get_features(
        days_back=s.days_back,
        target_horizon=s.target_horizon,
    )
    logger.info(f"Train data ({s.days_back} days back): {train_data.info()}")

    test_size = 0.2
    train_size = int(len(train_data) * (1 - test_size))
    train_df = train_data.iloc[:train_size]
    test_df = train_data.iloc[train_size:]

    X_train = train_df.drop(columns=["target"])
    y_train = train_df["target"]  # type: ignore

    X_test = test_df.drop(columns=["target"])
    y_test = test_df["target"]  # type: ignore

    shapes: dict[str, Any] = {
        "X_train": X_train.shape,
        "y_train": y_train.shape,
        "X_test": X_test.shape,
        "y_test": y_test.shape,
    }
    exp.log_parameters(shapes)

    return (
        X_train,
        cast(Sequence[float], y_train),
        X_test,
        cast(Sequence[float], y_test),
    )


def evaluate_baseline(train_test_split: TrainTestSplit, exp: CometExperiment):
    """
    Evaluate the baseline model using mean absolute error.
    """
    model = CryptoPricePredictionDummyModel()

    X_train, y_train, X_test, y_test = train_test_split
    y_test_pred, y_train_pred = model.predict(X_test), model.predict(X_train)
    results: dict[str, Any] = {
        "mae_dummy_test": mae(y_test, y_test_pred),
        "mae_dummy_train": mae(y_train, y_train_pred),
    }
    exp.log_metrics(results)


if __name__ == "__main__":
    settings = price_predictions_settings()
    train(settings)
