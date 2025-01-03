import comet_ml
from loguru import logger
from price_predictions.core.settings import Settings, price_predictions_settings

from domain.core import now_timestamp


def train(s: Settings):
    """
    Train the Price Predictions model.

    This script will train the Price Predictions model using the feature view
    specified by the fview_name and fview_version.

    It has the following steps:
    1. Reads the feature data from the Feature Store.
    2. Splits the data into training and testing sets. #TODO: implement this step
    3. Trains the model using the training set. #TODO: implement this step
    4. Evaluates the model using the testing set. #TODO: implement this step
    5. Saves the model to the Model Registry. #TODO: implement this step

    For experiment tracking, it uses CometML.

    Args:
        fstore_project (str): The name of the Hopsworks project.
        fstore_api_key (str): The API key for the Hopsworks project.
        fview_name (str): The name of the feature view.
        fview_version (int): The version of the feature view.
    """
    _exp, _params = setup_experiment(s)

    # # reader, days_back = PricePredictionsReader(s), s.days_back
    # # train_data = reader.train_data(days_back)
    # logger.info(f"Train data ({days_back} days back): {train_data.info()}")


def setup_experiment(s: Settings):
    """
    Setups the experiment in the experiment tracker and logs base params.
    """
    now = now_timestamp()
    target_horizon_sec = s.timeframe.to_sec() * s.target_horizon
    exp_name = f"train_{s.symbol.value}_{s.timeframe.value}x{s.target_horizon}_{now}"
    params = {
        "fview_name": s.fview_name,
        "fview_version": s.fview_version,
        "deployment_env": s.deployment_env.value,
        "days_back": s.days_back,
        "symbol": s.symbol.value,
        "timeframe": s.timeframe.value,
        "target_horizon": s.target_horizon,
        "target_horizon_sec": target_horizon_sec,
        "correlated_symbol_features": [f.value for f in s.correlated_symbol_features],
        "ta_features": [f.value for f in s.ta_features],
        "hyperparam_tuning_search_trials": s.hyperparam_tuning_search_trials,
        "hyperparam_tuning_n_splits": s.hyperparam_tuning_n_splits,
    }

    logger.info(
        f"Training Price Predictions model: {exp_name} "
        f"target_horizon={s.target_horizon} ({target_horizon_sec} sec)"
    )

    exp = comet_ml.start(
        api_key=s.comet_ml_api_key,
        workspace=s.comet_ml_workspace,
        project_name=s.comet_ml_project,
    )
    exp.set_name(exp_name)
    exp.log_parameters(params)

    return exp, params


if __name__ == "__main__":
    settings = price_predictions_settings()
    train(settings)
