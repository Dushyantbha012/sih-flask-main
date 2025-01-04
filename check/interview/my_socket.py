import websockets
import asyncio
import random
import string
import requests
import os
from firebasae_interview import InterviewAssistant
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_interview(websocket, interview_assistant):
    logger.info("Interview handler started.")
    """
    Event-based interview handling using InterviewAssistant as reference.
    """
    while True:
        try:
            message = await websocket.recv()
            logger.info(f"Received message: {message}")
            if message == "start_interview":
                logger.info("Clearing database.")
                interview_assistant.clear_database()
                await websocket.send("Database cleared. Please specify difficulty.")
            elif message.startswith("difficulty:"):
                logger.info("Difficulty specified by user.")
                difficulty = message.split(":", 1)[1]
                context_old = interview_assistant.retrieve_all_q_a()
                question = interview_assistant.generate_question(context_old, difficulty)
                interview_assistant.text_to_speech(question)
                await websocket.send(f"Question asked: {question}")
            elif message == "record_answer":
                logger.info("Recording answer.")
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
                logger.info("Analyzing responses.")
                all_ques_ans = interview_assistant.retrieve_all_q_a()
                list_n = [{'Question': q, 'Answer': a} for q, a in all_ques_ans.items()]
                insight = interview_assistant.analyze_responses(list_n)
                interview_assistant.text_to_speech(insight)
                await websocket.send(f"Analysis: {insight}")
            elif message == "stop_interview":
                logger.info("Stopping interview.")
                await websocket.send("Interview session stopped.")
                break
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed.")
            break

async def interview_socket_handler(websocket, path):
    logger.info("Socket handler invoked.")
    try:
        data = await websocket.recv()
        logger.info(f"Received initial data: {data}")
        pdf_url, n_q = data.split(';')
        n_q = int(n_q)

        # Generate random filename
        random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32)) + ".pdf"
        save_dir = "resume_pdf"
        os.makedirs(save_dir, exist_ok=True)
        pdf_path = os.path.join(save_dir, random_name)

        logger.info(f"Downloading PDF from {pdf_url} to {pdf_path}")
        # Download and save PDF
        download_pdf(pdf_url, pdf_path)

        logger.info("Conducting interview based on PDF.")
        # Conduct interview using the downloaded PDF
        api_key = "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"
        interview_assistant = InterviewAssistant(api_key, pdf_path, n_q=n_q, duration=1000)
        await handle_interview(websocket, interview_assistant)
    except websockets.exceptions.ConnectionClosed:
        logger.warning("WebSocket connection closed in interview_socket_handler.")
        pass
    finally:
        logger.info("Cleaning up downloaded PDF if it exists.")
        # Remove the downloaded PDF upon disconnection
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

async def main():
    logger.info("Starting WebSocket server on localhost:8765.")
    server = await websockets.serve(interview_socket_handler, "localhost", 8765)
    await server.wait_closed()

def download_pdf(url, save_path):
    logger.info(f"Downloading PDF from: {url}")
    response = requests.get(url)
    with open(save_path, 'wb') as f:
        f.write(response.content)

if __name__ == "__main__":
    asyncio.run(main())
