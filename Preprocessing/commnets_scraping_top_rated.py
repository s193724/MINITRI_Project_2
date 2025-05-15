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
import re

# Setup WebDriver
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install())
)

# Format date
def parse_date_format(raw_date):
    try:
        if ',' in raw_date and len(raw_date.split(" ")[0]) > 3:
            return datetime.strptime(raw_date, "%B %d, %Y")
        return None
    except Exception as e:
        print(f"Error parsing date: {raw_date} - {e}")
        return None

# Sanitize file name
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")

# Scrape reviews and metadata
def scrape_reviews(driver, game_url, target_reviews=500):
    driver.get(game_url)

    # Get game name
    try:
        game_name_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".apphub_AppName"))
        )
        game_name = game_name_elem.text.strip()
    except:
        game_name = "Unknown_Game"

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
                    # Review text
                    review_text = review_element.find_element(By.CSS_SELECTOR, '.apphub_CardTextContent').text
                    review_lines = review_text.split("\n")
                    clean_review_text = " ".join(review_lines[1:]).strip()

                    # Date
                    raw_date = review_element.find_element(By.CSS_SELECTOR, '.date_posted').text.replace("Posted: ", "").strip()
                    formatted_date = parse_date_format(raw_date)

                    # Hours played
                    try:
                        hours_text = review_element.find_element(By.CSS_SELECTOR, '.hours').text
                        hours_played = hours_text.replace("hrs on record", "").strip()
                    except:
                        hours_played = "Unknown Hours"

                    # Likes
                    try:
                        likes_text = review_element.find_element(By.CSS_SELECTOR, '.found_helpful').text.strip()
                        likes = ''.join(filter(str.isdigit, likes_text)) or "0"
                    except:
                        likes = "0"

                    # Replies
                    try:
                        replies_text = review_element.find_element(By.CSS_SELECTOR, '.apphub_CommentCount').text.strip()
                        replies = ''.join(filter(str.isdigit, replies_text)) or "0"
                    except:
                        replies = "0"

                    # Recommendation
                    try:
                        rec_text = review_element.find_element(By.CSS_SELECTOR, '.title').text.strip()
                        recommendation = "Recommended" if "Recommended" in rec_text else "Not Recommended"
                    except:
                        recommendation = "Unknown"

                    if clean_review_text and formatted_date and (formatted_date, clean_review_text) not in review_data:
                        review_data.append((formatted_date, clean_review_text, hours_played, likes, replies, recommendation))
                except Exception as e:
                    print(f"Review error: {e}")
                    continue

            reviews_collected = len(review_data)
            print(f"Collected: {reviews_collected}")

            if reviews_collected >= target_reviews:
                break

        except StaleElementReferenceException:
            print("Stale element, retrying...")
            time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")
            break

    return game_name, review_data

# Save to CSV
def save_reviews_to_csv(game_name, reviews):
    filename = f"reviews_{sanitize_filename(game_name)}.csv"
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Review", "Hours Played", "Likes", "Replies", "Recommendation"])
        for review in reviews:
            writer.writerow(review)
    print(f"Saved to {filename}")

# Game review URLs
game_urls = [
    'https://steamcommunity.com/app/730/reviews/?browsefilter=toprated&snr=1_5_100010_&p=1&filterLanguage=english',
    'https://steamcommunity.com/app/578080/reviews/?browsefilter=toprated&snr=1_5_100010_&p=1&filterLanguage=english',
    'https://steamcommunity.com/app/1172470/reviews/?p=1&browsefilter=toprated&filterLanguage=english',
    'https://steamcommunity.com/app/359550/reviews/?p=1&browsefilter=toprated&filterLanguage=english',
    'https://steamcommunity.com/app/1938090/reviews/?p=1&browsefilter=toprated&filterLanguage=english'
]

# Run for each game
for url in game_urls:
    game_name, reviews = scrape_reviews(driver, url)
    save_reviews_to_csv(game_name, reviews)

driver.quit()
