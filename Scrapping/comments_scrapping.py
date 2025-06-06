import time
import csv
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

# Use ChromeDriverManager to automatically manage driver
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()))  # Automatically installs the correct version of chromedriver

# Function to parse the date into the desired format
def parse_date_format(raw_date):
    try:
        # Handle format like "May 21, 2024" or "July 15, 2023"
        if ',' in raw_date and len(raw_date.split(" ")[0]) > 3:
            parsed_date = datetime.strptime(raw_date, "%B %d, %Y")
            return parsed_date
        # Handle other possible formats here
        return None  # If no format matches, return None
    except Exception as e:
        print(f"Error parsing date: {raw_date} - {e}")
        return None  # Return None if it doesn't match any format

# Function to scrape reviews with date and hours played
def scrape_reviews(driver, game_url, target_reviews=600):
    driver.get(game_url)
    reviews_collected = 0
    review_data = []

    while reviews_collected < target_reviews:
        try:
            body = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(2)

            review_elements = driver.find_elements(By.CSS_SELECTOR, '.apphub_Card')

            for review_element in review_elements:
                try:
                    # Extract review text
                    review_text = review_element.find_element(By.CSS_SELECTOR, '.apphub_CardTextContent').text
                    review_lines = review_text.split("\n")
                    clean_review_text = " ".join(review_lines[1:]).strip()

                    # Extract date
                    date_element = review_element.find_element(By.CSS_SELECTOR, '.date_posted')
                    raw_date = date_element.text.replace("Posted: ", "").strip()
                    formatted_date = parse_date_format(raw_date)

                    # Extract hours played
                    hours_element = review_element.find_element(By.CSS_SELECTOR, '.hours')
                    hours_played = hours_element.text if hours_element else "Unknown Hours"
                    if "hrs on record" in hours_played:
                        hours_played = hours_played.replace("hrs on record", "").strip()

                    # Extract recommendation
                    recommendation_element = review_element.find_element(By.CSS_SELECTOR, '.title')
                    recommendation = recommendation_element.text.strip()  # "Recommended" or "Not Recommended"

                    # Extract helpful votes
                    helpful_vote_text = ""
                    try:
                        helpful_vote_element = review_element.find_element(By.CSS_SELECTOR, '.found_helpful')
                        helpful_vote_text = helpful_vote_element.text.strip()
                    except:
                        helpful_vote_text = "No helpful votes"

                    # Avoid duplicates
                    if clean_review_text and formatted_date and (formatted_date, clean_review_text, hours_played, recommendation, helpful_vote_text) not in review_data:
                        review_data.append((formatted_date, clean_review_text, hours_played, recommendation, helpful_vote_text))

                except Exception as e_inner:
                    print(f"Skipping a review due to error: {e_inner}")

            reviews_collected = len(review_data)
            print(f"Reviews collected: {reviews_collected}")

            if reviews_collected >= target_reviews:
                break

        except StaleElementReferenceException:
            print("Stale element found, retrying...")
            time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")
            break

    return review_data

# Function to save all reviews to a single CSV
def save_reviews_to_csv(game_name, reviews):
    filename = f"{game_name}_reviews.csv"
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Game", "Date", "Review", "Hours Played", "Recommendation", "Helpful Votes"])
        for review in reviews:
            writer.writerow([game_name, *review])

# List of game URLs you want to scrape
game_urls = [
    'https://steamcommunity.com/app/105600/reviews/?browsefilter=toprated&snr=1_5_100010_&p=1&filterLanguage=english#scrollTop=0', #csgo
    #'https://steamcommunity.com/app/578080/reviews/?browsefilter=toprated&snr=1_5_100010_&p=1&filterLanguage=english#scrollTop=0', #pubg
    #'https://steamcommunity.com/app/1172470/reviews/?p=1&browsefilter=toprated&filterLanguage=english',
    #'https://steamcommunity.com/app/359550/reviews/?p=1&browsefilter=toprated&filterLanguage=english',
    #'https://steamcommunity.com/app/1938090/reviews/?p=1&browsefilter=toprated&filterLanguage=english'
]

# Dictionary to store all reviews
all_reviews = {}

# Iterate through each game URL and scrape reviews
output_file = "terraria_reviews_with_metadata.csv"
first_game = True  # To control when to write the header

for url in game_urls:
    game_name = url.split("/")[4]
    reviews = scrape_reviews(driver, url)
    save_reviews_to_csv(game_name, reviews)
    print(f"Saved reviews to {game_name}_reviews.csv")

print("All reviews saved to reviews_with_metadata.csv")

# Close the WebDriver after scraping
driver.quit()
