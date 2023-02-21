#!/bin/bash

QUERY_VIDEO_STREAMER=$1
FFMPEG_BIN=$2
QUERY_ID=$3
VIDEO_SIZE=$4
FPS=$5
OUPUT_MEDIA_SERVER_URL=$6


# echo "python $QUERY_VIDEO_STREAMER $QUERY_ID | $FFMPEG_BIN -f rawvideo -r $FPS -pixel_format bgr24 -video_size $VIDEO_SIZE -i - -vf format=yuv420p -c:v libx264 -g 1 -x264opts \"keyint=1:min-keyint=1:no-scenecut\" -an -f flv ${OUPUT_MEDIA_SERVER_URL}$QUERY_ID"
# python videostreamforwarder/video_streaming/query_video_streamer.py d16591a615e99c5c76ac7e8a38be1f32 | ffmpeg_bin/ffmpeg-linux64-v3.3.1  -f rawvideo -r 10 -pixel_format bgr24 -video_size 1280x720 -i - -vf format=yuv420p -c:v libx264 -g 1 -x264opts "keyint=1:min-keyint=1:no-scenecut" -an -f flv rtmp://localhost/hls/d16591a615e99c5c76ac7e8a38be1f32
python $QUERY_VIDEO_STREAMER $QUERY_ID | $FFMPEG_BIN -f rawvideo -r $FPS -pixel_format bgr24 -video_size $VIDEO_SIZE -i - -vf format=yuv420p -c:v libx264 -g 1 -x264opts "keyint=1:min-keyint=1:no-scenecut" -an -f flv ${OUPUT_MEDIA_SERVER_URL}$QUERY_ID