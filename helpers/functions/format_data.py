from typing import Dict
from helpers.config.llm_schemas import CATEGORY_MAP

def format_assembled_data(assembled: Dict) -> str:
    assembled = _deduplicate_keywords(assembled)
    formatted_sections = []

    if "keywords" in assembled:
        category_data = assembled["keywords"]
        section_title = "KEYWORDS"
        formatted_sections.append(f"\n=== {section_title} ===")
        
        for category_name, category_content in category_data.items():
            category_display = CATEGORY_MAP.get(category_name, category_name).upper()
            formatted_sections.append(f"\n--- {category_display} ---")
            
            if isinstance(category_content, list):
                sorted_keywords = _sort_keywords_trending_first(category_content)
                for i, keyword_obj in enumerate(sorted_keywords, 1):
                    formatted_sections.append(_format_keyword_object(keyword_obj, i))
    
    for category_type, category_data in assembled.items():
        if category_type == "keywords": 
            continue
        if not isinstance(category_data, dict):
            continue
            
        section_title = category_type.upper()
        formatted_sections.append(f"\n=== {section_title} ===")
        
        for category_name, category_content in category_data.items():
            category_display = CATEGORY_MAP.get(category_name, category_name).upper()
            formatted_sections.append(f"\n--- {category_display} ---")
            
            if isinstance(category_content, list):
                sorted_keywords = _sort_keywords_trending_first(category_content)
                for i, keyword_obj in enumerate(sorted_keywords, 1):
                    formatted_sections.append(_format_keyword_object(keyword_obj, i))
            elif isinstance(category_content, dict):
                sort_order = ["trending", "top"]
                for sort_type in sort_order:
                    if sort_type in category_content:
                        keyword_list = category_content[sort_type]
                        if isinstance(keyword_list, list) and keyword_list:
                            sort_title = sort_type.upper()
                            formatted_sections.append(f"\n{sort_title}:")
                            sorted_keywords = _sort_keywords_trending_first(keyword_list)
                            for i, keyword_obj in enumerate(sorted_keywords, 1):
                                formatted_sections.append(_format_keyword_object(keyword_obj, i))
    
    return "\n".join(formatted_sections)

def _deduplicate_keywords(assembled: Dict) -> Dict:
    seen_keywords = set()
    
    priority_order = [
        ("major", "trending"), ("major", "top"), 
        ("minor", "trending"), 
        ("keywords", "profile")
    ]
    
    for category_type, sort_type in priority_order:
        if category_type in assembled:
            if category_type == "keywords":
                if sort_type in assembled[category_type]:
                    unique_keywords = []
                    for keyword_obj in assembled[category_type][sort_type]:
                        keyword = keyword_obj.get("keyword", "").lower()
                        if keyword and keyword not in seen_keywords:
                            seen_keywords.add(keyword)
                            unique_keywords.append(keyword_obj)
                    assembled[category_type][sort_type] = unique_keywords
            else:
                for category_name, category_data in assembled[category_type].items():
                    if sort_type in category_data:
                        unique_keywords = []
                        for keyword_obj in category_data[sort_type]:
                            keyword = keyword_obj.get("keyword", "").lower()
                            if keyword and keyword not in seen_keywords:
                                seen_keywords.add(keyword)
                                unique_keywords.append(keyword_obj)
                        assembled[category_type][category_name][sort_type] = unique_keywords
    
    return assembled

def _sort_keywords_trending_first(keyword_list):
    trending = [k for k in keyword_list if k.get("trending", False)]
    non_trending = [k for k in keyword_list if not k.get("trending", False)]
    return trending + non_trending

def _format_keyword_object(keyword_obj: Dict, index: int) -> str:
    keyword = keyword_obj.get("keyword", "")
    keyword_num = keyword_obj.get("keyword_number", "")
    summary = keyword_obj.get("summary", "")
    interesting = keyword_obj.get("interesting", [])
    
    header_parts = [f"{index}. {keyword}"]
    if keyword_num:
        header_parts.append(f"(#{keyword_num})")
    
    stats = []
    if keyword_obj.get("trending"):
        stats.append("🔥 TRENDING")
    if "count" in keyword_obj:
        stats.append(f"Count: {keyword_obj['count']}")
    if "change_in_count" in keyword_obj:
        change = keyword_obj["change_in_count"]
        if change > 0:
            stats.append(f"↗️ +{change}%")
        elif change < 0:
            stats.append(f"↘️ {change}%")
    if "engagement" in keyword_obj:
        stats.append(f"Engagement: {keyword_obj['engagement']}")
    if "change_in_engagement" in keyword_obj:
        change = keyword_obj["change_in_engagement"]
        if change > 0:
            stats.append(f"↗️ +{change}%")
        elif change < 0:
            stats.append(f"↘️ {change}%")
    if "sentiment" in keyword_obj and keyword_obj["sentiment"]:
        try:
            sentiment = keyword_obj["sentiment"]
            positive_count = sentiment.get("positive", {}).get("count", 0)
            negative_count = sentiment.get("negative", {}).get("count", 0)
            total_count = keyword_obj.get("count", 0)
            
            if total_count > 0:
                positive_pct = positive_count / total_count
                negative_pct = negative_count / total_count
                
                if positive_pct > 0.5:
                    stats.append("😊 Majority Positive")
                elif negative_pct > 0.5:
                    stats.append("😞 Majority Negative")
        except:
            pass
    
    if stats:
        header_parts.append(f"[{', '.join(stats)}]")
    parts = [f"\n{' '.join(header_parts)}"]
    if summary:
        parts.append(f"Summary: {summary}")
    if interesting:
        parts.append("Interesting points:")
        for point in interesting:
            parts.append(f"  • {point}")
    
    return "\n".join(parts)
