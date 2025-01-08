from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
from loguru import logger
from quixstreams.sinks.base import BatchingSink, SinkBackpressureError, SinkBatch

from price_predictions.core.settings import Settings
from price_predictions.predictor import PricePrediction


class ElasticSearchSink(BatchingSink):
    """
    Elasticsearch Sink.
    This sink writes the predictions to the Elasticsearch.
    """

    def __init__(self, settings: Settings):
        super().__init__()  # call super to make sure the batches are initialized
        self.client = Elasticsearch(settings.elasticsearch_url)
        self.index_name = settings.elasticsearch_index
        self.chunk_size = 1000
        self.max_retries = 3

    def write(self, batch: SinkBatch):
        """
        Write the batch to the Hopsworks Feature Store.
        Implementation of the abstract method from the BatchingSink class.
        """
        try:
            predictions = [PricePrediction.parse(i.value) for i in batch if i.value]
            for p in predictions:
                logger.info(f"Indexing prediction: {p.unpack()}")

            result_stream = streaming_bulk(
                client=self.client,
                chunk_size=self.chunk_size,
                max_retries=self.max_retries,
                actions=(
                    {
                        "_index": self.index_name,
                        "_id": p.key,
                        "_source": p.unpack(),
                    }
                    for p in predictions
                ),
            )

            for is_success, doc in result_stream:
                if not is_success:
                    logger.error(f"Failed to index document: {doc}")

        except TimeoutError as err:
            # In case of timeout, wait for 30s and retry
            raise SinkBackpressureError(
                retry_after=30.0,
                topic=batch.topic,
                partition=batch.partition,
            ) from err
