from groq import Groq
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
import json

def get_courses(api_key, current, end_goal, num_courses=5):
    # Trusted learning platforms
    TRUSTED_SITES = [
        "coursera.org", "edx.org", "udemy.com", "khanacademy.org", 
        "codecademy.com", "udacity.com", "futurelearn.com", 
        "skillshare.com", "pluralsight.com", "lynda.com", 
        "datacamp.com", "alison.com", "linkedin.com/learning", 
        "open.edu", "w3schools.com", "sololearn.com", 
        "freecodecamp.org", "mit.edu", "harvard.edu", 
        "stanford.edu", "nptel.ac.in", "swayam.gov.in",
    ]

    # Initialize Groq client
    client = Groq(api_key=api_key)

    # Function to fetch trusted search links
    def fetch_trusted_search_links(query, num_results=10):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
        }
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num={num_results}"

        try:
            html = requests.get(url, headers=headers, timeout=10)
            html.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching search results: {e}")
            return [], []

        soup = BeautifulSoup(html.text, "html.parser")
        allData = soup.find_all("div", {"class": "g"})
        trusted_links = []
        untrusted_links = []

        for data in allData:
            link_tag = data.find("a")
            if link_tag:
                link = link_tag.get("href")
                if link:
                    parsed_domain = urlparse(link).netloc.lower()
                    if any(trusted_site in parsed_domain for trusted_site in TRUSTED_SITES):
                        trusted_links.append(link)
                    else:
                        untrusted_links.append(link)

        return trusted_links, untrusted_links

    # Generate roadmap
    roadmap_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You Are A Roadmap Generator"},
            {
                "role": "user",
                "content": f"{current} - this is the current status of the user, {end_goal} - this is what the user wants to achieve. Now find the user's weakness and create a roadmap for the user to reach their goal. To deal with each weakness, create a checkpoint.",
            },
        ],
        model="llama3-8b-8192",
        max_tokens=1000,
    )
    roadmap_response = roadmap_completion.choices[0].message.content

    # Find course names
    courses_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system", 
                "content": "You are a course name generator. You only generate course names and nothing else."
            },
            {
                "role": "user",
                "content": f"{roadmap_response} - For each checkpoint, suggest a course. In the output, only mention course names separated by commas do not write anything other than that write them in correct order in order of easy to advanced strictly follow the output format",
            },
        ],
        model="llama3-8b-8192",
        max_tokens=1000,
    )
    course_names_response = courses_completion.choices[0].message.content

    course_names = [course.strip() for course in course_names_response.split(",") if len(course.strip()) >= 5]

    courses =[]
    for course_name in course_names[:num_courses]:
        course={}
        trusted, _ = fetch_trusted_search_links(
            f"{course_name} coursera course or edx course or stanford course", 
            num_results=1
        )
        if trusted:
            course["courseName"]=course_name 
            course["courseLink"]= trusted[0]
            courses.append(course)
    courses_json = json.dumps(courses)
    print(courses)
    return courses


