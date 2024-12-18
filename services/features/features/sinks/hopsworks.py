from datetime import datetime, timezone
from typing import Any, cast

import hopsworks
import pandas as pd
from hsfs.feature_store import FeatureStore
from loguru import logger
from quixstreams.sinks.base import BatchingSink, SinkBackpressureError, SinkBatch

from features.core.settings import features_settings


class HopsworksFeatureStoreSink(BatchingSink):
    """
    Hopsworks Feature Store Sink.

    This sink writes the features to the Hopsworks Feature Store
    from the quixstream
    """

    def __init__(self):
        settings = features_settings()
        self.fg_name = settings.fg_name
        self.fg_version = settings.fg_version
        self.fg_pk = settings.fg_pk
        self.fg_event_time = settings.fg_event_time
        self.fg_materialization_job_schedule = settings.fg_materialization_job_schedule
        self.project_name = settings.hopsworks_project_name
        self.api_key = settings.hopsworks_api_key
        self.fs: FeatureStore | None = None

        # call super to make sure the batches are initialized
        super().__init__()

    def connect(self):
        """
        Establish a connection to the Hopsworks Feature Store.
        """
        project = hopsworks.login(project=self.project_name, api_key_value=self.api_key)
        self.fs = project.get_feature_store()
        assert self.fs

        # Get or create the feature group
        self.fg = self.fs.get_or_create_feature_group(
            name=self.fg_name,
            version=self.fg_version,
            primary_key=self.fg_pk,
            event_time=self.fg_event_time,
            online_enabled=True,
        )
        try:
            # set the materialization job interval
            if job := cast(Any, self.fg.materialization_job):
                job.schedule(
                    cron_expression=self.fg_materialization_job_schedule,
                    start_time=datetime.now(tz=timezone.utc),
                )
        except Exception as e:
            logger.error(f"Error scheduling matjob: {e}")

        return self

    def write(self, batch: SinkBatch):
        """
        Write the batch to the Hopsworks Feature Store.
        Implementation of the abstract method from the BatchingSink class.
        """
        try:
            data = pd.DataFrame([item.value for item in batch])
            self.fg.insert(data)

        except TimeoutError as err:
            # In case of timeout, wait for 30s and retry
            raise SinkBackpressureError(
                retry_after=30.0,
                topic=batch.topic,
                partition=batch.partition,
            ) from err
