# Media Assistant

This is is a demo created for the Realtime Voice AI and Multimodal Hackathon
that happened in San Francisco on April 13, 2025.

The demo has two components a web client and a backend piece. The web client
will join a Daily meeting room and will receive real-time video/audio from a
remote participant. The remote participant is a backend Python app that reads a
video file (e.g. MP4) and sends that into the meeting. The backend server will
also process the video in real time (using Moondream) and will send an audio
description (using ElevenLabs) of the video every 10 seconds.

ℹ️ The first time, things might take some time to get started since the vision
model needs to be downloaded.

## Get started

```python
python3 -m venv venv
source env/bin/activate
pip install -r requirements.txt

cp env.example .env # and add your credentials

```

# Client

Edit the `index.html` and look where to enter your Daily room in there.

Open a browser and load the `index.html` from this repo.

```
open index.html
```

## Run the server

Start the backend server and give it a video file (e.g. MP4).

```bash
python bot.py -i FILE
```
