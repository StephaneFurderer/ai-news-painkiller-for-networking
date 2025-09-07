from typing import Dict
import asyncio
from helpers.functions.send_profile_to_db import send_profile_to_db

async def handle_setup_command(data: Dict, user_id: str, user_name: str, global_name: str):
    about_you = ""
    for option in (data.get("data", {}) or {}).get("options", []) or []:
        if option.get("name") == "about_you":
            about_you = (option.get("value") or "").strip()

    prefill = about_you.replace("\n", " ").replace("|", "/").strip()[:80]

    return {
        "type": 4,
        "data": {
            "content": f" Set up your profile, {global_name or user_name}! This will help build news reports that are customized to you.\n\n",
            "flags": 64,
            "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "style": 1,
                            "label": "Open Setup Form",
                            "custom_id": f"open_setup_modal|{prefill}" if prefill else "open_setup_modal"
                        }
                    ]
                }
            ]
        }
    }

async def handle_setup_button_interaction(data: Dict):
    custom_id = (data.get("data", {}) or {}).get("custom_id")
    if not custom_id or not custom_id.startswith("open_setup_modal"):
        return None

    about_you = ""
    if "|" in custom_id:
        about_you = custom_id.split("|", 1)[1]
    
    return {
        "type": 9,  
        "data": {
            "custom_id": "setup_modal",
            "title": "Profile Setup",
            "components": [
                { 
                    "type": 1,
                    "components": [{
                        "type": 4,
                        "custom_id": "interests_input",
                        "label": "Your work and interests", 
                        "style": 2, 
                        "required": True,
                        "max_length": 500,
                        "placeholder": "e.g., tech, AI, startups",
                        "value": about_you  
                    }]
                },
                { 
                    "type": 1,
                    "components": [{
                        "type": 4,
                        "custom_id": "keywords_input",
                        "label": "Track keywords (comma-separated)", 
                        "style": 2,
                        "required": False,
                        "max_length": 500,
                        "placeholder": "AI, LLMs, Machine Learning, Google, OpenAI, Elon Musk, etc"
                    }]
                },
                { 
                    "type": 1,
                    "components": [{
                        "type": 4,
                        "custom_id": "connecting_keywords_input",
                        "label": "Use connecting keywords? (yes/no)", 
                        "style": 1,
                        "required": False,
                        "max_length": 10,
                        "placeholder": "yes"
                    }]
                },
                {  
                    "type": 1,
                    "components": [{
                        "type": 4,
                        "custom_id": "summary_style_input",
                        "label": "Summary style you prefer", 
                        "style": 2,
                        "required": False,
                        "max_length": 500,
                        "placeholder": "Concise bullets / exec summary"
                    }]
                },
                {  # 5
                    "type": 1,
                    "components": [{
                        "type": 4,
                        "custom_id": "time_period_input",
                        "label": "Time period (daily/weekly/monthly)",
                        "style": 1, 
                        "required": True,
                        "max_length": 20,
                        "placeholder": "daily"
                    }]
                }
            ]
        }
    }


async def handle_modal_submission(data: Dict):
    if data.get("data", {}).get("custom_id") != "setup_modal":
        return None

    user = (data.get("member") or {}).get("user") or {}
    user_id = user.get("id")
    user_name = user.get("username")
    global_name = user.get("global_name")
    if not user_id:
        return {"type": 4, "data": {"content": "Could not determine user id.", "flags": 64}}

    comps = data.get("data", {}).get("components", [])
    responses = {}
    for row in comps:
        for c in row.get("components", []):
            cid, val = c.get("custom_id"), c.get("value", "").strip()
            if cid == "interests_input": responses["interests"] = val
            elif cid == "keywords_input": responses["keywords"] = val
            elif cid == "summary_style_input": responses["summary_style"] = val
            elif cid == "time_period_input": responses["time_period"] = val.title()
            elif cid == "connecting_keywords_input": responses["connecting_keywords"] = val.title()

    summary = (
        f"• **Notes from user: ** {responses.get('interests','Not specified')}\n"
        f"• **Keywords they want to track: ** {responses.get('keywords','Not specified')}\n"
        f"• **Do they want to track connecting Keywords? ** {responses.get('connecting_keywords','Not specified')}\n"
        f"• **Summary Style: ** {responses.get('summary_style','Not specified')}\n"
        f"• **Time Period: ** {responses.get('time_period','Not specified')}\n"
    )

    profile_data = {
        "user_id": user_id,
        "user_name": user_name,
        "global_name": global_name,
        "responses": responses,
        "summary": summary,
    }

    response_payload = {"type": 4, "data": {"content": "** We're working on your profile...**", "flags": 64}}
    return response_payload, profile_data

