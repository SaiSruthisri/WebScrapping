import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import os

async def scrape_amazon_jobs(start_offset=0, end_offset=2650):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # URL template for the Amazon jobs page
        url_template = 'https://www.amazon.jobs/en/search?offset={}&result_limit=10&sort=relevant&distanceType=Mi&radius=24km&latitude=28.63142&longitude=77.21677&loc_group_id=&loc_query=India&base_query=&city=&country=IND&region=&county=&query_options='

        # Load existing job details
        existing_jobs = load_existing_jobs()

        for offset in range(start_offset, end_offset + 1, 10):  # Increment offset by 10
            print(f"Fetching job listings from offset {offset}...")
            await page.goto(url_template.format(offset))
            await page.wait_for_timeout(3000)  # Wait for the page to load

            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            job_cards = soup.find_all('div', class_='info first col-12 col-md-8')
            print(f"Found {len(job_cards)} job cards.")

            all_jobs_details = []

            for card in job_cards:
                try:
                    job_title = card.find('h3', class_='job-title').text.strip()
                    location_and_id = card.find('ul', class_='list-unstyled')
                    location = location_and_id.find('li', class_='text-nowrap').text.strip()
                    job_id = location_and_id.find_all('li')[-1].text.strip().replace('Job ID: ', '')

                    job_link = "https://www.amazon.jobs" + card.find('a', class_='job-link')['href']
                    await page.goto(job_link)

                    job_content = await page.content()
                    job_soup = BeautifulSoup(job_content, 'html.parser')

                    company = "Amazon"
                    eligibility_tag = job_soup.find('h2', text='BASIC QUALIFICATIONS')
                    eligibility_criteria = eligibility_tag.find_next('p').text.strip() if eligibility_tag else "Not available"
                    years_of_experience = eligibility_criteria.split('\n')[0].split('-')[1].strip() if eligibility_criteria else "Not available"

                    description_tag = job_soup.find('h2', text='DESCRIPTION')
                    job_description = description_tag.find_next('p').text.strip() if description_tag else "Not available"

                    apply_button = job_soup.find('a', id='apply-button')
                    apply_link = apply_button['href'] if apply_button else "Not available"
                    
                    job_details = {
                        "company": company,
                        "job_title": job_title,
                        "eligibility_criteria": eligibility_criteria,
                        "job_description": job_description,
                        "years_of_exp": years_of_experience,
                        "location": location,
                        "job_type": None,
                        "apply_link": apply_link
                    }

                    all_jobs_details.append(job_details)
                    print(f"Job details for '{job_title}' collected.")

                    await asyncio.sleep(1)  # Delay to prevent getting blocked

                except Exception as e:
                    print(f"Error processing job card '{job_title}': {e}")

            # Check for new or updated jobs
            check_for_updates(existing_jobs, all_jobs_details)

            # Update existing jobs with the current data
            existing_jobs = {job['job_title']: job for job in all_jobs_details}

        # Save final job listings to JSON
        save_jobs(existing_jobs.values())

        await browser.close()

def load_existing_jobs():
    """Load existing job details from the JSON file."""
    if os.path.exists('amazon_jobs.json'):
        with open('amazon_jobs.json', 'r') as json_file:
            return {job['job_title']: job for job in json.load(json_file)}
    return {}

def check_for_updates(existing_jobs, current_jobs):
    """Check for new or updated jobs and save them."""
    new_jobs = []
    for job in current_jobs:
        if job['job_title'] not in existing_jobs:
            new_jobs.append(job)
            print(f"New job found: {job['job_title']}")
    
    if new_jobs:
        save_jobs(new_jobs)

def save_jobs(new_jobs):
    """Save new job details to the JSON file."""
    if os.path.exists('amazon_jobs.json'):
        with open('amazon_jobs.json', 'r') as json_file:
            existing_jobs = json.load(json_file)
    else:
        existing_jobs = []

    existing_jobs.extend(new_jobs)
    
    with open('amazon_jobs.json', 'w') as json_file:
        json.dump(existing_jobs, json_file, indent=4)

    print("Updated job details saved to 'amazon_jobs.json'.")

# Run the asynchronous function
asyncio.run(scrape_amazon_jobs(start_offset=0, end_offset=2650))

