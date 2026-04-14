import os
import time
import json
import logging
import random
import re
import argparse
from typing import List, Optional, Dict, Any

import schedule
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from final_fantasy_eventbot.llm_middleware import MoogleSummarizer
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

# LLM 미들웨어 초기화
moogle_summarizer = MoogleSummarizer()

# --- Helper Functions ---

def load_latest_event() -> Optional[set]:
    """
    Load the known event ID set from the local JSON file.

    Returns:
        Optional[set]: Set of known event ID URLs, or None if file doesn't exist.
    """
    if not os.path.exists(LATEST_EVENT_FILE):
        return None
    try:
        with open(LATEST_EVENT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Backward compatibility: support old single-id format
            if "ids" in data:
                return set(data["ids"])
            if "id" in data:
                return {data["id"]}
            return None
    except Exception as e:
        logger.error(f"Failed to load latest event file: {e}")
        return None


def save_latest_event(event_ids: List[str]) -> None:
    """
    Save the current event ID list to the local JSON file to prevent duplicates.

    Args:
        event_ids (List[str]): All currently known event IDs.
    """
    try:
        with open(LATEST_EVENT_FILE, "w", encoding="utf-8") as f:
            json.dump({"ids": event_ids}, f, indent=4)
        logger.debug(f"Updated known event IDs ({len(event_ids)} total)")
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

    # 요약 정보가 존재하면 description에 추가
    summary_text = f"\n\n**[모그리의 요약 쿠뽀!]**\n{event.get('summary', '')}" if event.get('summary') else ""
    
    embed = {
        "title": f"🎉 새로운 이벤트 알림: {event['title']}",
        "description": f"**기간**: {event['date']}\n[이벤트 보러가기]({event['link']}){summary_text}",
        "url": event['link'],
        "color": 0x58b9ff,  # FF14-ish Blue
        "image": {"url": event.get('thumbnail', '')}
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
        # Force UTF-8 as valid FF14 pages are UTF-8, but sometimes headers miss it
        response.encoding = "utf-8"
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
            else:
                # Fallback: Check for background-image in .banner_img
                banner_img = item.find(class_="banner_img")
                if banner_img and banner_img.get("style"):
                    # Extract url('...') from style
                    style = banner_img.get("style")
                    # Simple parse: look for url('...') or url("...")
                    if "url('" in style:
                        src = style.split("url('")[1].split("')")[0]
                    elif 'url("' in style:
                        src = style.split('url("')[1].split('")')[0]
                    elif "url(" in style:
                         src = style.split("url(")[1].split(")")[0]
                    else:
                        src = ""
                else:
                    src = ""

            if src:
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


def enrich_event_info(event: Dict[str, str]) -> Dict[str, str]:
    """
    Visit the event detail page to extract more accurate date and title information.
    Best-effort approach: returns modified event or original if extraction fails.
    """
    try:
        logger.info(f"Enriching info for: {event['title']} ({event['link']})")
        resp = requests.get(event['link'], headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        # Force UTF-8 encoding as apparent_encoding might be wrong for some pages
        resp.encoding = "utf-8"
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 본문 텍스트 추출하여 LLM 요약을 위해 저장
        content_area = soup.select_one(".evt_view") or soup.select_one(".view_cont") or soup
        event['raw_text'] = content_area.get_text(separator="\n", strip=True)[:2500]

        
        # 1. Title Enrichment (OG Title or Title Tag)
        # Often the detail page has a full title (e.g. "Valentione's Day: ~Subtitle~")
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            new_title = og_title.get("content").strip()
            # If the new title is significantly longer or different, use it.
            # Simple heuristic: if it contains the original title, it's likely better.
            if len(new_title) > len(event['title']):
                logger.info(f"Updated title: {event['title']} -> {new_title}")
                event['title'] = new_title

        # 2. Image Enrichment (OG Image)
        # The detail page usually provides a high-res banner image via og:image
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            new_image = og_image.get("content").strip()
            # Ensure it's an absolute URL (though og:image usually is)
            if new_image.startswith("//"):
                new_image = "https:" + new_image
            elif new_image.startswith("/"):
                new_image = "https://www.ff14.co.kr" + new_image
            
            if new_image != event['thumbnail']:
                logger.info(f"Updated image: {event['thumbnail']} -> {new_image}")
                event['thumbnail'] = new_image

        # 3. Date Enrichment (Regex Search in Body)
        # Look for patterns like "2026.01.27 ~ 2026.02.09" or "26.01.27 ~ 02.09"
        # We search the entire text content for simplicity
        text_content = soup.get_text()
        
        # Regex Explanation:
        # \d{2,4}      : Year (26 or 2026)
        # [\.\-]       : Separator
        # \d{1,2}      : Month (1 or 01)
        # \d{1,2}      : Day
        # .*?          : Any char (space, day name like (화), time)
        # ~            : Range separator
        # This matches: "26.1.27(화) 17:00 ~ 2.9(월) 23:59"
        date_pattern = re.compile(r"(\d{2,4}[\.\-]\d{1,2}[\.\-]\d{1,2}).*?~.*?(\d{1,2}[\.\-]\d{1,2})")
        match = date_pattern.search(text_content)
        
        if match:
            # We found a range!
            # full match string might be very long if we use .*?, so let's try to capture the date part cleanly.
            # Actually, standardizing the date string is better.
            start_date = match.group(1)
            end_date = match.group(2) # This might just be "2.9" or "26.2.9"
            
            # The match itself (group(0)) will contain the full text "26.1.27(화) 17:00 ~ 2.9"
            # Let's clean it up for display.
            full_text = match.group(0).strip()
            # Truncate if it got too greedy (e.g. captured whole paragraph), though .*? is non-greedy.
            if len(full_text) < 50:
                 logger.info(f"Updated date: {event['date']} -> {full_text}")
                 event['date'] = full_text
            
    except Exception as e:
        logger.warning(f"Failed to enrich event info: {e}")
    
    return event


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

    known_ids = load_latest_event()

    # -- Startup Logic --
    # If explicitly requested via CLI flag, send summary of ALL active events
    if is_startup and events:
        logger.info("Startup Mode: Sending summary...")
        send_summary_webhook(events)

    # If first run (no DB), save all current events as baseline
    if known_ids is None:
        logger.info("No previous event data found. Saving baseline...")
        save_latest_event([e['id'] for e in events])
        return

    # -- Detection Logic --
    # New events = events whose ID is not in the known set
    new_events = [e for e in events if e['id'] not in known_ids]

    if new_events:
        # 도배 방지 안전장치: DB에 없는 밀린 이벤트들 중, 제일 예전 것부터 1분마다 1개씩 순차적으로 발송
        event_to_process = new_events[-1]
        logger.info(f"Found {len(new_events)} new event(s)! Processing exactly 1 to prevent spam (ID: {event_to_process['id']})")

        # Enchant event data with real date/title before sending
        enrich_event_info(event_to_process)
        
        # 본문이 성공적으로 추출되었다면 모그리 요약 파이프라인 통과
        if 'raw_text' in event_to_process:
            summary = moogle_summarizer.process_event_text(event_to_process['id'], event_to_process['raw_text'])
            if summary:
                event_to_process['summary'] = summary
            
        send_discord_webhook(event_to_process)

        # 발송을 완료한 1개의 이벤트만 DB(known_ids)에 저장
        # (나머지 미처리 이벤트는 다음 1분 루프 때 순차적으로 처리됨)
        if known_ids is None:
            known_ids = set()
        
        known_ids.add(event_to_process['id'])
        
        # 현재까지 처리 완료된 ID들만 저장
        save_latest_event(list(known_ids))

    else:
        # 더 이상 처리할 새로운 이벤트가 없을 때, 
        # 사이트에서 내려간 옛날 이벤트 ID를 known_ids에서 정리(메모리 누수 방지)
        current_event_ids = {e['id'] for e in events}
        # 교집합: 현재 사이트에 있는 이벤트 중 이미 처리된 것들만 남김
        cleaned_ids = known_ids.intersection(current_event_ids)
        save_latest_event(list(cleaned_ids))


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
