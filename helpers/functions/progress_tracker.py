import threading
import time
from helpers.functions.discord_updates import patch_original

def start_progress_tracker(application_id: str, token: str, total_keywords: int, facts_done_event):
    """Start background thread to send progress updates to Discord."""
    
    def progress_tracker():
        time.sleep(15) 
        if not facts_done_event.is_set():
            patch_original(application_id, token, f"We dig into all of these sources one by one, to drag out what's interesting.")
            patch_original(application_id, token, f"Each keyword can have hundreds of sources, so it may take a while.")
            time.sleep(30) 
            if not facts_done_event.is_set():
                patch_original(application_id, token, "You can check back here later.")
            time.sleep(30) 
            if not facts_done_event.is_set():
                patch_original(application_id, token, "We're almost there, remember go do something else.")
            time.sleep(30) 
            if not facts_done_event.is_set():
                patch_original(application_id, token, "Since you're first we are digging for the first time today.")
                patch_original(application_id, token, "The first run of the day is always slow for LLM concurrency limits.")
            time.sleep(15) 
            if not facts_done_event.is_set():
                patch_original(application_id, token, "You can check back here later.")
    
    tracker_thread = threading.Thread(target=progress_tracker)
    tracker_thread.daemon = True
    tracker_thread.start()
    return tracker_thread
