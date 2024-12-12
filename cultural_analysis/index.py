import json
import redis
from cult import cultural_fit
import requests


redisClient = redis.Redis(
    db=1
)

def download_pdf(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    return False


api_key = "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"

print("RUNNING: REDIS AI BACKEND (Culture Analysis)")

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
            if type == "GET_CULTURAL_FIT":
                print("here in fit")
                audio_url = data.get('audio_url')
                if not audio_url:
                    redisClient.publish(clientId,json.dumps({"type": "ERROR", "payload": {"message": "An Error Occurred"}}))
                    continue
                try:
                    culture_fit_score = cultural_fit(audio_url)
                    redisClient.publish(clientId,culture_fit_score)
                    print("published")
                except Exception as e:
                    print(e)
                    redisClient.publish(clientId,json.dumps({"type": "ERROR", "payload": {"message": "An Error Occurred"}}))
                pass
    except Exception as e:
        print(e)
        redisClient.publish(clientId,json.dumps({"type": "ERROR", "payload": {"message": "Not able to download PDF"}}))