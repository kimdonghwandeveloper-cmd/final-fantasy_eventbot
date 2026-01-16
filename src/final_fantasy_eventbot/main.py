import os
import time
import json
import logging
import random
import argparse
from typing import List, Optional, Dict, Any

import schedule
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --- Configuration & Constants ---
load_dotenv()

# Environment Variables
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Target Settings
TARGET_URL = "https://www.ff14.co.kr/news/event"
BASE_URL = "https://www.ff14.co.kr"
LATEST_EVENT_FILE = "latest_event.json"

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


# --- Helper Functions ---

def load_latest_event() -> Optional[str]:
    """
    Load the last known event ID from the local JSON file.
    
    Returns:
        Optional[str]: The latest event ID URL, or None if file doesn't exist.
    """
    if not os.path.exists(LATEST_EVENT_FILE):
        return None
    try:
        with open(LATEST_EVENT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("id")
    except Exception as e:
        logger.error(f"Failed to load latest event file: {e}")
        return None


def save_latest_event(event_id: str) -> None:
    """
    Save the latest event ID to the local JSON file to prevent duplicates.
    
    Args:
        event_id (str): The unique ID (URL) of the newest event.
    """
    try:
        with open(LATEST_EVENT_FILE, "w", encoding="utf-8") as f:
            json.dump({"id": event_id}, f, indent=4)
        logger.debug(f"Updated latest event ID to {event_id}")
    except Exception as e:
        logger.error(f"Failed to save latest event file: {e}")


def send_discord_webhook(event: Dict[str, str]) -> None:
    """
    Send a rich embed notification to Discord via Webhook.
    
    Args:
        event (Dict[str, str]): Event data containing title, link, date, thumbnail.
    """
    if not DISCORD_WEBHOOK_URL:
        logger.warning("No Discord Webhook URL found. Skipping notification.")
        return

    embed = {
        "title": f"🎉 새로운 이벤트 알림: {event['title']}",
        "description": f"**기간**: {event['date']}\n[이벤트 보러가기]({event['link']})",
        "url": event['link'],
        "color": 0x58b9ff,  # FF14-ish Blue
        "image": {"url": event['thumbnail']},
        "footer": {"text": "FF14 Event Bot by Antigravity"}
    }
    
    payload = {"username": "FF14 Event Bot", "embeds": [embed]}

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        response.raise_for_status()
        logger.info(f"Notification sent: {event['title']}")
    except Exception as e:
        logger.error(f"Failed to send Discord webhook: {e}")


def send_summary_webhook(events: List[Dict[str, str]]) -> None:
    """
    Send a summary list of all currently active events.
    Triggered on startup if requested.
    """
    if not DISCORD_WEBHOOK_URL or not events:
        return

    # Format list for embed description
    description_lines = [
        f"• [{event['title']}]({event['link']}) ({event['date']})"
        for event in events
    ]
    description = "\n".join(description_lines)
    
    embed = {
        "title": "📋 현재 진행 중인 이벤트 목록",
        "description": description,
        "color": 0x34eb92,  # Green-ish for summary
        "footer": {"text": "FF14 Event Bot - Startup Summary"}
    }
    
    payload = {"username": "FF14 Event Bot", "embeds": [embed]}

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        response.raise_for_status()
        logger.info("Sent active event summary.")
    except Exception as e:
        logger.error(f"Failed to send summary webhook: {e}")


def fetch_events() -> List[Dict[str, str]]:
    """
    Crawl the target URL and parse event items.
    
    Returns:
        List[Dict[str, str]]: List of events containing id, title, link, date, thumbnail.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Network error fetching events: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    event_list = []
    
    # CSS Selector for FF14 KR Event Page
    # Captures <li> items inside the banner list with class 'event'
    items = soup.select(".banner_list.event li")
    
    if not items:
        logger.warning("No event items found. The site structure might have changed.")
        return []

    for item in items:
        try:
            # 1. Extract Link (Critical)
            a_tag = item.find("a")
            if not a_tag:
                continue
            
            raw_link = a_tag.get("href")
            # Normalize URL to absolute path
            full_link = raw_link if raw_link.startswith("http") else BASE_URL + raw_link

            # 2. Extract ID (Unique Identifier)
            # Remove query params to ensure stability (e.g. ?category=1)
            event_id = full_link.split('?')[0]

            # 3. Extract Metadata
            title_tag = item.find(class_="txt")
            title = title_tag.get_text(strip=True) if title_tag else "No Title"

            date_tag = item.find(class_="date")
            date = date_tag.get_text(strip=True) if date_tag else "Unknown Date"

            img_tag = item.find("img")
            thumbnail = ""
            if img_tag:
                src = img_tag.get("src")
                # Handle protocol-relative URLs (//image.ff14...)
                if src.startswith("//"):
                    thumbnail = "https:" + src
                elif src.startswith("/"):
                    thumbnail = BASE_URL + src
                else:
                    thumbnail = src

            event_list.append({
                "id": event_id,
                "title": title,
                "link": full_link,
                "date": date,
                "thumbnail": thumbnail
            })
        except Exception as e:
            logger.error(f"Error parsing item: {e}")
            continue
            
    # Note: The site usually returns newest first.
    return event_list


def crawling_job(is_startup: bool = False) -> None:
    """
    Main job loop logic.
    1. Fetch events.
    2. Check against local DB.
    3. Notify if new.
    
    Args:
        is_startup (bool): If True, enables summary notification logic.
    """
    logger.info("Checking for new events...")
    
    # Random delay to simulate human behavior and reduce server load pattern
    time.sleep(random.uniform(1, 3))
    
    events = fetch_events()
    if not events:
        logger.warning("No events fetched.")
        return

    latest_id = load_latest_event()

    # -- Startup Logic --
    # If explicitly requested via CLI flag, send summary of ALL active events
    if is_startup and events:
        logger.info("Startup Mode: Sending summary...")
        send_summary_webhook(events)
    
    # If first run (no DB), just save baseline to prevent spamming old events
    if latest_id is None:
        logger.info("No previous event data found. Saving baseline...")
        if events:
            # Save the top (newest) event as the latest known
            save_latest_event(events[0]['id'])
        return

    # -- Detection Logic --
    # Find events that are newer than latest_id
    # We iterate from the top; if we meet latest_id, we stop.
    new_events = []
    
    for event in events:
        if event['id'] == latest_id:
            break
        new_events.append(event)
    
    if new_events:
        logger.info(f"Found {len(new_events)} new event(s)!")
        
        # Send notifications from Oldest -> Newest order (for Discord readability)
        for event in reversed(new_events):
            send_discord_webhook(event)
            # Update DB immediately after sending to avoid duplicates if crash occurs
            save_latest_event(event['id']) 
            time.sleep(1) # Prevent rate-limiting


def main():
    """Application Entry Point"""
    # CLI Argument Parsing
    parser = argparse.ArgumentParser(description="FF14 KR Event Notification Bot")
    parser.add_argument(
        "--summary", 
        action="store_true", 
        help="Send a summary list of all active events on startup."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run the crawling job once and exit immediately (useful for Cron jobs)."
    )
    args = parser.parse_args()

    logger.info(f"Starting FF14 Event Bot (PID: {os.getpid()})...")
    if args.summary:
        logger.info("Option: Summary Mode Enabled")
    if args.once:
        logger.info("Option: Run-Once Mode Enabled")
    
    # 1. Immediate Execution on Start
    crawling_job(is_startup=args.summary)
    
    # If run-once is enabled, exit here
    if args.once:
        logger.info("Run-once completed. Exiting.")
        return
    
    # 2. Schedule Setup (Every 1 minute)
    schedule.every(1).minutes.do(crawling_job)
    logger.info("Scheduler started. Monitoring every 1 minute.")
    
    # 3. Main Loop
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            time.sleep(60) # Backoff on error

if __name__ == "__main__":
    main()
