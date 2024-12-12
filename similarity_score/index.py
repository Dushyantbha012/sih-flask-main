import json
import redis
import os
from similarity_score import pdf_to_text, calculate_similarity_score
import requests


redisClient = redis.Redis(
    db=2
)

def download_pdf(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    return False


api_key = "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"

print("RUNNING: REDIS AI BACKEND (Similarity Score) ")

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
            if type == "GET_SIMILARITY_SCORE":
                
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
                    score = calculate_similarity_score(resume_text,job_description)
                    os.remove(pdf_path)
                    score_json = json.dumps({
                        "type": "SIMILARITY_SCORE",
                        "payload": {
                            "score": score
                        }
                    })
                    redisClient.publish(clientId,score_json)
                except Exception as e:
                    redisClient.publish(clientId,json.dumps({"type": "ERROR", "payload": {"message": "Not able to download PDF"}}))
                pass
            
    except Exception as e:
        print(e)
        redisClient.publish(clientId,json.dumps({"type": "ERROR", "payload": {"message": "Not able to download PDF"}}))