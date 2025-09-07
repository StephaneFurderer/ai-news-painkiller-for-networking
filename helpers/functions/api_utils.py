import requests
import re
import time
from typing import Dict, List

def fetch_keywords(period: str, api_category_name: str, sort: str) -> List[Dict]:
    """Fetch keywords from Safron API for a specific category and sort type."""
    try:
        url = "https://public.api.safron.io/v2/keywords"
        params = {"period": period, "category": api_category_name, "sort": sort, "slim": "false"}
        r = requests.get(url, params=params, timeout=45)
        r.raise_for_status()
        data = r.json() or {}
        keywords = []
        for item in data.get("keywords", []):
            if item.get("keyword"):
                keyword_data = {
                    "keyword": item.get("keyword"),
                    "trending": item.get("trending", False),
                    "count": item.get("count", 0),
                    "change_in_count": item.get("change_in_count", 0),
                    "engagement": item.get("engagement", 0),
                    "change_in_engagement": item.get("change_in_engagement", 0),
                    "sentiment": item.get("sentiment", {})
                }
                keywords.append(keyword_data)
        return keywords
    except Exception:
        import traceback
        print("Keyword fetch failed:", period, api_category_name, sort)
        print(traceback.format_exc())
        return []

def fetch_keyword_facts(keyword: str, period: str, max_retries: int = 3) -> Dict:
    """Fetch facts for a specific keyword from Safron AI facts API."""
    for attempt in range(max_retries):
        try:
            print(f"Fetching facts for: {keyword} (attempt {attempt + 1}/{max_retries})")
            url = "https://public.api.safron.io/v2/ai-keyword-facts"
            payload = {"keywords": keyword, "period": period}
            r = requests.post(url, json=payload, timeout=60)
            r.raise_for_status()
            data = r.json() or {}
            
            summary = data.get("summary", "")
            interesting = data.get("interesting", [])
            all_citations = data.get("citations", [])
            
            if not summary and not interesting:
                facts = data.get("facts", [])
                if facts:
                    if len(facts) >= 3:
                        summary = " ".join(facts[:3])  
                        interesting = facts[3:]       
                    elif len(facts) >= 1:
                        summary = " ".join(facts)    
                        interesting = []
            
            referenced_citations = set()
            
            for match in re.finditer(r'\[(\d+)\]', summary):
                referenced_citations.add(int(match.group(1)))
            
            for item in interesting:
                for match in re.finditer(r'\[(\d+)\]', item):
                    referenced_citations.add(int(match.group(1)))
            
            filtered_citations = [
                citation for citation in all_citations 
                if citation.get("n") in referenced_citations
            ]
            
            return {
                "summary": summary,
                "interesting": interesting,
                "citations": filtered_citations
            }
        except Exception as e:
            print(f"Keyword facts fetch failed: {keyword} (attempt {attempt + 1}/{max_retries}) - {e}")
            if attempt < max_retries - 1:
                print(f"Retrying {keyword} in 2 seconds...")
                time.sleep(2)
            else:
                import traceback
                print(traceback.format_exc())
    
    return {}
