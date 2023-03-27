#!/bin/bash

QUERY_VIDEO_STREAMER=$1
FFMPEG_BIN=$2
QUERY_ID=$3
VIDEO_OUTPUT_TYPE=$4
VIDEO_SIZE=$5
FPS=$6
OUPUT_MEDIA_SERVER_URL=$7


python $QUERY_VIDEO_STREAMER $QUERY_ID $VIDEO_OUTPUT_TYPE | $FFMPEG_BIN -f rawvideo -r $FPS -pixel_format bgr24 -video_size $VIDEO_SIZE -i - -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 -map 0:v -map 1:a -vf format=yuv420p -c:v libx264 -profile:v main -preset ultrafast -tune zerolatency  -r $FPS -g $FPS -keyint_min $FPS -sc_threshold 0 -b:v 2000k -maxrate 2000k -bufsize 2000k -s $VIDEO_SIZE -c:a aac -f flv ${OUPUT_MEDIA_SERVER_URL}$QUERY_ID