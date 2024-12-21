from datetime import datetime, timedelta
from typing import cast

import hopsworks
import pandas as pd
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
        self.timeframe = settings.timeframe
        self.llm_name = settings.llm_name
        self.asset = settings.asset
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
        return self.fstore.get_or_create_feature_view(
            name=self.fview_name,
            version=self.fview_version,
            labels=[],
            logging_enabled=True,
            description="""
            Feature view combining TA and news signals by asset
            with point-in-time correctness
            """,
            # Join views on asset using point-in-time correctness
            query=self.ta.select_all().join(
                self.news_signals.select_all(),
                on=["asset"],
                prefix="news_signal_",
            ),
        )

    def train_data(self, days_back: int = 30) -> pd.DataFrame:
        """
        Get the training data from the feature view for the given asset, timeframe
        and llm_name, dating `days_back` days back.
        """

        df = cast(
            pd.DataFrame,
            self.fview.get_batch_data(
                start_time=(now := datetime.now()) - timedelta(days=days_back),
                end_time=now,
            ),
        )

        return df[
            (df.asset == self.asset.value)
            & (df.timeframe == self.timeframe.value)
            & (df.news_signal_llm_name == self.llm_name.value)
        ]
