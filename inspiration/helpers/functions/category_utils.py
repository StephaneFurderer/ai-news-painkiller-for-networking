from typing import Dict, List
from helpers.config.llm_schemas import CATEGORY_MAP

def find_category_name(input_category: str) -> str:
    """Find the normalized category name from input string."""
    input_lower = input_category.lower().strip()
    if input_lower in CATEGORY_MAP:
        return input_lower
    for short_name, long_name in CATEGORY_MAP.items():
        if input_lower == long_name.lower():
            return short_name
    return None

def normalize_profile_categories(profile: Dict, time_period_override: str = None) -> tuple[List[str], List[str], str]:
    """Normalize profile categories and return major, minor categories and time period."""
    def normalize_list(raw: List[str]) -> List[str]:
        seen, out = set(), []
        for category in raw or []:
            category_name = find_category_name(category)
            if category_name and category_name not in seen:
                seen.add(category_name)
                out.append(category_name)
        return out

    major = normalize_list(profile.get("major_categories") or [])
    minor = normalize_list(profile.get("minor_categories") or [])
    
    major_set = set(major)
    minor = [cat for cat in minor if cat not in major_set]
    
    if time_period_override:
        period = time_period_override.lower()
    else:
        period = (profile.get("time_period") or "weekly").lower()
    
    return major, minor, period
