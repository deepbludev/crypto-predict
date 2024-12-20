from loguru import logger
from price_predictions.core.settings import Settings, price_predictions_settings
from price_predictions.fstore import PricePredictionsReader


def train(settings: Settings):
    """
    Train the Price Predictions model.

    This script will train the Price Predictions model using the feature view
    specified by the fview_name and fview_version.

    It has the following steps:
    1. Reads the feature data from the Feature Store.
    2. Splits the data into training and testing sets.
    3. Trains the model using the training set.
    4. Evaluates the model using the testing set.
    5. Saves the model to the Model Registry.

    For experiment tracking, it uses CometML.

    Args:
        fstore_project (str): The name of the Hopsworks project.
        fstore_api_key (str): The API key for the Hopsworks project.
        fview_name (str): The name of the feature view.
        fview_version (int): The version of the feature view.
    """
    logger.info("Training Price Predictions model")

    _reader = PricePredictionsReader(settings)


if __name__ == "__main__":
    settings = price_predictions_settings()
    train(settings)
