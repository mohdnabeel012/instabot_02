from instagrapi import Client
import json
import os
import re
import random
import time
from datetime import datetime

# ========== CONFIGURATION ==========
CONFIG_PATH = 'config.json'
MESSAGED_USERS_FILE = 'messaged_users.json'
OUTPUT_FILE = 'whatsapp-links.json'
HASHTAGS = ["dropshippingindia", "indiandropshipping", "shopifyindia", "ecomindia"]
MAX_SCRAPED_PER_DAY = 10
TIME_WINDOW_START = 12  # 12 PM
TIME_WINDOW_END = 21    # 9 PM

# ========== UTILITIES ==========
def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def is_within_time_window():
    hour = datetime.now().hour
    return TIME_WINDOW_START <= hour < TIME_WINDOW_END

def sleep_random(min_sec, max_sec):
    duration = random.randint(min_sec, max_sec)
    print(f"⏳ Sleeping for {duration} seconds...")
    time.sleep(duration)

def extract_whatsapp_link(text):
    pattern = r"(https?://)?(www\.)?(wa\.me|chat\.whatsapp\.com|whatsapp\.com/channel|whatsapp\.com/send)/[^\s'\"]+"
    match = re.search(pattern, text)
    if match:
        url = match.group(0)
        return "https://" + url if not url.startswith("http") else url
    return None

# ========== LOAD CREDENTIALS ==========
config = load_json(CONFIG_PATH, {})
USERNAME = config.get("username")
PASSWORD = config.get("password")

if not USERNAME or not PASSWORD:
    raise ValueError("❌ Username or password not set in config.json")

# ========== INSTAGRAM LOGIN ==========
cl = Client()
cl.login(USERNAME, PASSWORD)

# ========== LOAD TRACKING DATA ==========
visited_users = set(load_json(MESSAGED_USERS_FILE, []))
scraped_data = load_json(OUTPUT_FILE, [])

# ========== SCRAPE FUNCTION ==========
def scrape_whatsapp_links():
    print("🚀 Starting scraping session...")
    if not is_within_time_window():
        print("⏰ Outside allowed time (12 PM–9 PM). Exiting.")
        return

    scraped_count = 0
    random.shuffle(HASHTAGS)

    for tag in HASHTAGS:
        try:
            medias = cl.hashtag_medias_recent(tag, amount=50)
        except Exception as e:
            print(f"❌ Error fetching hashtag #{tag}: {e}")
            continue

        print(f"🔍 Scanning #{tag} with {len(medias)} posts...")

        for media in medias:
            user = media.user
            user_id = str(user.pk)
            username = user.username

            if user_id in visited_users:
                continue

            try:
                profile = cl.user_info_by_username(username)
                bio = profile.biography or ""
                url = profile.external_url or ""

                link = extract_whatsapp_link(bio) or extract_whatsapp_link(url)
                visited_users.add(user_id)
                save_json(MESSAGED_USERS_FILE, list(visited_users))

                if link:
                    print(f"✅ Found WhatsApp link for @{username}: {link}")
                    scraped_data.append({
                        "username": username,
                        "whatsapp_link": link
                    })
                    save_json(OUTPUT_FILE, scraped_data)

                    scraped_count += 1
                    if scraped_count >= MAX_SCRAPED_PER_DAY:
                        print(f"🎯 Reached daily limit of {MAX_SCRAPED_PER_DAY}. Exiting.")
                        return

                    # ✅ Sleep after a successful scrape
                    sleep_random(300, 400)

            except Exception as e:
                print(f"❌ Error with @{username}: {e}")
                continue

        # Longer sleep between hashtags
        sleep_random(120, 180)

    print("✅ Scraping session complete.")

# ========== RUN ==========
scrape_whatsapp_links()
