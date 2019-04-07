import sys
import os
import speech_recognition as sr
import pyaudio
import wave
from tqdm import tqdm

sys.path.append('../')
from pathlib import Path
home = str(Path.home())
BASE_DIR = "/"
sys.path.append(BASE_DIR)

from flask import Flask
from flask import jsonify
from flask import request
from flask import Response
from flask_cors import CORS
from multiprocessing.dummy import Pool

with open("api-key.json") as f:
        GOOGLE_CLOUD_SPEECH_CREDENTIALS = f.read()
r = sr.Recognizer()

sys.path.append('../')
app = Flask(__name__)
CORS(app)
app.config['DEBUG'] = True


def transcribe(data):
    
    idx, file = data 
    name = "parts/" + file
    print(name + " started")
    # Load audio file
    with sr.AudioFile(name) as source:
        audio = r.record(source)
    # Transcribe audio file
    text = r.recognize_google_cloud(audio, credentials_json=GOOGLE_CLOUD_SPEECH_CREDENTIALS)
    print(text + " done")
    return {
        "idx": idx,
        "text": text
    }


@app.route("/recordAudio")
def recordAudio():
    try:
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 2
        RATE = 44100
        RECORD_SECONDS = 5
        WAVE_OUTPUT_FILENAME = "parts/output-from-api.wav"

        p = pyaudio.PyAudio()

        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        print("* recording")

        frames = []

        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)

        print("* done recording")

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        pool = Pool(8) # Number of concurrent threads
        files = sorted(os.listdir('parts/'))
        all_text = pool.map(transcribe, enumerate(files))
        pool.close()
        pool.join()

        transcript = ""
        for t in sorted(all_text, key=lambda x: x['idx']):
            total_seconds = t['idx'] * 30
            # Cool shortcut from:
            # https://stackoverflow.com/questions/775049/python-time-seconds-to-hms
            # to get hours, minutes and seconds
            m, s = divmod(total_seconds, 60)
            h, m = divmod(m, 60)

            # Format time as h:m:s - 30 seconds of text
            transcript = transcript + "{:0>2d}:{:0>2d}:{:0>2d} {}\n".format(h, m, s, t['text'])

        print(transcript)

        with open("transcript.txt", "w") as f:
            f.write(transcript)

    except Exception as e:
        print("Cannot recognise the statement")
        transcript = "Cannot recognise the statement"
        print(e)
    
    return transcript

if __name__ == '__main__':
    
    app.run()