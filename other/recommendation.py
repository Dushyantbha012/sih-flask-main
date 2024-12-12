from groq import Groq
import os

client = Groq(api_key="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")

def get_bot_response(user_input,resume_text):
    chat_completion = client.chat.completions.create(
       messages=[
        {
            "role": "system",
            "content": "You Are An Profile Analyser Analyse The Interviews Profile Professionaly"
        },
        {
            "role": "user",
            "content": f"Respond to this prompt {user_input} using this data {resume_text}",
        }
    ],
        model="llama3-8b-8192",
        max_tokens=1000
    )
    return chat_completion.choices[0].message.content

def generate_recommendation(resume_text, job_description,responsibilities,requirements,experience,location,jobType,mode,organization,title,salary):
    query = f"""
    Job Description:

    You will critically and in a high level analyze a job seeker's profile based on the following job description and evaluate it across several key parameters. Provide an overall rating out of 100, considering the alignment of the job seeker’s profile which is given to you with the job description. The parameters you should consider are: Skills Match, Experience, Education, Accomplishments, Cultural Fit, Geographical Fit, Career Progression, Availability, Industry Knowledge, and Recommendations/References.

    ---

    Job Description:

    {job_description}

    Responsibilities:

    {responsibilities}

    Requirements:

    {requirements}

    Expirience:

    {experience}

    Location:

    {location}

    Job Type:

    {jobType}

    Mode:

    {mode}

    Organisation:

    {organization}

    Title:

    {title}

    Salary:

    {salary}
    ---
    Instructions:

    Instructions:

    1. Skills Match (0-25 points):
    - Evaluate how well the job seeker's technical and soft skills align with the job requirements.

    2. Experience (0-25 points):
    - Consider the relevance of the job seeker's years of experience, prior roles, and industry experience to the job description.

    3. Education (0-10 points):
    - Assess the relevance of the job seeker’s educational background, including degrees and certifications, to the job requirements.

    4. Accomplishments (0-10 points):
    - Evaluate the significance of the job seeker's professional achievements and project experience in relation to the job description.

    5. Geographical Fit (0-5 points):
    - Consider the job seeker’s location in relation to the job location and their willingness to relocate, if necessary.

    6. Career Progression (0-10 points):
    - Evaluate the job seeker’s career growth trajectory and their ability to take on increasing responsibilities.

    7. Availability (0-5 points):
    - Assess the job seeker’s availability to start work and their willingness to commit to the company.

    8. Industry Knowledge (0-5 points):
    - Evaluate the job seeker’s understanding of industry trends and market conditions, and their ability to contribute valuable insights.

    9. Recommendations/References (0-5 points):
        - Assess the quality and relevance of the job seeker’s recommendations or references.

    ---
    Output format:

    Overall Rating: [Sum of all points out of 100]

    Strengths:
    - [Strength 1]
    - [Strength 2]
    - ...

    Weaknesses:
    - [Weakness 1]
    - [Weakness 2]
    - ...

    Overall Assessment:
    [Provide a brief summary of the job seeker’s strengths and weaknesses in relation to the job description, highlighting the key factors that influenced the overall rating.]
    """

    return get_bot_response(query,resume_text)
