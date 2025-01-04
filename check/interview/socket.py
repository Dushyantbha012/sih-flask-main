import websockets
import asyncio
import random
import string
import os
import requests


from .firebasae_interview import InterviewAssistant

async def handle_interview(websocket, interview_assistant):
    """
    Event-based interview handling using InterviewAssistant as reference.
    """
    while True:
        try:
            message = await websocket.recv()
            if message == "start_interview":
                interview_assistant.clear_database()
                await websocket.send("Database cleared. Please specify difficulty.")
            elif message.startswith("difficulty:"):
                difficulty = message.split(":", 1)[1]
                context_old = interview_assistant.retrieve_all_q_a()
                question = interview_assistant.generate_question(context_old, difficulty)
                interview_assistant.text_to_speech(question)
                await websocket.send(f"Question asked: {question}")
            elif message == "record_answer":
                audio_data = interview_assistant.record_answer()
                answer_text = interview_assistant.convert_audio_to_text(audio_data)
                await websocket.send(f"Answer recorded: {answer_text}")
                if answer_text:
                    # Use question as doc_id, or something unique
                    doc_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
                    interview_assistant.db.collection(interview_assistant.collection_name).document(doc_id).set({
                        "question": "Previous question placeholder",
                        "answer": answer_text
                    })
            elif message == "analyze":
                all_ques_ans = interview_assistant.retrieve_all_q_a()
                list_n = [{'Question': q, 'Answer': a} for q, a in all_ques_ans.items()]
                insight = interview_assistant.analyze_responses(list_n)
                interview_assistant.text_to_speech(insight)
                await websocket.send(f"Analysis: {insight}")
            elif message == "stop_interview":
                await websocket.send("Interview session stopped.")
                break
        except websockets.exceptions.ConnectionClosed:
            break

async def interview_socket_handler(websocket, path):
    try:
        data = await websocket.recv()
        pdf_url, n_q = data.split(';')
        n_q = int(n_q)

        # Generate random filename
        random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32)) + ".pdf"
        save_dir = "resume_pdf"
        os.makedirs(save_dir, exist_ok=True)
        pdf_path = os.path.join(save_dir, random_name)

        # Download and save PDF
        download_pdf(pdf_url, pdf_path)

        # Conduct interview using the downloaded PDF
        api_key = "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"
        interview_assistant = InterviewAssistant(api_key, pdf_path, n_q=n_q, duration=1000)
        await handle_interview(websocket, interview_assistant)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # Remove the downloaded PDF upon disconnection
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

async def main():
    server = await websockets.serve(interview_socket_handler, "localhost", 8765)
    await server.wait_closed()

def download_pdf(url, save_path):
    response = requests.get(url)
    with open(save_path, 'wb') as f:
        f.write(response.content)

if __name__ == "__main__":
    asyncio.run(main())
