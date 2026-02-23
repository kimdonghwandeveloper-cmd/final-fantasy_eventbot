import sys
import os
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Mocking things to avoid actual Discord spam
import final_fantasy_eventbot.main as bot

# Mock fetch_events to return a list of dummy events
dummy_events = [
    {"id": "http://test.com/1", "title": "Event 1", "date": "2026.01.01", "link": "http://test.com/1", "thumbnail": ""},
    {"id": "http://test.com/2", "title": "Event 2", "date": "2026.01.02", "link": "http://test.com/2", "thumbnail": ""},
    {"id": "http://test.com/3", "title": "Event 3", "date": "2026.01.03", "link": "http://test.com/3", "thumbnail": ""},
]

# Override the fetch_events function
bot.fetch_events = lambda: dummy_events
# Override send_discord_webhook to just print
bot.send_discord_webhook = lambda e: print(f"[MOCK SEND] {e['title']}")
# Override enrich to do nothing
bot.enrich_event_info = lambda e: e

def test_unknown_id_logic():
    print("--- Test: Unknown Latest ID ---")
    # Simulate a state where the latest ID is "old_event" which is NOT in the current list
    with open("latest_event.json", "w") as f:
        json.dump({"id": "http://test.com/old"}, f)
    
    # This should trigger "All events are new" logic
    # Because it iterates all dummy_events and never matches "http://test.com/old"
    bot.crawling_job()
    
    # Expected: Notifications for Event 3, 2, 1 (in reverse order of list? No, list is usually New->Old)
    # If dummy_events is [New, Old], then 1 is Newest?
    # Usually fetch_events returns [Newest, ..., Oldest]
    # So dummy_events[0] is Event 1. 
    # If Event 1 is newest, then code processes Event 3, then 2, then 1?
    
def test_persistence_failure():
    print("\n--- Test: Persistence Failure ---")
    # Reset DB
    with open("latest_event.json", "w") as f:
        json.dump({"id": "http://test.com/old"}, f)
        
    # Mock save to fail
    original_save = bot.save_latest_event
    bot.save_latest_event = lambda id: print(f"[MOCK SAVE FAIL] {id}") # Does not write to file
    
    # Run once
    print("Run 1:")
    bot.crawling_job()
    
    # Run twice - should send EVERYTHING AGAIN because file wasn't updated
    print("Run 2:")
    bot.crawling_job()
    
    # Restore
    bot.save_latest_event = original_save

if __name__ == "__main__":
    test_unknown_id_logic()
    test_persistence_failure()
