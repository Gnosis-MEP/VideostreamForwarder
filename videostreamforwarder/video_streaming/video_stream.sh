#!/bin/bash

QUERY_VIDEO_STREAMER=$1
FFMPEG_BIN=$2
QUERY_ID=$3
VIDEO_OUTPUT_TYPE=$4
VIDEO_SIZE=$5
FPS=$6
OUPUT_MEDIA_SERVER_URL=$7


# echo "python $QUERY_VIDEO_STREAMER $QUERY_ID | $FFMPEG_BIN -f rawvideo -r $FPS -pixel_format bgr24 -video_size $VIDEO_SIZE -i - -vf format=yuv420p -c:v libx264 -g 1 -x264opts \"keyint=1:min-keyint=1:no-scenecut\" -an -f flv ${OUPUT_MEDIA_SERVER_URL}$QUERY_ID"
# python videostreamforwarder/video_streaming/query_video_streamer.py d16591a615e99c5c76ac7e8a38be1f32 | ffmpeg_bin/ffmpeg-linux64-v3.3.1  -f rawvideo -r 10 -pixel_format bgr24 -video_size 1280x720 -i - -vf format=yuv420p -c:v libx264 -g 1 -x264opts "keyint=1:min-keyint=1:no-scenecut" -an -f flv rtmp://localhost/hls/d16591a615e99c5c76ac7e8a38be1f32
# ok:
# python $QUERY_VIDEO_STREAMER $QUERY_ID $VIDEO_OUTPUT_TYPE | $FFMPEG_BIN -f rawvideo -r $FPS -pixel_format bgr24 -video_size $VIDEO_SIZE -i - -vf format=yuv420p -c:v libx264 -profile:v baseline -an -preset ultrafast -tune zerolatency -g 1 -x264opts "keyint=1:min-keyint=1:no-scenecut" -an -f flv ${OUPUT_MEDIA_SERVER_URL}$QUERY_ID
# python $QUERY_VIDEO_STREAMER $QUERY_ID $VIDEO_OUTPUT_TYPE


# new:
# python $QUERY_VIDEO_STREAMER $QUERY_ID $VIDEO_OUTPUT_TYPE | $FFMPEG_BIN -f rawvideo -r $FPS -pixel_format bgr24 -video_size $VIDEO_SIZE -i - -vf -vcodec libx264 -profile:v main -pix_fmt yuv420p -preset ultrafast -tune zerolatency  -r 10 -g 10 -keyint_min 10 -sc_threshold 0 -b:v 2000k -maxrate 2000k -bufsize 2000k -s 768x432 -acodec aac  -f flv ${OUPUT_MEDIA_SERVER_URL}$QUERY_ID



# ffmpeg -f rawvideo -pixel_format bgr24 -video_size 768x432 -i - -vf format=yuv420p -c:v libx264 -profile:v main -preset ultrafast -f flv rtmp://localhost/app/mystream



# ffmpeg -f v4l2 -i /dev/video0 -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 -profile:v main -pix_fmt yuv420p -vcodec libx264 -r 10 -s 768x432 -acodec aac -f flv rtmp://localhost:1935/app/mystream



python $QUERY_VIDEO_STREAMER $QUERY_ID $VIDEO_OUTPUT_TYPE | $FFMPEG_BIN -f rawvideo -r $FPS -pixel_format bgr24 -video_size $VIDEO_SIZE -i - -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 -map 0:v -map 1:a -vf format=yuv420p -c:v libx264 -profile:v main -preset ultrafast -tune zerolatency  -r $FPS -g $FPS -keyint_min $FPS -sc_threshold 0 -b:v 2000k -maxrate 2000k -bufsize 2000k -s $VIDEO_SIZE -c:a aac -f flv ${OUPUT_MEDIA_SERVER_URL}$QUERY_ID