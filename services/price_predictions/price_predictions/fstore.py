from datetime import datetime, timedelta
from typing import cast

import hopsworks
import pandas as pd
from hsfs.client import exceptions as hsfs_exceptions
from hsfs.feature import Feature
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
        self.symbol = settings.symbol
        self.timeframe = settings.timeframe
        self.fview_base_name = settings.fview_name
        self.fview_version = settings.fview_version
        self.ta_features = settings.ta_features
        logger.info(f"Connecting to Hopsworks: {settings.hopsworks_project_name}")
        self.project = hopsworks.login(
            project=settings.hopsworks_project_name,
            api_key_value=settings.hopsworks_api_key,
        )
        self.fstore: FeatureStore = self.project.get_feature_store()
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
        self.fview = self.init_fview()
        logger.info(
            f"Reading Feature View: {self.labeled_fview_name} "
            f"(version: {self.fview.version})"
        )

    @property
    def features(self) -> list[str]:
        return ["end", "open", "close", "story_signal"] + [
            indicator.value for indicator in self.ta_features
        ]

    def init_fview(self) -> FeatureView:
        """
        Initialize the feature view, using the labeled feature view name in order to
        programmaticaly get or create the feature view based on the symbol and
        timeframe.
        """
        try:
            return self.fstore.get_feature_view(
                name=self.labeled_fview_name,
                version=self.fview_version,
            )

        except hsfs_exceptions.RestAPIError:
            logger.info(f"Creating feature view {self.labeled_fview_name}...")

            return self.fstore.create_feature_view(
                name=self.labeled_fview_name,
                version=self.fview_version,
                description=f"""
                    Feature view combining TA and news signals by
                    asset with point-in-time correctness for symbol {self.symbol.value}
                    and timeframe {self.timeframe.value}.
                    """,
                query=(
                    self.ta.select_all()
                    .filter(Feature("asset") == self.symbol.to_asset().value)
                    .filter(Feature("timeframe") == self.timeframe.value)
                    .join(
                        self.news_signals.select_all(),
                        on=["asset"],
                        prefix="story_",
                    )
                ),
            )

    @property
    def labeled_fview_name(self) -> str:
        """
        Get the name of the feature view with the symbol and timeframe.
        Example: "sentimented_ta__xrpusd_1h"
        """
        return (
            f"{self.fview_base_name}__"
            + f"{self.symbol.value}_"
            + f"{self.timeframe.value}"
        ).lower()

    def get_features(
        self,
        days_back: int = 30,
        target_horizon: int | None = None,
    ) -> pd.DataFrame:
        """
        Get the training data from the feature view for the given asset and timeframe
        dating `days_back` days back.

        If the target is required, it is added to the dataframe, by shifting the close
        price `target_horizon` periods ahead. This is used for training the model.
        In inference pipelines, the target is not required.

        TODO: add correlated symbols features in the future

        Args:
            days_back (int): The number of days back to get the features from.
            target_horizon (int): The number of periods ahead to shift the close price.

        Returns:
            pd.DataFrame: The features dataframe.
        """

        # get the features from the feature view
        features = cast(
            pd.DataFrame,
            self.fview.get_batch_data(
                start_time=(now := datetime.now()) - timedelta(days=days_back),
                end_time=now,
            ),
        )

        # rename the end column to close_time and drop the na values
        features = (
            features[self.features]
            .rename(columns={"end": "close_time"})
            .dropna()
            .drop_duplicates(subset=["close_time"], keep="last")
            .sort_values(by="close_time")
        )

        if not target_horizon:
            # return the features without the target
            return features

        # shift the close_time by the target_horizon
        time_delta = self.timeframe.to_sec() * target_horizon * 1000

        # get the target and shift the close_time by the target_horizon
        target = features[["close_time", "close"]].copy()
        target["close_time"] = target["close_time"] - time_delta

        # merge the features with the target
        return (
            features.merge(
                target,
                on="close_time",
                how="left",
                suffixes=("", "_target"),
            )
            .rename(columns={"close_target": "target"})
            .dropna()
        )
