from groq import Groq
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import requests
from pydub import AudioSegment
import speech_recognition as sr
import asyncio
from hume import HumeStreamClient
from hume.models.config import ProsodyConfig
import json

def cultural_fit(audio_url):
    
    if not audio_url:
        return json.dumps({"type": "ERROR", "payload": {"message": "no audio file present"}})

    # Download the audio file
    audio_response = requests.get(audio_url)
    if audio_response.status_code != 200:
        return json.dumps({"type": "ERROR", "payload": {"message": "Failed to download"}})

    # Determine the audio format from Content-Type
    content_type = audio_response.headers.get('Content-Type')
    print('Content-Type:', content_type)


    audio_filename = 'output.wav'
    with open(audio_filename, 'wb') as f:
        f.write(audio_response.content)

    if os.path.getsize(audio_filename) == 0:
        os.remove(audio_filename)
        return json.dumps({"type": "ERROR", "payload": {"message": "audio file is empty"}})
    try:
        audio = AudioSegment.from_file(audio_filename)
    except Exception as e:
        print(f'message loading audio file: {e}')
        os.remove(audio_filename)
        return json.dumps({"type": "ERROR","payload": { "message": "failed to load audio file"}})

    if audio.rms == 0:
        os.remove(audio_filename)
        return json.dumps({"type": "ERROR", "payload": {"message": "audio file is empty"}})
    segment_length = len(audio) // 6 
    audio_segments = [audio[i * segment_length:(i + 1) * segment_length] for i in range(6)]
    emotions = []
    text_segments = []

    # Speech-to-text for full audio
    def stt_full():
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(audio_filename) as source:
                audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            text_segments.append(f"Complete answer: {text}")
        except Exception as e:
            print(f"message during speech recognition for full audio: {e}")
            text_segments.append("Complete answer: [Error processing audio]")

    # Process each segment
    async def process_segment(segment, index):
        segment_filename = f"output_segment_{index}.wav"
        segment.export(segment_filename, format="wav")

        # Check if segment is silent
        if segment.rms == 0:
            print(f"Segment {index} contains only silence.")
            emotions.append(["No emotions detected"] * 3)
            text_segments.append(f"Text for segment {index}: [Silence]")
            os.remove(segment_filename)
            return

        # Hume API for emotions
        try:
            hume_api_key = 'CJffluuY10Z47dNMZSMs4WQ7eBparPq0XYWJduyczGMk9OQO'
            client = HumeStreamClient(hume_api_key)
            config = ProsodyConfig()

            async with client.connect([config]) as socket:
                result = await socket.send_file(segment_filename)
                prediction = result['prosody']['predictions'][0]["emotions"]

            top_emotions = sorted(prediction, key=lambda x: x['score'], reverse=True)[:3]
            emotions.append([f"{e['name']}: {e['score']}" for e in top_emotions])
        except Exception as e:
            print(f"Error during emotion analysis for segment {index}: {e}")
            emotions.append(["Error detecting emotions"] * 3)

        # Speech-to-text for the segment
        try:
            recognizer = sr.Recognizer()
            with sr.AudioFile(segment_filename) as source:
                audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            text_segments.append(f"Text for segment {index}: {text}")
        except Exception as e:
            print(f"Error during speech recognition for segment {index}: {e}")
            text_segments.append(f"Text for segment {index}: [Error processing audio]")

        os.remove(segment_filename)

    # Asynchronous processing of segments
    async def process_all_segments():
        tasks = [process_segment(seg, i) for i, seg in enumerate(audio_segments)]
        await asyncio.gather(*tasks)

    try:
        asyncio.run(process_all_segments())
        stt_full()
    except Exception as e:
        print(f"Error during asynchronous processing: {e}")

    # Generate prompt for Groq API
    question = "What is your favorite programming language?"
    prompt = f"""
You have to judge the user's answer according to what they have spoken (text) and how they have spoken (emotions). 
Only rate it as positive, negative or neutral based on the emotions and the text. Rate the response from 1 to 5 with 5 being the most positive and 1 being the most negative.
Also give a brief explanation of why you rated it as such.

question : {question}

{text_segments[-1]}

text segment 0:{text_segments[0]}
text segment 1:{text_segments[1]}
text segment 2:{text_segments[2]}
text segment 3:{text_segments[3]}
text segment 4:{text_segments[4]}
text segment 5:{text_segments[5]}

Top 3 emotions for segment 0:
{emotions[0][0]}
{emotions[0][1]}
{emotions[0][2]}

Top 3 emotions for segment 1:
{emotions[1][0]}
{emotions[1][1]}
{emotions[1][2]}

Top 3 emotions for segment 2:
{emotions[2][0]}
{emotions[2][1]}
{emotions[2][2]}

Top 3 emotions for segment 3:
{emotions[3][0]}
{emotions[3][1]}
{emotions[3][2]}

Top 3 emotions for segment 4:
{emotions[4][0]}
{emotions[4][1]}
{emotions[4][2]}

Top 3 emotions for segment 5:
{emotions[5][0]}
{emotions[5][1]}
{emotions[5][2]}
"""

    # Groq API for generating the response
    try:
        groq_api_key = "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"
        client = Groq(api_key=groq_api_key)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": prompt}],
            model="llama-3.1-8b-instant",
        )
        response_text = chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error during Groq API call: {e}")
        response_text = "Error generating response"

    os.remove(audio_filename)
    for i in range(len(emotions)) :
        print(f"Top 3 emotions for segment {i+1} :")
        print(emotions[i][0])
        print(emotions[i][1])
        print(emotions[i][2]+"\n")
    return json.dumps({"type": "CULTURAL_FIT","payload": {'result': response_text , 'emotions': emotions}})
    