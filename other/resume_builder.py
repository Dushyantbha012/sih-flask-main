from groq import Groq
import os

client = Groq(api_key="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")

def resume_builder(resume, job_description):
    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {
                "role": "user",
                "content": f"Build a custom resume for this job posting. Here is the resume: {resume} and here is the job description: {job_description}"
            },
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )
    
    return completion.choices[0].message.content
