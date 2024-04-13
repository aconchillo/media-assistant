import asyncio
import logging

from dailyai.pipeline.frames import (Frame, AudioFrame, ImageFrame)
from dailyai.pipeline.frame_processor import FrameProcessor

from typing import AsyncGenerator

try:
    import gi
    gi.require_version('Gst', '1.0')
    gi.require_version('GstApp', '1.0')
    from gi.repository import Gst, GstApp, GLib
except ModuleNotFoundError as e:
    print(f"Exception: {e}")
    print(
        "In order to use the GStreamer Daily transport, you need to install GStreamer`.")
    raise Exception(f"Missing module: {e}")

VIDEO_WIDTH = 1024
VIDEO_HEIGHT = 576
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1


class GStreamerFileSource(FrameProcessor):
    def __init__(self, filename: str, sink_queue, loop, **kwargs):
        super().__init__(**kwargs)

        Gst.init()

        self._loop = loop
        self._sink_queue = sink_queue
        self._logger: logging.Logger = logging.getLogger("dailyai")

        self._player = Gst.Pipeline.new("player")

        source = Gst.ElementFactory.make("filesrc", None)
        source.set_property("location", filename)

        decodebin = Gst.ElementFactory.make("decodebin", None)
        decodebin.connect("pad-added", self._decodebin_callback)

        self._player.add(source)
        self._player.add(decodebin)
        source.link(decodebin)

        bus = self._player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_gstreamer_message)

    async def process_frame(self, frame: Frame) -> AsyncGenerator[Frame, None]:
        yield frame

    def start(self):
        self._player.set_state(Gst.State.PLAYING)

    def _on_gstreamer_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            self._logger.error(f"Error: {err} : {debug}")
        return True

    def _decodebin_callback(self, decodebin, pad):
        caps_string = pad.get_current_caps().to_string()
        if caps_string.startswith("audio"):
            self._decodebin_audio(pad)
        elif caps_string.startswith("video"):
            self._decodebin_video(pad)

    def _decodebin_audio(self, pad):
        queue_audio = Gst.ElementFactory.make("queue", None)
        audioconvert = Gst.ElementFactory.make("audioconvert", None)
        audioresample = Gst.ElementFactory.make("audioresample", None)
        audiocapsfilter = Gst.ElementFactory.make("capsfilter", None)
        audiocaps = Gst.Caps.from_string(
            f"audio/x-raw,format=S16LE,rate={AUDIO_SAMPLE_RATE},channels={AUDIO_CHANNELS},layout=interleaved")
        audiocapsfilter.set_property("caps", audiocaps)
        appsink_audio = Gst.ElementFactory.make("appsink", None)
        appsink_audio.set_property("emit-signals", True)
        appsink_audio.connect("new-sample", self._appsink_audio_new_sample)

        self._player.add(queue_audio)
        self._player.add(audioconvert)
        self._player.add(audioresample)
        self._player.add(audiocapsfilter)
        self._player.add(appsink_audio)
        queue_audio.sync_state_with_parent()
        audioconvert.sync_state_with_parent()
        audioresample.sync_state_with_parent()
        audiocapsfilter.sync_state_with_parent()
        appsink_audio.sync_state_with_parent()

        queue_audio.link(audioconvert)
        audioconvert.link(audioresample)
        audioresample.link(audiocapsfilter)
        audiocapsfilter.link(appsink_audio)

        queue_pad = queue_audio.get_static_pad("sink")
        pad.link(queue_pad)

    def _decodebin_video(self, pad):
        queue_video = Gst.ElementFactory.make("queue", None)
        videoconvert = Gst.ElementFactory.make("videoconvert", None)
        videoscale = Gst.ElementFactory.make("videoscale", None)
        videocapsfilter = Gst.ElementFactory.make("capsfilter", None)
        videocaps = Gst.Caps.from_string(
            f"video/x-raw,format=RGB,width={VIDEO_WIDTH},height={VIDEO_HEIGHT}")
        videocapsfilter.set_property("caps", videocaps)

        appsink_video = Gst.ElementFactory.make("appsink", None)
        appsink_video.set_property("emit-signals", True)
        appsink_video.connect("new-sample", self._appsink_video_new_sample)

        self._player.add(queue_video)
        self._player.add(videoconvert)
        self._player.add(videoscale)
        self._player.add(videocapsfilter)
        self._player.add(appsink_video)
        queue_video.sync_state_with_parent()
        videoconvert.sync_state_with_parent()
        videoscale.sync_state_with_parent()
        videocapsfilter.sync_state_with_parent()
        appsink_video.sync_state_with_parent()

        queue_video.link(videoconvert)
        videoconvert.link(videoscale)
        videoscale.link(videocapsfilter)
        videocapsfilter.link(appsink_video)

        queue_pad = queue_video.get_static_pad("sink")
        pad.link(queue_pad)

    def _appsink_audio_new_sample(self, appsink):
        buffer = appsink.pull_sample().get_buffer()
        (_, info) = buffer.map(Gst.MapFlags.READ)
        frame = AudioFrame(info.data)
        asyncio.run_coroutine_threadsafe(self._sink_queue.put(frame), self._loop)
        buffer.unmap(info)
        return Gst.FlowReturn.OK

    def _appsink_video_new_sample(self, appsink):
        buffer = appsink.pull_sample().get_buffer()
        (_, info) = buffer.map(Gst.MapFlags.READ)
        frame = ImageFrame(info.data, (VIDEO_WIDTH, VIDEO_HEIGHT))
        asyncio.run_coroutine_threadsafe(self._sink_queue.put(frame), self._loop)
        buffer.unmap(info)
        return Gst.FlowReturn.OK
