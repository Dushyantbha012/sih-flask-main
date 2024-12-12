import PyPDF2
import requests
from groq import Groq
import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"

class InterviewAssistant:
    def __init__(self, api_key="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" , pdf_path=None):
        self.api_key = api_key
        self.client = Groq(api_key=api_key)
        
        if pdf_path: 
            self.resume = self.extract_text_from_pdf(pdf_path)
        else:
            self.resume = ""  

    def extract_text_from_pdf(self, pdf_path):
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()

    def generate_questions(self):
        prompt = f"Generate 5-10 concise and formal technical questions based on the following resume: {self.resume}"
        
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an interviewer who asks only formal and concise questions."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-8b-8192",
            max_tokens=150
        )
        
        return chat_completion.choices[0].message.content.strip().split('\n')

    def analyze_response(self, question, transcript):
        prompt = f"Based on the question: '{question}', evaluate the response: '{transcript}' and provide constructive feedback."
        
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an evaluator who gives constructive feedback on interview responses."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-8b-8192",
            max_tokens=150
        )
        
        return chat_completion.choices[0].message.content.strip()

def download_pdf(url, save_path):
    response = requests.get(url)
    with open(save_path, 'wb') as f:
        f.write(response.content)

# @app.route('/ask_questions', methods=['POST'])
# def ask_questions():
#     data = request.json
#     pdf_url = data.get('pdf_url')
    
#     if not pdf_url:
#         return jsonify({"error": "PDF URL is required"}), 400

#     # Save PDF from the URL
#     pdf_path = 'temp_resume.pdf'
#     download_pdf(pdf_url, pdf_path)

#     api_key = "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" 
#     assistant = InterviewAssistant(api_key, pdf_path)
    
#     questions = assistant.generate_questions()
    
#     os.remove(pdf_path)

#     return jsonify({"questions": questions})

# @app.route('/analyze_responses', methods=['POST'])
# def analyze_responses():
#     data = request.json
#     responses = data.get('responses')  # Access the array of responses

#     if not responses:
#         return jsonify({"error": "Responses data is required"}), 400

#     api_key = "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" 
#     assistant = InterviewAssistant(api_key, pdf_path=None)

#     analysis_results = []  

#     for item in responses:
#         question = item.get('question')
#         transcript = item.get('transcript')

#         if not question or not transcript:
#             return jsonify({"error": "Both question and transcript are required for each response"}), 400

#         feedback = assistant.analyze_response(question, transcript)

#         analysis_result = {
#             "question": question,
#             "transcript": transcript,
#             "feedback": feedback
#         }
#         analysis_results.append(analysis_result)

#     return jsonify({"analysis_results": analysis_results})


# if __name__ == "__main__":
#     app.run(debug=True)