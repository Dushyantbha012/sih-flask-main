import json
import fitz
import redis
import os
from resume_builder import resume_builder
from recommendation import generate_recommendation
from interview import InterviewAssistant
import requests
from checkpoints import get_courses
from jobScraper import get_links

redisClient = redis.Redis()

def download_pdf(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    return False

def pdf_to_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    
    for page_num in range(doc.page_count):
        page = doc[page_num]
        text += page.get_text()
    
    doc.close()
    return text


api_key = "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"

print("RUNNING: REDIS AI BACKEND")

while True:
    try:
        response = redisClient.rpop("messages")
        if response:
            print("hello\n")
            res = json.loads(response)
            print("hello2\n")
            clientId = res['clientId']
            message = res['message']  # No need to load it again
            type = message['type']
            data = message['data']
            
            print(json.dumps(data, indent=4))
            if type == "GET_RECOMMENDATION":
                job_description = data.get('description')
                responsibilities = data.get('responsibilities')
                requirements = data.get('requirements')
                experience = data.get('experience')
                location = data.get('location')
                jobType = data.get('jobType')
                mode = data.get('mode')
                organization = data.get('organization')
                title = data.get('title')
                salary = data.get('salary')
                resume = data.get('resume')
                print("here in recommendation 3 resume: ",resume, " description ", job_description)
                if not resume or not job_description:
                    redisClient.publish(clientId,json.dumps({"type": "ERROR", "message": "Job Description and Resume Absent"}))
                    continue
                try:
                    print("here in recommendation 4")
                    pdf_path = 'downloaded_resume.pdf'
                    if not download_pdf(resume, pdf_path):
                        redisClient.publish(clientId,json.dumps({"type": "ERROR", "message": "Not able to download PDF"}))
                        continue
                    resume_text = pdf_to_text(pdf_path)
                    print("here in recommendation 5")
                    recommendation = generate_recommendation(resume_text,job_description,responsibilities,requirements,experience,location,jobType,mode,organization,title,salary)
                    os.remove(pdf_path)
                    similarity_score_json = {
                        "type": "RECOMMENDATION",
                        "payload": {
                            "recommendation": recommendation
                        }
                    }
                    print(recommendation)
                    json_string = json.dumps(similarity_score_json)
                    redisClient.publish(clientId,json_string)
                    print("published")
                except Exception as e:
                    redisClient.publish(clientId,json.dumps({"type": "ERROR", "payload": {"message": "Not able to download PDF"}}))
                pass
            elif type == "GET_RESUME_BUILD":
                job_description = data.get('job_description')
                resume = data.get('resume')
                if not resume or not job_description:
                    redisClient.publish(clientId,json.dumps({"type": "ERROR", "message": "Job Description and Resume Absent"}))
                    continue
                try:
                    pdf_path = 'downloaded_resume.pdf'
                    if not download_pdf(resume, pdf_path):
                        redisClient.publish(clientId,json.dumps({"type": "ERROR", "message": "Not able to download PDF"}))
                        continue
                    resume_text = pdf_to_text(pdf_path)
                    
                    resume_built = resume_builder(resume_text,job_description)
                    os.remove(pdf_path)
                    resume_json = json.dumps({
                        "type": "RESUME_BUILD",
                        "payload": {
                            "resume": resume_built
                        }
                    })
                    print(resume_json)
                    redisClient.publish(clientId,resume_json)
                except Exception as e:
                    redisClient.publish(clientId,json.dumps({"type": "ERROR", "payload": {"message": "Not able to download PDF"}}))
                pass
            elif type == "GET_QUESTIONS":
                resume = data.get('resume')
                if not resume:
                    redisClient.publish(clientId,json.dumps({"type": "ERROR", "message": "Resume Absent"}))
                    continue
                try:
                    pdf_path = 'downloaded_resume.pdf'
                    if not download_pdf(resume, pdf_path):
                        redisClient.publish(clientId,json.dumps({"type": "ERROR", "message": "Not able to download PDF"}))
                        continue
                    assistant = InterviewAssistant(api_key=api_key, pdf_path=pdf_path)    
                    questions = assistant.generate_questions()
                    #questions = ["What is your name?", "What is your experience?", "What are your skills?"]
                    os.remove(pdf_path)
                    score_json = json.dumps({
                        "type": "SIMILARITY_SCORE",
                        "payload": {
                            "questions": questions
                        }
                    })
                    redisClient.publish(clientId,score_json)
                    print("published")
                except Exception as e:
                    print(e)
                    redisClient.publish(clientId,json.dumps({"type": "ERROR", "payload": {"message": "An Error Occurred"}}))
                pass
            elif type == "GET_INTERVIEW_ANALYSIS":
                question_responses = data.get('question_responses')
                if not question_responses:
                    redisClient.publish(clientId,json.dumps({"type": "ERROR", "message": "Question Responses Absent"}))
                    continue
                try:
                    print("hello in here")
                    assistant = InterviewAssistant()
                    analysis_results = []  

                    for item in question_responses:
                        print("item: ",item)
                        question = item.get('question')
                        transcript = item.get('transcript')

                        if not question or not transcript:
                            continue

                        feedback = assistant.analyze_response(question, transcript)

                        analysisresult = {
                            "question": question,
                            "transcript": transcript,
                            "feedback": feedback
                        }
                        analysis_results.append(analysisresult)
                        print(analysis_results)
                    analysis_result_json = json.dumps(analysis_results)
                    score_json = json.dumps({
                        "type": "INTERVIEW_ANALYSIS",
                        "payload": {
                            "analysis": analysis_result_json
                        }
                    })
                    redisClient.publish(clientId,score_json)
                    print("published")
                except Exception as e:
                    print(e)
                    redisClient.publish(clientId,json.dumps({"type": "ERROR", "payload": {"message": "An Error Occurred"}}))
                pass
            elif type=="GET_CHECKPOINTS":
                try:
                    current = data.get('currentStatus')
                    end_goal = data.get('endGoal')
                    if not current:
                        redisClient.publish(clientId,json.dumps({"type": "ERROR", "message": "Current Status Absent"}))
                        continue
                    if not end_goal:
                        redisClient.publish(clientId,json.dumps({"type": "ERROR", "message": "Final Status Absent"}))
                        continue
                    courses = get_courses(api_key = "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", current =current, end_goal = end_goal, num_courses=5)
                    response_json = json.dumps({
                        "type": "CHECKPOINTS",
                        "payload": {
                            "courses": courses
                        }
                    })
                    print(courses)
                    redisClient.publish(clientId,response_json)
                except Exception as e:
                    print(e)
                    redisClient.publish(clientId,json.dumps({"type": "ERROR", "payload": {"message": "An Error Occurred"}}))
                pass
            elif type=="GET_JOBS_SCRAPED":
                try:
                    jobType = data.get('jobType')
                    role = data.get('role')
                    location = data.get('location')
                    years = data.get('years')
                    if not jobType:
                        redisClient.publish(clientId,json.dumps({"type": "ERROR", "message": "jobType Absent"}))
                        continue
                    if not role:
                        redisClient.publish(clientId,json.dumps({"type": "ERROR", "message": "role Absent"}))
                        continue
                    if not location:
                        redisClient.publish(clientId,json.dumps({"type": "ERROR", "message": "location Absent"}))
                        continue
                    if not years:
                        redisClient.publish(clientId,json.dumps({"type": "ERROR", "message": "years Absent"}))
                        continue
                    jobs = get_links(job_type=jobType, role=role, location=location, years=years)
                    response_json = json.dumps({
                        "type": "SCRAPED_JOB",
                        "payload": {
                            "jobs": jobs
                        }
                    })
                    print(jobs)
                    redisClient.publish(clientId,response_json)
                except Exception as e:
                    print(e)
                    redisClient.publish(clientId,json.dumps({"type": "ERROR", "payload": {"message": "An Error Occurred"}}))
            pass
    except Exception as e:
        print(e)
        redisClient.publish(clientId,json.dumps({"type": "ERROR", "payload": {"message": "Not able to download PDF"}}))