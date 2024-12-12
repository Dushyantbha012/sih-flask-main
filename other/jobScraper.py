from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse

TRUSTED_SITES = [
    "linkedin.com",
    "indeed.com",
    "glassdoor.com",
    "monster.com",
    "careerbuilder.com",
    "ziprecruiter.com",
    "remotive.io",
    "angel.co",
    "weworkremotely.com",
    "jobsearch.com",
    "flexjobs.com",
    "remote.co",
    "remoteworkers.co",
    "workingnomads.co",
    "jobspresso.co",
    "careerjet.com",
    "simplyhired.com",
    "jobvite.com",
    "hired.com",
    "theladders.com",
    "techcareers.com",
    "angel.co/jobs",
    "gitconnected.com",
    "upwork.com",
    "fiverr.com",
    "toptal.com",
    "freelancer.com",
    "monster.ca",
    "seek.com.au",
    "reed.co.uk",
    "jobstreet.com",
    "glassdoor.co",
    "naukri.com",
    "nielit.gov.in",
    "aicte-india.org",
]


def fetch_trusted_search_links(
    query,
    output_trusted="trusted_search_links.txt",
    output_untrusted="untrusted_search_links.txt",
    num_results=10,
):
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

    for i in range(len(allData)):
        link = allData[i].find("a").get("href")
        if link is not None:
            parsed_domain = urlparse(link).netloc.lower()
            if any(trusted_site in parsed_domain for trusted_site in TRUSTED_SITES):
                trusted_links.append(link)
            else:
                untrusted_links.append(link)

    with open(output_trusted, "w", encoding="utf-8") as file:
        for link in trusted_links:
            file.write(link + "\n")

    with open(output_untrusted, "w", encoding="utf-8") as file:
        for link in untrusted_links:
            file.write(link + "\n")

    print(f"Trusted links have been saved to '{output_trusted}'.")
    print(f"Untrusted links have been saved to '{output_untrusted}'.")

    return trusted_links


def get_links(job_type, role, location, years):

    if job_type == "internship":
        query = f"{role} internship posting with {location} location and {years} of experience required"
    elif job_type == "private":
        query = f"{role} private job posting with {location} location and {years} of experience required"
    elif job_type == "government":
        query = f"{role} government job posting in India with {location} location and {years} of experience required"
    else:
        print("Invalid job type. Please enter 'internship', 'private', or 'govt'.")
        exit(1)

    trusted = fetch_trusted_search_links(query, num_results=100)

    return trusted