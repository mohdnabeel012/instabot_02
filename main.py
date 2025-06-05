import json
import os
import re
import time
import random
from datetime import datetime
from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# ========= CONFIGURATION =========
HASHTAGS = ["dropshippingindia", "indiandropshipping", "shopifyindia", "ecomindia"]
WHATSAPP_LINKS_PATH = "whatsapp_links.json"
VISITED_USERS_PATH = "visited_users.json"
SCROLL_COUNT = 100

TIME_WINDOW_START = 12  # 12 PM
TIME_WINDOW_END = 23    # 11 PM

# ========= UTILITIES =========
def load_json(path, default):
    return json.load(open(path)) if os.path.exists(path) else default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def extract_whatsapp_link(text):
    pattern = r"(https?://)?(www\.)?(wa\.me|chat\.whatsapp\.com|whatsapp\.com/channel|whatsapp\.com/send)/[^\s'\"]+"
    match = re.search(pattern, text)
    if match:
        url = match.group(0)
        return "https://" + url if not url.startswith("http") else url
    return None

def sleep_random(min_sec, max_sec):
    delay = random.randint(min_sec, max_sec)
    print(f"⏳ Sleeping for {delay} seconds...")
    time.sleep(delay)

def is_within_time_window():
    now = datetime.now()
    return TIME_WINDOW_START <= now.hour < TIME_WINDOW_END

# ========= MAIN =========
def run():
    # Day off chance (10% to 15%)
    if random.random() < random.uniform(0.10, 0.15):
        print("🛌 Taking a day off (random skip to avoid spam)...")
        return

    driver = uc.Chrome()
    driver.get("https://www.instagram.com/")
    input("🔐 Please log in to Instagram manually, then press Enter here...")

    visited_users = set(load_json(VISITED_USERS_PATH, []))
    results = load_json(WHATSAPP_LINKS_PATH, [])

    for tag in HASHTAGS:
        print(f"🔍 Searching #{tag}...")
        driver.get(f"https://www.instagram.com/explore/tags/{tag}/")
        sleep_random(2, 5)

        links = set()
        for _ in range(SCROLL_COUNT):
            if not is_within_time_window():
                print("⏰ Outside allowed time. Sleeping 10 minutes...")
                time.sleep(600)
                continue

            anchors = driver.find_elements(By.TAG_NAME, "a")
            for a in anchors:
                try:
                    href = a.get_attribute('href')
                    if href and "/p/" in href:
                        links.add(href)
                except:
                    continue
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
            sleep_random(4, 9)

        print(f"📸 Found {len(links)} post links.")

        batch_count = 0
        pause_after = random.randint(8, 12)

        for link in list(links)[:50]:
            if not is_within_time_window():
                print("⏰ Outside allowed time. Sleeping 10 minutes...")
                time.sleep(600)
                continue

            driver.get(link)
            sleep_random(2, 5)
            try:
                user_elem = driver.find_element(By.XPATH, '//a[contains(@href, "/")]')
                profile_url = user_elem.get_attribute("href")
                username = profile_url.strip("/").split("/")[-1]

                if username in visited_users:
                    continue
                visited_users.add(username)

                driver.get(profile_url)
                sleep_random(2, 5)

                bio = ""
                try:
                    bio_elem = driver.find_element(By.XPATH, "//div[contains(@class, '_aa_c') or contains(@class, '_aa_c _aa_d')]")
                    bio = bio_elem.text
                except:
                    pass

                try:
                    url_elem = driver.find_element(By.XPATH, "//a[contains(@href, 'http')]")
                    bio += "\n" + url_elem.get_attribute("href")
                except:
                    pass

                link = extract_whatsapp_link(bio)
                if link and "chat.whatsapp.com" in link:
                    print(f"✅ @{username} => {link}")
                    results.append({"username": username, "whatsapp_link": link})
                    save_json(WHATSAPP_LINKS_PATH, results)
                    sleep_random(3, 7)

            except Exception as e:
                print(f"❌ Error: {e}")

            save_json(VISITED_USERS_PATH, list(visited_users))
            batch_count += 1

            if batch_count >= pause_after:
                sleep_time = random.randint(720, 900)
                print(f"😴 Pausing after {batch_count} users for {sleep_time // 60} min...")
                time.sleep(sleep_time)
                batch_count = 0
                pause_after = random.randint(8, 12)
            else:
                sleep_random(110, 150)

    print("✅ Done scraping.")
    driver.quit()

run()
