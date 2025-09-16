from typing import Dict, Any, Optional
from helpers.functions.llm_runner import run_llm_structured
from helpers.config.llm_schemas import ProfileNotesResponse, PROMPT_PROFILE_NOTES
from helpers.functions.discord_updates import patch_original
import traceback
import os
from pymongo import MongoClient
from datetime import datetime, timezone

def _get_mongo_collection() -> Any:
    uri = os.environ.get("MONGO_DB_URI")
    if not uri:
        raise RuntimeError("MONGO_DB_URI not set")
    client = MongoClient(uri)
    db_name = "Discord"
    db = client[db_name]
    return db["user_profiles"]

def send_profile_to_db(profile_data: Dict, application_id: Optional[str] = None, token: Optional[str] = None) -> None:
    try:
        notes: ProfileNotesResponse = run_llm_structured(
            prompt_template="The user's profile summary: {summary}",
            variables={"summary": profile_data.get('summary')},
            output_cls=ProfileNotesResponse,
            model='models/gemini-2.5-flash',
            provider='gemini',
            system_template=PROMPT_PROFILE_NOTES,
        )
        user_id = profile_data.get("user_id")
        doc = {
            "user_id": user_id,
            "username": profile_data.get("user_name"),
            "name": profile_data.get("global_name"),
            "user_interests": (profile_data.get("responses", {}) or {}).get("interests"),
            "user_keywords_input": (profile_data.get("responses", {}) or {}).get("keywords"),
            "user_connecting_keywords": (profile_data.get("responses", {}) or {}).get("connecting_keywords"),
            "user_summary_style": (profile_data.get("responses", {}) or {}).get("summary_style"),
            "personality": getattr(notes, "personality", None),
            "major_categories": getattr(notes, "major_categories", []) or [],
            "minor_categories": getattr(notes, "minor_categories", []) or [],
            "keywords": getattr(notes, "keywords", []) or [],
            "time_period": getattr(notes, "time_period", None),
            "concise_summaries": getattr(notes, "concise_summaries", False),
        }

        try:
            col = _get_mongo_collection()
            col.update_one(
                {"user_id": user_id},
                {
                    "$set": {**doc, "updated_at": datetime.now(timezone.utc)},
                    "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
                },
                upsert=True,
            )
            if application_id and token:
                patch_original(application_id, token, "**Profile setup complete.** Your personalized profile is ready. Try `/news` whenever you want.")
                
        except Exception as db_err:
            print("MongoDB error:", db_err)
            print(traceback.format_exc())
            if application_id and token:
                patch_original(application_id, token, "**Profile setup failed.** Please try again later.")
    except Exception as e:
        print("send_profile_to_db error:", e)
        print(traceback.format_exc())

