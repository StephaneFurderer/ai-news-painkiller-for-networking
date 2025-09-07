from typing import Dict, List

def add_profile_keywords(assembled: Dict, profile: Dict) -> None:
    """Add user's tracked keywords to the assembled data structure."""
    profile_keywords = profile.get("keywords", []) or []
    if not profile_keywords:
        return
    
    if "keywords" not in assembled:
        assembled["keywords"] = {}
    
    for keyword in profile_keywords:
        if keyword:
            if "profile" not in assembled["keywords"]:
                assembled["keywords"]["profile"] = []
            
            keyword_obj = {"keyword": keyword}
            assembled["keywords"]["profile"].append(keyword_obj)

def get_all_keyword_objects(assembled: Dict) -> List[Dict]:
    """Extract all keyword objects from the assembled data structure."""
    all_keyword_objects = []
    for category_type in assembled.values():
        if isinstance(category_type, dict):
            for category_data in category_type.values():
                if isinstance(category_data, list):
                    all_keyword_objects.extend(category_data)
                elif isinstance(category_data, dict):
                    for sort_data in category_data.values():
                        if isinstance(sort_data, list):
                            all_keyword_objects.extend(sort_data)
    return all_keyword_objects
