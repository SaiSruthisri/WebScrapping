import requests
from bs4 import BeautifulSoup
import json
import os

# Base URL
base_url = 'https://www.aptech-worldwide.com/pages/careers/careers-with-aptech_currentvacancies.html'

# Function to extract job details from each job section
def extract_job_details(fragment, is_first_job):
    job_url = base_url + fragment
    response = requests.get(job_url)
    job_soup = BeautifulSoup(response.content, 'html.parser')
    
    # Set eligibility criteria and exp_needed as null by default
    eligibility_criteria = None
    exp_needed = None
    
    if is_first_job:
        # Extract eligibility criteria
        criteria_section = job_soup.find('h4', string='Desired Candidate Profile:')
        if criteria_section:
            ul = criteria_section.find_next('ul')
            if ul:
                eligibility_criteria = '\n'.join([li.get_text(strip=True) for li in ul.find_all('li')])
        
        # Extract the first line for exp_needed from eligibility_criteria
        if eligibility_criteria:
            exp_needed = eligibility_criteria.split('\n')[0]

    # Extract job description
    job_description = ""
    description_section = job_soup.find('h4', string='Brief Job Description:')
    if description_section:
        ul = description_section.find_next('ul')
        if ul:
            job_description = '\n'.join([li.get_text(strip=True) for li in ul.find_all('li')])
    
    # Construct the apply link as a clean URL
    apply_link = job_url
    
    return {
        'eligibility_criteria': eligibility_criteria,
        'job_description': job_description,
        'apply_link': apply_link,
        'exp_needed': exp_needed
    }

# Main function to scrape all job cards
def scrape_jobs():
    response = requests.get(base_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    jobs = []
    is_first_job = True  # Track the first job
    
    # Extract job links
    job_links = soup.find_all('a', title=True)
    for link in job_links:
        title = link.get('title', '')
        if '(' in title and ')' in title:
            job_title = title.split(' (')[0]
            location = title.split(' (')[1].split(')')[0]
            location = location.replace('&amp;', '&').replace(', ', ', ')
            
            job_link = link.get('href', '')
            if job_link.startswith('#'):
                # Extract additional job details
                details = extract_job_details(job_link, is_first_job)

                # Append job info to list
                jobs.append({
                    'company': 'Aptech',
                    'location': location,
                    'job_title': job_title,
                    'exp_needed': details['exp_needed'],
                    'eligibility_criteria': details['eligibility_criteria'],
                    'job_description': details['job_description'],
                    'apply_link': details['apply_link']
                })
                
                # Set is_first_job to False after handling the first job
                is_first_job = False
    
    return jobs

# Run the scraper and save results to a JSON file
if __name__ == '__main__':
    job_data = scrape_jobs()
    
    # Print current working directory
    print(f"Current directory: {os.getcwd()}")
    
    # Write data to JSON file
    with open('jobs.json', 'w') as f:
        json.dump(job_data, f, indent=4)
    
    print(f"Scraped data saved to jobs.json. Found {len(job_data)} job(s).")

