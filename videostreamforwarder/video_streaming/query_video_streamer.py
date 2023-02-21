#!/usr/bin/env python
import sys
import json

import logging
from unittest.mock import MagicMock
import logzero
import cv2

from event_service_utils.streams.redis import RedisStreamFactory

from event_service_utils.img_serialization.redis import RedisImageCache
from event_service_utils.services.tracer import EVENT_ID_TAG, tags, Format
from event_service_utils.tracing.jaeger import init_tracer

from videostreamforwarder.conf import (
    REDIS_ADDRESS,
    REDIS_PORT,
    LOGGING_LEVEL,
    TRACER_REPORTING_HOST,
    TRACER_REPORTING_PORT,
)

class QueryVideoStreammer():
    def __init__(self, query_id, file_storage_cli, stream_factory, tracer, logging_level, out_type='sysout'):
        self.name = 'VideoStreamForwarder:Streamer'
        self.logging_level = logging_level
        self.query_id = query_id
        self.fs_client = file_storage_cli
        self.stream_factory = stream_factory
        self.tracer = tracer
        self.out_type = out_type
        self.logger = self._setup_logging()
        self.query_stream = self.create_query_stream(query_id)

    def _setup_logging(self):
        log_format = (
            '%(color)s[%(levelname)1.1s %(name)s %(asctime)s:%(msecs)d '
            '%(module)s:%(funcName)s:%(lineno)d]%(end_color)s %(message)s'
        )
        formatter = logzero.LogFormatter(fmt=log_format)
        return logzero.setup_logger(name=self.name, level=logging.getLevelName(self.logging_level), formatter=formatter)

    def create_query_stream(self, query_id):
        return self.stream_factory.create(query_id, stype='streamOnly')

    def default_event_deserializer(self, json_msg):
        event_key = b'event' if b'event' in json_msg else 'event'
        event_json = json_msg.get(event_key, '{}')
        event_data = json.loads(event_json)
        return event_data

    def get_event_tracer_kwargs(self, event_data):
        tracer_kwargs = {}
        tracer_data = event_data.get('tracer', {})
        tracer_headers = tracer_data.get('headers', {})
        if tracer_headers:
            span_ctx = self.tracer.extract(Format.HTTP_HEADERS, tracer_headers)
            tracer_kwargs.update({
                'child_of': span_ctx
            })
        else:
            self.logger.info(f'No tracer id found on event id: {event_data["id"]}')
            self.logger.info(
                (
                    'Will start a new tracer id.'
                    'If this event came from another service '
                    'this will likelly cause confusion in the current event tracing')
            )
        return tracer_kwargs

    def event_trace_for_method_with_event_data(
            self, method, method_args, method_kwargs, get_event_tracer=False, tracer_tags=None):
        span_name = method.__name__
        if tracer_tags is None:
            tracer_tags = {}

        tracer_kwargs = {}
        if get_event_tracer:
            event_data = method_kwargs['event_data']
            tracer_kwargs = self.get_event_tracer_kwargs(event_data)
        with self.tracer.start_active_span(span_name, **tracer_kwargs) as scope:
            for tag, value in tracer_tags.items():
                scope.span.set_tag(tag, value)
            method(*method_args, **method_kwargs)

    def process_data_event(self, event_data):
        for vekg_event in event_data['vekg_stream']:
            image_ndarray = self.get_event_data_image_ndarray(vekg_event)
            if self.out_type == 'sysout':
                framestring = image_ndarray.tostring()
                sys.stdout.buffer.write(framestring)
            else:
                cv2.imshow('frame', image_ndarray)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    pass

    def get_event_data_image_ndarray(self, event_data):
        img_key = event_data['image_url']
        width = event_data['width']
        height = event_data['height']
        color_channels = event_data['color_channels']
        n_channels = len(color_channels)
        nd_shape = (int(height), int(width), n_channels)
        image_nd_array = self.fs_client.get_image_ndarray_by_key_and_shape(img_key, nd_shape)
        return image_nd_array

    def run(self):
        while True:
            event_list = self.query_stream.read_events(count=1)
            for event_tuple in event_list:
                msg_id, json_msg = event_tuple
                try:
                    event_data = self.default_event_deserializer(json_msg)
                    self.event_trace_for_method_with_event_data(
                        method=self.process_data_event,
                        method_args=(),
                        method_kwargs={
                            'event_data': event_data
                        },
                        get_event_tracer=True,
                        tracer_tags={
                            tags.SPAN_KIND: tags.SPAN_KIND_CONSUMER,
                            EVENT_ID_TAG: event_data['id'],
                        }
                    )
                except Exception as e:
                    self.logger.error(f'Error processing {json_msg}:')
                    self.logger.exception(e)



if __name__ == '__main__':
    query_id = sys.argv[1]

    stream_factory = RedisStreamFactory(host=REDIS_ADDRESS, port=REDIS_PORT)
    tracer_configs = {
        'reporting_host': TRACER_REPORTING_HOST,
        'reporting_port': TRACER_REPORTING_PORT,
    }
    sub_service_name = 'VideoStreamForwarder'
    tracer = init_tracer(sub_service_name, **tracer_configs)

    redis_fs_cli_config = {
        'host': REDIS_ADDRESS,
        'port': REDIS_PORT,
        'db': 0,
    }

    file_storage_cli = RedisImageCache()
    file_storage_cli.file_storage_cli_config = redis_fs_cli_config
    file_storage_cli.initialize_file_storage_client()

    video_streamer = QueryVideoStreammer(
        query_id=query_id,
        file_storage_cli=file_storage_cli,
        stream_factory=stream_factory,
        tracer=tracer,
        logging_level=LOGGING_LEVEL,
        out_type='sysout'
    )
    video_streamer.run()