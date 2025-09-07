import requests
import json
import os

def patch_original(application_id: str, token: str, content: str, ephemeral: bool = True) -> int:
    url = f"https://discord.com/api/v10/webhooks/{application_id}/{token}/messages/@original"
    payload = {"content": content}
    if ephemeral:
        payload["flags"] = 64
    resp = requests.patch(url, json=payload, timeout=10)
    return resp.status_code


def post_followup(application_id: str, token: str, content: str, ephemeral: bool = True) -> int:
    url = f"https://discord.com/api/v10/webhooks/{application_id}/{token}"
    payload = {"content": content}
    if ephemeral:
        payload["flags"] = 64
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.status_code
    except Exception as e:
        print(f"post_followup failed: {e}")
        import traceback
        print(traceback.format_exc())
        return 500

def send_followup_get_msg(application_id: str, token: str, content: str) -> dict:
    """Send followup message and return full response with message_id and channel_id."""
    url = f"https://discord.com/api/v10/webhooks/{application_id}/{token}?wait=true"
    r = requests.post(url, json={"content": content}, timeout=10)
    r.raise_for_status()
    return r.json()

def post_channel_message(bot_token: str, channel_id: str, content: str):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bot {bot_token}"}
    r = requests.post(url, headers=headers, json={"content": content}, timeout=10)
    r.raise_for_status()
    return r.json()

def create_thread_from_message(bot_token: str, channel_id: str, message_id: str, name: str = "Discussion", auto_archive: int = 1440) -> str:
    """Create a thread from a message using bot token."""
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}/threads"
    headers = {"Authorization": f"Bot {bot_token}"}
    r = requests.post(url, headers=headers, json={"name": name, "auto_archive_duration": auto_archive}, timeout=10)
    r.raise_for_status()
    return r.json()["id"] 

def bot_post_in_thread(bot_token: str, thread_id: str, content: str) -> str:
    url = f"https://discord.com/api/v10/channels/{thread_id}/messages"
    headers = {"Authorization": f"Bot {bot_token}"}
    r = requests.post(url, headers=headers, json={"content": content, "flags": 4}, timeout=10)
    r.raise_for_status()
    return r.json()["id"]

def post_followup_with_thread(application_id: str, token: str, content: str, ephemeral: bool = False, citations_list: list = None, username: str = None, channel_id: str = None, summary_title: str = None) -> int:
    try:
        bot_token = os.environ.get("BOT_TOKEN")
        if not bot_token:
            print("BOT_TOKEN not found, falling back to regular post")
            return post_followup(application_id, token, content[:1900], ephemeral)
        
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        
        if not paragraphs:
            return post_followup(application_id, token, content[:1900], ephemeral)
        
        first_paragraph = paragraphs[0]
        remaining_paragraphs = paragraphs[1:]
        
        if channel_id and bot_token:
            try:
                msg_data = post_channel_message(bot_token, channel_id, first_paragraph)
                message_id = msg_data.get("id")
            except Exception as e:
                print(f"Failed to post original message: {e}")
        else:
            print(f"Missing channel_id ({channel_id}) or bot_token ({bool(bot_token)}), using followup")
            msg_data = send_followup_get_msg(application_id, token, first_paragraph)
            message_id = msg_data.get("id")
            channel_id = msg_data.get("channel_id")
        
        if not message_id or not channel_id or not remaining_paragraphs:
            return 200

        from datetime import datetime
        
        if summary_title:
            thread_name = f"{summary_title} ({datetime.now().strftime('%m/%d')})"
        else:
            date_str = datetime.now().strftime("%m/%d")
            thread_name = f"{username}'s Summary ({date_str})"
        
        thread_id = create_thread_from_message(bot_token, channel_id, message_id, thread_name)
        
        thread_messages = []
        current_message = ""
        
        for paragraph in remaining_paragraphs:
            if paragraph.strip():
                test_message = current_message + ("\n\n" if current_message else "") + paragraph.strip()
                if len(test_message) <= 1900:
                    current_message = test_message
                else:
                    if current_message:
                        thread_messages.append(current_message)
                    current_message = paragraph.strip()
        
        if current_message:
            thread_messages.append(current_message)
        
        for message in thread_messages:
            bot_post_in_thread(bot_token, thread_id, message)
        
        if citations_list:
            from helpers.functions.process_citations import format_citations_for_thread
            citations_messages = format_citations_for_thread(citations_list)
            for citations_text in citations_messages:
                if citations_text:
                    print(f"Posting citations: {citations_text}")
                    bot_post_in_thread(bot_token, thread_id, citations_text)
        return 200
        
    except Exception as e:
        print(f"post_followup_with_thread failed: {e}")
        import traceback
        print(traceback.format_exc())