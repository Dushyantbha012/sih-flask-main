import random
import wave
import pyaudio
from pydub import AudioSegment, silence
import asyncio
from hume import HumeStreamClient
from hume.models.config import ProsodyConfig
import speech_recognition as sr
from groq import Groq
import os

# Create a PyAudio object
p = pyaudio.PyAudio()

# Set up constants for the audio file
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 30
WAVE_OUTPUT_FILENAME = "output.wav"

#Select Random Question

def get_random_question():
        with open("questions.txt", "r") as file:
            questions = file.readlines()                                #NEW CODE ADDED
        return random.choice(questions).strip()


question = get_random_question()
print(question)



# Open a new stream
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("* recording")

frames = []

# Record audio
for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)

print("* done recording")

# Stop the stream
stream.stop_stream()
stream.close()
p.terminate()

# Write the audio data to a WAV file
wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()

# Load the audio file
audio = AudioSegment.from_wav(WAVE_OUTPUT_FILENAME)

# Split the audio into 6 parts - for 30 second audio file 
segment_length = len(audio) // 6 
audio_segments = [audio[i * segment_length:(i + 1) * segment_length] for i in range(6)]

# Initialize list to store results
new_list = []
emotions = []
text_segments = []

# Function to convert complete audio from speech to text
def stt_full(): #Converts the complete audio to text
    recognizer = sr.Recognizer()
    with sr.AudioFile("output.wav") as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data)
        text_segments.append(f"Complete answer: {text}")
    except sr.UnknownValueError:
        print(f"Google Web Speech could not understand the audio in full answer")
    except sr.RequestError:
        print(f"Could not request results from Google Web Speech API for segment full answer")

# Function to process each audio segment with Hume API and STT
async def process_segment(segment, segment_index): #Processes each segment
    segment_filename = f"output_segment_{segment_index}.wav"
    segment.export(segment_filename, format="wav") 

    client = HumeStreamClient("CJffluuY10Z47dNMZSMs4WQ7eBparPq0XYWJduyczGMk9OQO")
    config = ProsodyConfig()

    async with client.connect([config]) as socket:
        result = await socket.send_file(segment_filename)
        result = await socket.send_file(segment_filename)
        result = result['prosody']['predictions'][0]["emotions"]

    top_3_emotions = sorted(result, key=lambda x: x['score'], reverse=True)[:3]
    new_list.append(top_3_emotions)

    current_emotions = {}
    for emotion in top_3_emotions:
        current_emotions[emotion['name']] = emotion['score']
    emotions.append(current_emotions)

    recognizer = sr.Recognizer()
    with sr.AudioFile(segment_filename) as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data)
        text_segments.append(f"Text for segment {segment_index}: {text}")
    except sr.UnknownValueError:
        print(f"Google Web Speech could not understand the audio in segment {segment_index}")
    except sr.RequestError:
        print(f"Could not request results from Google Web Speech API for segment {segment_index}")

def print_output(): #Prints the emotions and text segments
    for i in range(len(emotions)):
        print(f"Top 3 emotions for segment {i + 1}:")
        for emotion, score in emotions[i].items():
            print(f"{emotion} : {score}")
        print()

def generate_summary(emotions, text_segments, question): #Generates the summary of the emotions and text segments
    prompt = f"""
You have to judge the user's answer according to what they have spoken (text) and how they have spoken (emotions). The user does not know that the text has been divided into segments so dont mention the segments, but provide a comprehensive analysis of the user's answer citing from the text segments and emotions as well. Give tips to the user about where and how they can improve.

question : {question}

{text_segments[-1]}

{text_segments[0]}
{text_segments[1]}
{text_segments[2]}
{text_segments[3]}
{text_segments[4]}
{text_segments[5]}

"""
    for i, segment_emotions in enumerate(emotions):
        prompt += f"Top 3 emotions for segment {i}: \n"
        for emotion, score in segment_emotions.items():
            prompt += f"{emotion} : {score}\n" #Prints the emotions for each segment

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": prompt,
            }
        ],
        model="llama-3.1-8b-instant",
    )

    print(chat_completion.choices[0].message.content) #Prints the generated summary

def delete_files():
    os.remove("output.wav")
    for i in range(6):
        os.remove(f"output_segment_{i}.wav")

def calculate_secondary_traits(emotion_scores_list):
    """
    Calculate secondary traits from a list of emotional scores across time segments.
    Takes into account temporal patterns and emotion combinations.
    """
    # First, calculate average emotions across all segments
    avg_emotions = {} #Dictionary to store the average emotions
    num_segments = len(emotion_scores_list)
    for segment in emotion_scores_list:
        for emotion, score in segment.items():
            avg_emotions[emotion] = avg_emotions.get(emotion, 0) + score / num_segments

    # Calculate emotion volatility (how much emotions change between segments)
    emotion_volatility = {} #Dictionary to store the emotion volatility
    for emotion in avg_emotions.keys():
        if num_segments > 1:
            changes = []
            for i in range(num_segments - 1):
                score1 = emotion_scores_list[i].get(emotion, 0)
                score2 = emotion_scores_list[i + 1].get(emotion, 0)
                changes.append(abs(score2 - score1))
            emotion_volatility[emotion] = sum(changes) / len(changes)
        else:
            emotion_volatility[emotion] = 0

def calculate_secondary_traits(emotion_scores_list):
    """
    Calculate secondary traits from a list of emotional scores across time segments.
    Uses only the specified set of emotions.
    """
    # Calculate average emotions across all segments
    avg_emotions = {}
    num_segments = len(emotion_scores_list)
    for segment in emotion_scores_list:
        for emotion, score in segment.items():
            avg_emotions[emotion] = avg_emotions.get(emotion, 0) + score / num_segments

    # Calculate emotion volatility
    emotion_volatility = {} #Dictionary to store the emotion volatility
    for emotion in avg_emotions.keys():
        if num_segments > 1:
            changes = []
            for i in range(num_segments - 1):
                score1 = emotion_scores_list[i].get(emotion, 0)
                score2 = emotion_scores_list[i + 1].get(emotion, 0)
                changes.append(abs(score2 - score1))
            emotion_volatility[emotion] = sum(changes) / len(changes)
        else:
            emotion_volatility[emotion] = 0

    # Define weights for traits using only available emotions
    # Each trait has a set of base emotions, volatility impacts, and combination effects
    weights = {
        "Leadership Potential": {
            "base_emotions": {
                "Determination": 0.3,
                "Pride": 0.2,
                "Satisfaction": 0.2,
                "Confidence": {
                    "Fear": -0.1,
                    "Doubt": -0.1,
                    "Anxiety": -0.1
                }
            },
            "volatility_impact": {
                "Determination": 0.1,
                "Pride": -0.1
            },
            "combinations": [
                (("Determination", "Pride"), 0.1),
                (("Pride", "Fear"), -0.2)
            ]
        },
        "Emotional Resilience": {
            "base_emotions": {
                "Calmness": 0.3,
                "Determination": 0.2,
                "Relief": 0.2,
                "Negatives": {
                    "Anxiety": -0.1,
                    "Fear": -0.1,
                    "Distress": -0.1
                }
            },
            "volatility_impact": {
                "Calmness": 0.2,
                "Anxiety": -0.1
            },
            "combinations": [
                (("Calmness", "Determination"), 0.15),
                (("Anxiety", "Fear"), -0.15)
            ]
        },
        "Creative Thinking": {
            "base_emotions": {
                "Interest": 0.3,
                "Excitement": 0.2,
                "Awe": 0.2,
                "Entrancement": 0.2,
                "Aesthetic Appreciation": 0.1
            },
            "volatility_impact": {
                "Interest": -0.1,  
                "Excitement": -0.1
            },
            "combinations": [
                (("Interest", "Excitement"), 0.15),
                (("Interest", "Boredom"), -0.2)
            ]
        },
        "Empathy": {
            "base_emotions": {
                "Sympathy": 0.3,
                "Empathic Pain": 0.3,
                "Love": 0.2,
                "Adoration": 0.2
            },
            "volatility_impact": {
                "Sympathy": 0.1,
                "Empathic Pain": 0.1
            },
            "combinations": [
                (("Sympathy", "Love"), 0.15),
                (("Contempt", "Disgust"), -0.2)
            ]
        },
        "Problem Solving": {
            "base_emotions": {
                "Concentration": 0.3,
                "Interest": 0.2,
                "Realization": 0.2,
                "Contemplation": 0.2,
                "Confusion": -0.1
            },
            "volatility_impact": {
                "Concentration": 0.1,
                "Confusion": -0.1
            },
            "combinations": [
                (("Concentration", "Interest"), 0.15),
                (("Confusion", "Doubt"), -0.15)
            ]
        },
        "Drive and Motivation": {
            "base_emotions": {
                "Determination": 0.3,
                "Desire": 0.2,
                "Craving": 0.2,
                "Excitement": 0.2,
                "Boredom": -0.1
            },
            "volatility_impact": {
                "Determination": 0.1,
                "Excitement": -0.1
            },
            "combinations": [
                (("Determination", "Desire"), 0.15),
                (("Boredom", "Tiredness"), -0.2)
            ]
        },
        "Adaptability": {
            "base_emotions": {
                "Calmness": 0.3,
                "Surprise (positive)": 0.2,
                "Interest": 0.2,
                "Confusion": -0.1,
                "Surprise (negative)": -0.1
            },
            "volatility_impact": {
                "Calmness": -0.1,  
                "Interest": -0.1
            },
            "combinations": [
                (("Calmness", "Surprise (positive)"), 0.15),
                (("Confusion", "Anxiety"), -0.15)
            ]
        }
    }

    # Calculate trait scores
    trait_scores = {} #Dictionary to store the trait scores
    for trait, trait_weights in weights.items():
        score = 0
        
        # Base emotion contribution
        for emotion, weight in trait_weights["base_emotions"].items():
            if isinstance(weight, dict):  # Handle nested negative emotions
                for sub_emotion, sub_weight in weight.items():
                    score += avg_emotions.get(sub_emotion, 0.1) * sub_weight
            else:
                score += avg_emotions.get(emotion, 0.1) * weight
        
        # Volatility impact
        for emotion, impact in trait_weights.get("volatility_impact", {}).items():
            score += emotion_volatility.get(emotion, 0.1) * impact
        
        # Combination effects
        for (emotion1, emotion2), impact in trait_weights.get("combinations", []):
            combined_score = min(
                avg_emotions.get(emotion1, 0.1), 
                avg_emotions.get(emotion2, 0.1)
            )
            score += combined_score * impact # Add the combined score
        
        # Temporal pattern analysis
        if num_segments > 2:
            # Check for improvement trends
            for emotion in trait_weights["base_emotions"]:
                if isinstance(emotion, str):  # Skip nested dictionaries
                    scores = [segment.get(emotion, 0) for segment in emotion_scores_list]
                    if all(scores[i] <= scores[i+1] for i in range(len(scores)-1)):
                        score *= 1.1  # 10% bonus for consistently improving emotions
        
        trait_scores[trait] = max(0, min(0.5, score))  # Clamp between 0.5 and 1

    # Sort traits by score and return top 5
    sorted_traits = sorted(trait_scores.items(), key=lambda x: x[1], reverse=True) # Sort the traits
    return sorted_traits[:5] # Return the top 5 traits

def print_output():
    """Print emotion analysis and secondary traits for each segment"""
    for i in range(len(emotions)):
        print(f"\nSegment {i + 1}:") #Prints the segment number
        print("Primary Emotions:") #Prints the primary emotions for each segment
        for emotion, score in emotions[i].items():
            print(f"  {emotion}: {score:.3f}") #Prints the emotions for each segment
            
    # Calculate overall traits
    print("\nOverall Secondary Traits:")
    top_traits = calculate_secondary_traits(emotions) #Calculates the secondary traits for the complete audio
    for trait, score in top_traits:
        print(f"  {trait}: {score:.3f}") #Prints the secondary traits for each segment
        
    # Segment-by-segment analysis
    print("\nTemporal Analysis of Secondary Traits:")
    for i in range(len(emotions)):
        print(f"\nSegment {i + 1} Secondary Traits:") #Prints the secondary traits for each segment
        segment_traits = calculate_secondary_traits([emotions[i]])
        for trait, score in segment_traits:
            print(f"  {trait}: {score:.3f}") #Prints the secondary traits for each segment

# Run the async process
async def measurer():
    tasks = [process_segment(segment, i) for i, segment in enumerate(audio_segments)] # Process each segment
    await asyncio.gather(*tasks)  # Concurrently process segments

    stt_full() #Converts the complete audio to text
    print_output() #Prints the emotions and text segments
    delete_files() #Deletes the audio files
    print(generate_summary(emotions, text_segments, question)) #Prints the generated summary
    

# Run the async process
asyncio.run(measurer())