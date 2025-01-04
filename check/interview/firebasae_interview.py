import tempfile
import time
import numpy as np
import scipy.io.wavfile as wavfile
import sounddevice as sd
from gtts import gTTS
import playsound
import speech_recognition as sr
import PyPDF2
from groq import Groq
import os
import firebase_admin
from firebase_admin import credentials, firestore

os.environ["TOKENIZERS_PARALLELISM"] = "false"

class InterviewAssistant:

    def __init__(self, api_key, pdf_path, collection_name="interview_answers", n_q=2, duration=30,difficulty="entry-level"):
        self.api_key = api_key
        self.client = Groq(api_key=api_key)
        self.pdf_path = pdf_path
        self.n_q = n_q
        self.duration = duration
        self.collection_name = collection_name
        self.resume = self.extract_text_from_pdf(pdf_path)
        self.difficulty = difficulty
        # Initialize Firebase if not already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate("/Users/dushyantbhardwaj/Documents/Projects/sih-flask-main/check/interview/cred.json")
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()


    def extract_text_from_pdf(self, pdf_path):
        # Extract text from each page of the PDF
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text.strip() #Returns the extracted text

    def retrieve_all_q_a(self):
        # Retrieve all question-answer pairs from the Firestore collection
        q_a_dict = {}
        collection_ref = self.db.collection(self.collection_name)
        docs = collection_ref.stream()
        for doc in docs:
            data = doc.to_dict()
            q_a_dict[data['question']] = data['answer']
        return q_a_dict #Dictionary of all questions and answers

    def text_to_speech(self, text, lang='en'):
        # Convert text to speech and play it
        tts = gTTS(text=text, lang=lang, slow=False)
        with tempfile.NamedTemporaryFile(delete=True, suffix='.mp3') as temp_audio_file:
            tts.save(temp_audio_file.name)
            playsound.playsound(temp_audio_file.name)

    def record_answer(self, threshold=0.1, fs=44100):
        # Record audio answer from the user
        print("Recording your answer...")
        audio = []
        start_time = time.time()
        while (time.time() - start_time) < self.duration:
            data = sd.rec(int(fs * 3), samplerate=fs, channels=1, blocking=True)
            audio.append(data)
            if np.max(np.abs(data)) < threshold:
                print("Silence detected, stopping recording.")
                break
        audio = np.concatenate(audio, axis=0)
        print("Recording finished.") 
        return audio #Returns the recorded audio

    def convert_audio_to_text(self, audio_data, fs=44100):
        # Convert recorded audio to text using Google Speech Recognition
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_wav_file:
            wavfile.write(temp_wav_file.name, fs, (audio_data * 32767).astype(np.int16))
            recognizer = sr.Recognizer()
            with sr.AudioFile(temp_wav_file.name) as source:
                audio = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio)
                return text #Returns the recognized text
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand the audio")
                return None
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")
                return None

    def generate_question(self, context):
        # Generate a technical question based on the resume and previous questions
        prompt = f"""
        Based on the project details in this resume: {self.resume}, and the previous questions asked: {context}, 
        create a concise and formal technical question related to the candidate's projects, ensuring it remains professional without any extra phrasing.
        Ask the question directly in less than 15 words.
        Keep the level of the question : {self.difficulty}
        """
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an interviewer who asks only formal and concise questions."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-8b-8192",
            max_tokens=50
        )
        return chat_completion.choices[0].message.content.strip() #Returns the generated question

    def analyze_responses(self, list_n):
        # Analyze the responses and provide feedback
        prompt = f"""
        Based on the following list of question-answer pairs, create an overall analysis of the person's performance. provide specific areas where they can improve. Offer constructive feedback in a professional tone, focusing on actionable improvements in communication, technical understanding, or any other relevant aspects and give an example of how they could have answered the questioned that were asked to them in a detailed and professional way output should be written in a way that you are giving feedback to the person the evaluation of the person should be comprehensive.
        
        Question-Answer pairs: {list_n}
        """
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an evaluator providing a performance review"},
                {"role": "user", "content": prompt}
            ],
            model="llama3-8b-8192",
            max_tokens=500
        )
        return chat_completion.choices[0].message.content.strip() #Returns the generated insights

    def clear_database(self):
        # Clear the Firestore collection
        collection_ref = self.db.collection(self.collection_name)
        docs = collection_ref.stream()
        for doc in docs:
            self.db.collection(self.collection_name).document(doc.id).delete()
        print("Database cleared successfully.") #Prints the message

    def conduct_interview(self):
        # Conduct the interview process
        self.clear_database()
        difficulty = input("Please select the difficulty level (entry-level, mid-level, senior-level): ") # NEW LINE ADDED
        
        for _ in range(self.n_q):
            context_old = self.retrieve_all_q_a()
            print(context_old)
            question = self.generate_question(context_old, self.difficulty)
            self.text_to_speech(question)
            audio_answer = self.record_answer()
            answer_text = self.convert_audio_to_text(audio_answer)

            if answer_text:
                doc_id = str(hash(question))
                self.db.collection(self.collection_name).document(doc_id).set({
                    "question": question,
                    "answer": answer_text
                })
                
        # Retrieve all questions and answers from the database
        all_ques_ans = self.retrieve_all_q_a()
        print(all_ques_ans)

        # Convert the retrieved questions and answers into a list of dictionaries
        list_n = [{'Question': q, 'Answer': a} for q, a in all_ques_ans.items()]

        # Analyze the responses to generate insights
        insight = self.analyze_responses(list_n)

        # Convert the insights into speech
        self.text_to_speech(insight)





# Create an instance of the InterviewAssistant class
# Arguments:
# - api_key: The API key for accessing the interview assistant service
# - pdf_path: The path to the PDF file containing the resume
# - n_q: The number of questions to be asked during the interview
# - duration: The duration of the interview in seconds


# Conduct the interview
# This function will retrieve questions and answers, analyze the responses, and convert the insights into speech
