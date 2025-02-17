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

from domain.ta import TechnicalIndicator
from price_predictions.core.settings import Settings


class PricePredictionsStore:
    """
    Class to extract the Price Predictions features from a feature view from Hopsworks.

    It uses the `ta` and `news_signals` feature groups to build a joint feature view,
    matching the `asset` and `llm_name` columns.
    """

    def __init__(
        self,
        settings: Settings,
        fview_base_name: str | None = None,
        fview_version: int | None = None,
        ta_features: list[TechnicalIndicator] | None = None,
    ):
        """
        Initialize the PricePredictionsReader.

        Args:
            settings (Settings): The settings object.
            fview_base_name (str | None, optional): The base name of the feature view.
                Defaults to None.
            fview_version (int | None, optional): The version of the feature view.
                Defaults to None.
            ta_features (list[TechnicalIndicator] | None, optional): The technical
                indicators to override the default ones from the settings.
        """
        self.symbol = settings.symbol
        self.timeframe = settings.timeframe
        self.fview_base_name = fview_base_name or settings.fview_name.split("__")[0]
        self.fview_version = fview_version or settings.fview_version
        self.ta_features = [
            TechnicalIndicator(f) for f in ta_features or settings.ta_features
        ]

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
            f"Reading Feature View: {self.fview_name} "
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
                name=self.fview_name,
                version=self.fview_version,
            )

        except hsfs_exceptions.RestAPIError:
            logger.info(f"Creating feature view {self.fview_name}...")

            return self.fstore.create_feature_view(
                name=self.fview_name,
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
    def fview_name(self) -> str:
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

        If a target is required (training case), it is added to the dataframe, by
        joining the features with the close time in the target horizon.

        Otherwise, only the features are returned (inference case).


        Args:
            days_back (int): The number of days back to get the features from.
            target_horizon (int): The number of periods ahead to shift the close price.

        Returns:
            pd.DataFrame: The features dataframe.

        TODO:
            - add correlated symbols features in the future
        """

        # get the features from the feature view
        features = cast(
            pd.DataFrame,
            self.fview.get_batch_data(
                start_time=(now := datetime.now()) - timedelta(days=days_back),
                end_time=now,
            ),
        )

        features = (
            # only select the features we need
            features[self.features]
            .rename(columns={"end": "close_time"})
            .dropna()
            # drop duplicates to remove incomplete candles from real-time data
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

    def get_inference_features(self) -> pd.DataFrame:
        """
        Get the inference features from the feature view.
        """
        vectors = self.fview.get_feature_vectors(
            return_type="pandas",
            entry=[
                {
                    "symbol": self.symbol.value,
                    "timeframe": self.timeframe.value,
                    "story_asset": self.symbol.to_asset().value,
                }
            ],
        )
        return pd.DataFrame(vectors)[self.features].rename(
            columns={"end": "close_time"}
        )
