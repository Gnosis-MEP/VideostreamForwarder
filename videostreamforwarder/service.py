import threading

from event_service_utils.logging.decorators import timer_logger
from event_service_utils.services.event_driven import BaseEventDrivenCMDService
from event_service_utils.tracing.jaeger import init_tracer

from videostreamforwarder.video_streaming.vs_process_manager import VSProcessManager
from videostreamforwarder.conf import (
    FFMPEG_BIN,
    VIDEO_STREAMER_PIPE_SCRIPT,
    VIDEO_STREAMER_SCRIPT,
    OUPUT_MEDIA_SERVER_URL,
    SUPPORTED_VIDEO_OUTPUT_TYPES,
    LISTEN_EVENT_TYPE_QUERY_CREATED,
    LISTEN_EVENT_TYPE_QUERY_REMOVED,
)


class VideoStreamForwarder(BaseEventDrivenCMDService):
    def __init__(self,
                 service_stream_key, service_cmd_key_list,
                 pub_event_list, service_details,
                 file_storage_cli,
                 stream_factory,
                 logging_level,
                 tracer_configs):
        tracer = init_tracer(self.__class__.__name__, **tracer_configs)
        super(VideoStreamForwarder, self).__init__(
            name=self.__class__.__name__,
            service_stream_key=service_stream_key,
            service_cmd_key_list=service_cmd_key_list,
            pub_event_list=pub_event_list,
            service_details=service_details,
            stream_factory=stream_factory,
            logging_level=logging_level,
            tracer=tracer,
        )
        self.cmd_validation_fields = ['id']
        self.data_validation_fields = ['id']
        self.fs_client = file_storage_cli
        self.query_id_to_video_stream_manager = {}
        self.publishers = {}

    def process_add_query(self, event_data):

        output_list = event_data['parsed_query']['output']
        video_outputs = [output for output in output_list if output in SUPPORTED_VIDEO_OUTPUT_TYPES]
        if len(video_outputs) != 0:
            video_output_type = video_outputs[0]
            query_id = event_data['query_id']
            buffer_stream = event_data['buffer_stream']

            fps = float(buffer_stream['fps'])
            width, height = buffer_stream['resolution'].lower().split('x')  #WxH

            query_vs_m = VSProcessManager(
                self,
                VIDEO_STREAMER_PIPE_SCRIPT,
                VIDEO_STREAMER_SCRIPT,
                FFMPEG_BIN,
                OUPUT_MEDIA_SERVER_URL,
                query_id,
                fps,
                width,
                height,
                video_output_type
            )
            self.query_id_to_video_stream_manager[query_id] = query_vs_m
            query_vs_m.run()

    def process_del_query(self, event_data):
        query_id = event_data['query_id']
        if query_id in self.query_id_to_video_stream_manager.keys():
           query_vs_m = self.query_id_to_video_stream_manager.pop(query_id, None)
           if query_vs_m and query_vs_m.isOpened():
                query_vs_m.close()

    # def process_publisher_created(self, publisher_id, source, meta):
    #     if publisher_id not in self.publishers.keys():
    #         self.publishers[publisher_id] = {
    #             'id': publisher_id,
    #             'source': source,
    #             'meta': meta,
    #         }
    #     else:
    #         self.logger.info('Ignoring duplicated publisher incluson')

    # def process_publisher_removed(self, publisher_id):
    #     publisher = self.publishers.pop(publisher_id, None)
    #     if publisher is None:
    #         self.logger.info('Ignoring removal of non-existing publisher')

    @timer_logger
    def process_data_event(self, event_data, json_msg):
        if not super(VideoStreamForwarder, self).process_data_event(event_data, json_msg):
            return False

    def process_event_type(self, event_type, event_data, json_msg):
        if not super(VideoStreamForwarder, self).process_event_type(event_type, event_data, json_msg):
            return False

        if event_type == LISTEN_EVENT_TYPE_QUERY_CREATED:
            self.process_add_query(event_data)
        elif event_type == LISTEN_EVENT_TYPE_QUERY_REMOVED:
            query_id = event_data['query_id']
            self.process_del_query(query_id)

    def log_state(self):
        super(VideoStreamForwarder, self).log_state()
        self.logger.info(f'Service name: {self.name}')
        self._log_dict('Current query Video streaming:', self.query_id_to_video_stream_manager)

    def kill_all_query_video_streams(self):
        self.logger.info(f'Killing all query video streaming subprocesses')
        for query_id, query_vs_m in self.query_id_to_video_stream_manager.items():
            if query_vs_m.isOpened():
                query_vs_m.close()

    def run(self):
        super(VideoStreamForwarder, self).run()
        self.log_state()
        try:
            self.run_forever(self.process_cmd)
        except KeyboardInterrupt as e:
            self.logger.error(f'Received keyInterrup, will kill all queries video streams before exiting')
            self.logger.exception(e)
        finally:
            self.kill_all_query_video_streams()