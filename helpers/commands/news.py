import json
import threading
import time
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from helpers.functions.send_profile_to_db import _get_mongo_collection  
from helpers.functions.discord_updates import patch_original, post_followup_with_thread
from helpers.functions.renumber_citations import renumber_keywords_and_citations
from helpers.functions.format_data import format_assembled_data
from helpers.functions.category_utils import normalize_profile_categories
from helpers.functions.data_utils import add_profile_keywords, get_all_keyword_objects
from helpers.functions.api_utils import fetch_keywords, fetch_keyword_facts
from helpers.functions.process_citations import process_citations_in_summaries
from helpers.functions.count_citations import count_total_citations
from helpers.functions.llm_summary import analyze_themes, generate_summary_from_analysis
from helpers.functions.progress_tracker import start_progress_tracker
from helpers.config.llm_schemas import SummaryResponse

class NewsSteps:

    def __init__(self, user_id: str):
        self.user_id = user_id

    def fetch_user_profile(self) -> Dict:
        col = _get_mongo_collection()
        return col.find_one({"user_id": self.user_id}) or {}

    def fetching_keywords(self, profile: Dict, time_period_override: str = None) -> tuple[Dict, str]:
        major, minor, period = normalize_profile_categories(profile, time_period_override)
        assembled = self.assemble_keywords(major, minor, period, profile)
        add_profile_keywords(assembled, profile)
        
        return assembled, period
    
    def assemble_keywords(self, major: List[str], minor: List[str], period: str, profile: Dict) -> Dict:
        assembled: Dict[str, Dict] = {"major": {}, "minor": {}}
        api_calls = []
        for key in major:
            api_calls.append((key, "major", "top", period, key, "top"))
            api_calls.append((key, "major", "trending", period, key, "trending"))
        for key in minor:
            api_calls.append((key, "minor", "trending", period, key, "trending"))
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_call = {
                executor.submit(fetch_keywords, period, category, sort): (key, category_type, sort)
                for key, category_type, sort, period, category, sort in api_calls
            }
            for future in as_completed(future_to_call):
                key, category_type, sort = future_to_call[future]
                try:
                    keywords = future.result()
                    if category_type not in assembled:
                        assembled[category_type] = {}
                    if key not in assembled[category_type]:
                        assembled[category_type][key] = {}
                    if category_type == "major":
                        assembled[category_type][key][sort] = keywords[:3]
                    else:  
                        assembled[category_type][key][sort] = keywords[:2]
                except Exception as e:
                    print(f"API call failed for {key} {sort}: {e}")
        
        return assembled

    def fetch_facts(self, assembled: Dict, period: str) -> None:
        all_keyword_objects = get_all_keyword_objects(assembled)
        keywords_list = [obj.get("keyword") for obj in all_keyword_objects if obj.get("keyword")]
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_keyword = {
                executor.submit(fetch_keyword_facts, keyword_obj.get("keyword"), period): keyword_obj
                for keyword_obj in all_keyword_objects if keyword_obj.get("keyword")
            }
            
            for future in as_completed(future_to_keyword):
                keyword_obj = future_to_keyword[future]
                try:
                    facts_data = future.result()
                    if facts_data:
                        keyword_obj["summary"] = facts_data.get("summary", "")
                        keyword_obj["citations"] = facts_data.get("citations", [])
                        has_stats = any(key in keyword_obj for key in ["trending", "count", "change_in_count", "engagement"])
                        if not has_stats:
                            keyword_obj["interesting"] = facts_data.get("interesting", [])
                except Exception as e:
                    print(f"Facts fetch failed for {keyword_obj.get('keyword')}: {e}")
    
    
    def generate_summary(self, assembled: Dict, profile: Dict, time_period: str) -> SummaryResponse | None:
        try:
            formatted_data = format_assembled_data(assembled)
            analysis_result = analyze_themes(formatted_data, profile, time_period)
            if not analysis_result:
                return None

            summary_result = generate_summary_from_analysis(analysis_result, formatted_data, profile, time_period)
            return summary_result
            
        except Exception as e:
            print(f"LLM summary generation failed: {e}")
            return None
    
    
    def process_and_post_summary(self, summary_result: SummaryResponse, assembled: Dict, profile: Dict, application_id: str, token: str, channel_id: str = None) -> None:
        cleaned_concise, cleaned_long, concise_citations, long_citations = process_citations_in_summaries(
            summary_result.concise_summary, 
            summary_result.long_summary, 
            assembled
        )
        
        total_citations = count_total_citations(assembled)
        
        timestamp = int(time.time())
        username = profile.get("name") or profile.get("username", "User")
        cleaned_concise = cleaned_concise + f"\n\n**We processed {total_citations} comments and posts to generate this report.**" + "\n\n **Note that this summary is built from posts and comments gathered from the web. Always verify.**" 
        post_followup_with_thread(application_id, token, cleaned_concise, ephemeral=False, citations_list=concise_citations, username=username, channel_id=channel_id, summary_title=summary_result.title)
        
        print(f"Cleaned long summary:")
        print(cleaned_long)
        

def run_news_updates(application_id: str, token: str, user_id: str, time_period_override: str = None, channel_id: str = None) -> None:
    try:
        patch_original(application_id, token, "Checking your profile...")
        steps = NewsSteps(user_id=user_id)
        profile = steps.fetch_user_profile()
        if not profile:
            patch_original(application_id, token, "No profile found. Use /setup first.")
            return
        
        patch_original(application_id, token, "Scouting top & trending keywords...")
        assembled, period = steps.fetching_keywords(profile, time_period_override)
        
        all_keyword_objects = get_all_keyword_objects(assembled)
        total_keywords = len([obj for obj in all_keyword_objects if obj.get("keyword")])
        patch_original(application_id, token, f"Let's dig into what people are saying about {total_keywords} keywords we found for you..")
        
        facts_done = threading.Event()
        start_time = time.time()
        start_progress_tracker(application_id, token, total_keywords, facts_done)
        
        steps.fetch_facts(assembled, period)
        facts_done.set() 

        assembled = renumber_keywords_and_citations(assembled)
        patch_original(application_id, token, "Summarizing tons of data. Give us a minute or two. We'll ping you.")
        summary_result = steps.generate_summary(assembled, profile, period)
        
        elapsed_time = int(time.time() - start_time)
        
        if summary_result:
            steps.process_and_post_summary(summary_result, assembled, profile, application_id, token, channel_id)
        else:
            patch_original(application_id, token, f"The summary via the LLM provider failed. Please contact support.")

    except Exception as e:
        import traceback
        print("run_news_updates error:", e)
        print(traceback.format_exc())
