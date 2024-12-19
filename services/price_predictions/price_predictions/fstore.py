from typing import cast

import hopsworks
from hsfs.feature_group import FeatureGroup
from hsfs.feature_store import FeatureStore
from hsfs.feature_view import FeatureView
from loguru import logger

from price_predictions.core.settings import Settings


class PricePredictionsReader:
    """
    Class to extract the Price Predictions features from a feature view from Hopsworks.

    It uses the `ta` and `news_signals` feature groups to build a joint feature view,
    matching the `symbol` and `timestamp` columns.
    """

    def __init__(self, settings: Settings):
        self.fview_name = settings.fview_name
        self.fview_version = settings.fview_version

        logger.info(f"Connecting to Hopsworks: {settings.hopsworks_project_name}")
        self.project = hopsworks.login(
            project=settings.hopsworks_project_name,
            api_key_value=settings.hopsworks_api_key,
        )
        self.fstore: FeatureStore = self.project.get_feature_store()

        # get feature groups
        self.ta = cast(
            FeatureGroup,
            self.fstore.get_feature_group(
                name=settings.ta_fgroup_name,
                version=settings.ta_fgroup_version,
            ),
        )
        self.news_signals = cast(
            FeatureGroup,
            self.fstore.get_feature_group(
                name=settings.news_signals_fgroup_name,
                version=settings.news_signals_fgroup_version,
            ),
        )

        # init feature view
        self.fview = self._init_fview()
        logger.info(f"Price Predictions fview initialized: {self.fview.name}")

    def _init_fview(self) -> FeatureView:
        return self.fstore.get_or_create_feature_view(
            name=self.fview_name,
            version=self.fview_version,
            query=self.news_signals.select_all(),  # TODO: join with ta
            logging_enabled=True,
        )
