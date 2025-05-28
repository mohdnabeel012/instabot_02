import json
import os
import re
import time
import random
from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# ========= CONFIGURATION =========
HASHTAGS = ["dropshippingindia", "indiandropshipping", "shopifyindia", "ecomindia"]
WHATSAPP_LINKS_PATH = "whatsapp_links.json"
VISITED_USERS_PATH = "visited_users.json"
SCROLL_COUNT = 5

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
    time.sleep(random.randint(min_sec, max_sec))

# ========= MAIN =========
def run():
    driver = uc.Chrome()
    driver.get("https://www.instagram.com/")

    input("🔐 Please log in to Instagram manually, then press Enter here...")

    visited_users = set(load_json(VISITED_USERS_PATH, []))
    results = load_json(WHATSAPP_LINKS_PATH, [])

    for tag in HASHTAGS:
        print(f"🔍 Searching #{tag}...")
        driver.get(f"https://www.instagram.com/explore/tags/{tag}/")
        time.sleep(5)

        links = set()
        for _ in range(SCROLL_COUNT):
            links.update([a.get_attribute('href') for a in driver.find_elements(By.TAG_NAME, "a") if "/p/" in a.get_attribute('href')])
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
            time.sleep(2)

        print(f"📸 Found {len(links)} post links.")

        for link in list(links)[:50]:
            driver.get(link)
            time.sleep(3)
            try:
                user_elem = driver.find_element(By.XPATH, '//a[contains(@href, "/")]')
                profile_url = user_elem.get_attribute("href")
                username = profile_url.strip("/").split("/")[-1]

                if username in visited_users:
                    continue
                visited_users.add(username)

                driver.get(profile_url)
                time.sleep(3)

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
                    sleep_random(5, 10)

            except Exception as e:
                print(f"❌ Error: {e}")
            save_json(VISITED_USERS_PATH, list(visited_users))
            sleep_random(2, 4)

    print("✅ Done scraping.")
    driver.quit()

run()

