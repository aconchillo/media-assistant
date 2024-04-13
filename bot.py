import asyncio

import aiohttp
import logging
import os
import time

from dailyai.pipeline.frames import (
    Frame, ImageFrame, VisionImageFrame, TextFrame, SendAppMessageFrame
)
from dailyai.pipeline.frame_processor import FrameProcessor
from dailyai.pipeline.pipeline import Pipeline
from dailyai.transports.daily_transport import DailyTransport
from dailyai.services.elevenlabs_ai_service import ElevenLabsTTSService
from dailyai.services.moondream_ai_service import MoondreamService

from typing import AsyncGenerator

from gstreamer_file_source import GStreamerFileSource

from runner import configure

from dotenv import load_dotenv
load_dotenv(override=True)

logging.basicConfig(format=f"%(levelno)s %(asctime)s %(message)s")
logger = logging.getLogger("dailyai")
logger.setLevel(logging.INFO)


class VisionFilterProcessor(FrameProcessor):

    def __init__(self, period):
        self._period = period
        self._last_image_time = 0

    async def process_frame(self, frame: Frame) -> AsyncGenerator[Frame, None]:
        if isinstance(frame, ImageFrame):
            diff_time = time.time() - self._last_image_time
            if diff_time >= self._period:
                yield VisionImageFrame("Describe what you see in a very short sentence", frame.image, frame.size)
                self._last_image_time = time.time()
        yield frame


class VideoDescription(FrameProcessor):
    async def process_frame(self, frame: Frame) -> AsyncGenerator[Frame, None]:
        if isinstance(frame, TextFrame):
            app_message = {
                "type": "gst",
                "text": frame.text
            }
            yield SendAppMessageFrame(app_message, None)
            yield frame
        else:
            yield frame


async def main(room_url: str, token: str, filename: str):
    async with aiohttp.ClientSession() as session:
        transport = DailyTransport(
            room_url,
            token,
            "Media Assistant",
            duration_minutes=5,
            start_transcription=False,
            mic_enabled=True,
            mic_sample_rate=16000,
            camera_enabled=True,
            camera_width=1024,
            camera_height=576,
            camera_framerate=30,
        )

        tts = ElevenLabsTTSService(
            aiohttp_session=session,
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            voice_id="pNInz6obpgDQGcFmaJgB",
        )

        filter = VisionFilterProcessor(period=10)

        moondream = MoondreamService()

        gst = GStreamerFileSource(
            filename=filename,
            sink_queue=transport.receive_queue,
            loop=transport._loop
        )

        descr = VideoDescription()

        pipeline = Pipeline([gst, filter, moondream, descr, tts])

        @transport.event_handler("on_first_other_participant_joined")
        async def on_first_other_participant_joined(transport, participant):
            gst.start()

        await asyncio.gather(transport.run(pipeline))

if __name__ == "__main__":
    (url, token, filename) = configure()
    asyncio.run(main(url, token, filename))
