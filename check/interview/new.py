import websockets
import asyncio
import random
import string
import requests
import os
from interview import InterviewAssistant
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_interview(websocket, interview_assistant):
    logger.info("Interview handler started.")
    """
    Event-based interview handling using InterviewAssistant with JSON messages.
    """
    try:
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                logger.info(f"Received message: {data}")
                action = data.get("action")

                if action == "add_ques_ans":
                    logger.info("Add question answer")
                   
                    answer_text = data.get("answer_text")
                    question=data.get("question")
                    try:
                       
                        if answer_text and question:
                            interview_assistant.add_ques_ans(question, answer_text)
                            await websocket.send(json.dumps({
                                "status": "ok",
                                "code": 200,
                                "action": "add_ques_ans",
                                "message": "Question and answer added successfully."
                            }))
                        else:
                            await websocket.send(json.dumps({
                                "status": "error",
                                "code": 400,
                                "action": "add_ques_ans",
                                "message": "Missing question or answer text."
                            }))
                    except Exception as e:
                        logger.error(f"Error : {e}")
                        await websocket.send(json.dumps({
                            "status": "error",
                            "code": 500,
                            "action": "add_ques_ans",
                            "message": "Server error occurred."
                        }))
                elif action == "get_question":
                    logger.info("Generating questions.")
                    question = interview_assistant.generate_question()
                    await websocket.send(json.dumps({
                        "status": "ok",
                        "code": 200,
                        "action": "get_question",
                        "question": question
                    }))
                    logger.info("Questions sent to socket.")
                elif action == "analyze":
                    logger.info("Analyzing responses.")
                    insight = interview_assistant.analyze_responses()
                    await websocket.send(json.dumps({
                        "status": "ok",
                        "code": 200,
                        "action": "analyze",
                        "analysis": insight
                    }))
                elif action == "stop_interview":
                    logger.info("Stopping interview.")
                    await websocket.send(json.dumps({
                        "status": "ok",
                        "code": 200,
                        "action": "stop_interview",
                        "message": "Interview session stopped."
                    }))
                    break
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed.")
                break

    except Exception as e:
        logger.error(f"Error in handle_interview: {e}")
        await websocket.send(json.dumps({
            "status": "error",
            "code": 500,
            "action": "handle_interview",
            "message": "Server error occurred."
        }))
        
async def interview_socket_handler(websocket):
    logger.info("Socket handler invoked.")
    try:
        data = await websocket.recv()
        initial_data = json.loads(data)
        logger.info(f"Received initial data: {initial_data}")
        pdf_url = initial_data.get("resume_pdf")  # Updated key from "pdf_url" to "resume_pdf"
        n_q = initial_data.get("number_of_ques", 10)  # Updated key from "n_q" to "number_of_ques"
        difficulty = initial_data.get("difficulty")
        if not pdf_url:
            logger.error("PDF URL is missing in initial data.")
            await websocket.send(json.dumps({
                "status": "error",
                "code": 400,
                "action": "pdf_validation",
                "message": "PDF URL is missing."
            }))
            return  # Terminate the handler if PDF URL is missing
        
        random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32)) + ".pdf"
        save_dir = "resume_pdf"
        os.makedirs(save_dir, exist_ok=True)
        pdf_path = os.path.join(save_dir, random_name)
        logger.info(f"Downloading PDF from {pdf_url} to {pdf_path}")
        download_pdf(pdf_url, pdf_path)
        logger.info("Conducting interview based on PDF.")
        interview_assistant = InterviewAssistant( pdf_path=pdf_path, n_q=n_q, duration=1000,difficulty=difficulty)
        logger.info("Clearing database.")
        await websocket.send(json.dumps({
            "status": "ok",
            "code": 200,
            "action": "initial_setup",
            "message": "Basic setup done."
        }))
        logger.info("Sent response: Basic Setup Done")
        await handle_interview(websocket, interview_assistant)
    except websockets.exceptions.ConnectionClosed:
        logger.warning("WebSocket connection closed in interview_socket_handler.")
        pass
    finally:
        logger.info("Cleaning up downloaded PDF if it exists.")
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

async def main():
    logger.info("Starting WebSocket server on localhost:8765.")
    server = await websockets.serve(interview_socket_handler, "localhost", 8765)
    await server.wait_closed()

def download_pdf(url, path):
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url
    response = requests.get(url)
    with open(path, "wb") as f:
        f.write(response.content)


if __name__ == "__main__":
    asyncio.run(main())
