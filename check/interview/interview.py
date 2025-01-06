import PyPDF2
from groq import Groq
import os


os.environ["TOKENIZERS_PARALLELISM"] = "false"

class InterviewAssistant:
    def __init__(self, pdf_path, n_q=5, duration=30,difficulty="entry-level"):
        self.api_key = "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"
        self.client = Groq(api_key="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")
        self.pdf_path = pdf_path
        self.n_q = n_q
        self.duration = duration
        self.resume = self.extract_text_from_pdf(pdf_path)
        self.difficulty = difficulty
        self.q_a_list = []  # Initialize an empty list to store question-answer pairs

    def extract_text_from_pdf(self, pdf_path):
        # Extract text from each page of the PDF
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text.strip() #Returns the extracted text

    def retrieve_all_q_a(self):
        # Retrieve all question-answer pairs from the list
        return {qa['question']: qa['answer'] for qa in self.q_a_list} #Dictionary of all questions and answers

    def generate_question(self):
        context = self.retrieve_all_q_a()
        # Generate a technical question based on the resume and previous questions
        prompt = f"""
        Based on the project details in this resume: {self.resume}, and the previous questions asked and their answers: {context}, 
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
    def add_ques_ans(self, question, answer):
        # Add a question-answer pair to the list
        self.q_a_list.append({
            "question": question,
            "answer": answer
        })
    def analyze_responses(self,):
        all_ques_ans = self.retrieve_all_q_a()
        list_n = [{'Question': q, 'Answer': a} for q, a in all_ques_ans.items()]
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

# Path to the PDF file containing the resume
pdf_path = "/Users/kabirarora/Desktop/Resume_google_final.pdf"
