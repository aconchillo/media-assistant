# Media Assistant

This is is a demo created for the [Realtime Voice AI and Multimodal
Hackathon](https://partiful.com/e/VJPFposDqQg2eCqHuL38) that happened in San
Francisco on April 13, 2025.

The demo has two components a web client and a backend piece. The web client
will join a [Daily](https://daily.co) meeting room and will receive real-time
video/audio from a remote participant. The remote participant is a backend
Python app that reads a video file (e.g. MP4) and sends that into the
meeting. The backend server will also process the video in real time (using
[Moondream](https://moondream.ai) and will send an audio description (using
ElevenLabs) of the video every 10 seconds.

ℹ️ The first time, things might take some time to get started since the vision
model needs to be downloaded.

## Dependencies

This is the list of technologies used in this demo:

| Service/Library                                 | Description                          |
|-------------------------------------------------|--------------------------------------|
| [Daily](https://daily.co)                       | Real-time Video/Audio Infrastructure |
| [Daily AI](https://github.com/daily-co/dailyai) | Real-time Video/Audio AI framework   |
| [ElevenLabs](https://elevenlabs.io/)            | Text-To-Speech                       |
| [Moondream](https://moondream.ai/)              | AI Vision Model                      |
| [GStreamer](https://gstreamer.freedesktop.org/) | Multimedia framework                 |

## Get started

```python
python3 -m venv venv
source env/bin/activate
pip install -r requirements.txt

cp env.example .env # and add your credentials

```

# Client

Edit the `index.html` and change `DAILY_ROOM_URL` for your Daily room.

Open a browser and load the `index.html` from this repo.

```
open index.html
```

## Run the server

Start the backend server and give it a video file (e.g. MP4).

```bash
python bot.py -i FILE
```
