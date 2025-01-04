# Project Overview
This folder contains the following:
- **socket.py**: A WebSocket server built with websockets, handling connections and directing InterviewAssistant.
- **firebasae_interview.py**: Houses the InterviewAssistant class for generating and analyzing interview questions.

# How It Works
1. **Start the Server**  
   - Run socket.py (e.g., `python socket.py`).  
   - This creates a WebSocket server on localhost:8765.

2. **Connect from Frontend**  
   - In a JavaScript app, open a connection:
   ```js
   const socket = new WebSocket("ws://localhost:8765");
   socket.onopen = () => {
     // First message: PDF URL plus question count
     socket.send("https://example.com/myresume.pdf;3");
   };
   ```
   - Then, send commands like:
   ```js
   socket.send("start_interview");
   socket.send("difficulty:entry-level");
   socket.send("record_answer");
   socket.send("analyze");
   socket.send("stop_interview");
   ```

3. **Event-Based Flow (socket.py)**  
   - On connection, it downloads your PDF and creates an **InterviewAssistant** with the given parameters.  
   - The function `handle_interview` receives messages (e.g., “start_interview,” “record_answer,” “analyze”) and calls the appropriate InterviewAssistant methods.  
   - When the connection closes, the resume PDF is deleted.

4. **InterviewAssistant (firebasae_interview.py)**  
   - **clear_database()**: Removes old Q&A from Firebase.  
   - **generate_question()**: Builds a question using the resume plus previous Q&A.  
   - **record_answer()**: Records mic input and converts it to text.  
   - **analyze_responses()**: Provides feedback based on all collected Q&A.  
   - **text_to_speech()**: Optionally reads out questions/feedback.

5. **Typical Usage**  
   1. “start_interview” → Clears database, awaits difficulty choice.  
   2. “difficulty:X” → Generates the next question.  
   3. “record_answer” → Raises a command to capture audio, transcribe, and store.  
   4. “analyze” → Summarizes all answers with constructive feedback.  
   5. “stop_interview” → Ends the session.

# Summary
Use socket.py to start a WebSocket server, and from your frontend, connect and control the interview flow. InterviewAssistant handles the logic behind the scenes: reading PDFs, asking questions, recording answers, and giving analysis. This event-driven format provides a dynamic, real-time experience.
