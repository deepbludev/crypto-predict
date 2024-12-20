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
    matching the `asset` and `llm_name` columns.
    """

    def __init__(self, settings: Settings):
        self.asset = settings.asset
        self.timeframe = settings.timeframe
        self.llm_name = settings.llm_name

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
        logger.info(
            f"Price Predictions Feature View initialized: {self.fview.name} "
            f"(version: {self.fview.version})"
        )

    def _init_fview(self) -> FeatureView:
        ta_for_asset_and_timeframe = (
            self.ta.select_all()
            .filter(self.ta.timeframe == self.timeframe)
            .filter(self.ta.asset == self.asset)
        )

        news_signals_for_asset_and_llm_name = (
            self.news_signals.select_all()
            .filter(self.news_signals.asset == self.asset)
            .filter(self.news_signals.llm_name == self.llm_name)
        )

        # Join on both asset
        join_query = ta_for_asset_and_timeframe.join(
            news_signals_for_asset_and_llm_name,
            on=["asset"],
            prefix="news_signal_",
        )

        return self.fstore.get_or_create_feature_view(
            name=self.fview_name,
            version=self.fview_version,
            query=join_query,
            labels=[],
            description="""
            Feature view combining TA and news signals by asset
            with point-in-time correctness
            """,
        )
