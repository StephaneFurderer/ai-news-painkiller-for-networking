import re
from typing import Dict, List, Tuple

def process_citations_in_summaries(concise_summary: str, long_summary: str, assembled_data: Dict) -> Tuple[str, str, List[Dict], List[Dict]]:
    cleaned_concise, concise_citations = process_single_summary(concise_summary, assembled_data)
    cleaned_long, long_citations = process_single_summary(long_summary, assembled_data)
    
    return cleaned_concise, cleaned_long, concise_citations, long_citations

def process_single_summary(summary: str, assembled_data: Dict) -> Tuple[str, List[Dict]]:
    citation_pattern = r'\[(\d+):(\d+)\]'
    
    groups = []
    matches = list(re.finditer(citation_pattern, summary))
    
    if not matches:
        return summary, []
    
    i = 0
    while i < len(matches):
        current_group = [matches[i].group(0)]
        while i + 1 < len(matches):
            current_end = matches[i].end()
            next_start = matches[i + 1].start()
            
            if next_start - current_end <= 1: 
                i += 1
                current_group.append(matches[i].group(0))
            else:
                break
        
        groups.append(current_group)
        i += 1
    
    unique_groups = []
    seen_groups = set()
    
    for group in groups:
        group_key = tuple(sorted(group)) 
        if group_key not in seen_groups:
            unique_groups.append(group)
            seen_groups.add(group_key)
    
    citations_list = []
    group_to_number = {}
    
    for i, group in enumerate(unique_groups, 1):
        group_urls = []
        
        for citation_ref in group:
            match = re.match(r'\[(\d+):(\d+)\]', citation_ref)
            if match:
                keyword_num = int(match.group(1))
                citation_num = int(match.group(2))
                keyword_obj = _find_keyword_by_number(assembled_data, keyword_num)
                if keyword_obj and "citations" in keyword_obj:
                    for citation in keyword_obj["citations"]:
                        if citation.get("n") == f"{keyword_num}:{citation_num}":
                            url = citation.get("url", "")
                            if url:
                                group_urls.append(url)
                            break
        
        deduplicated_urls = list(dict.fromkeys(group_urls))
        
        citations_list.append({
            "n": i,
            "urls": deduplicated_urls
        })
        
        group_key = tuple(sorted(group))
        group_to_number[group_key] = i
    
    cleaned_summary = summary
    
    for group in groups:
        group_key = tuple(sorted(group))
        new_number = group_to_number[group_key]
        
        group_text = ''.join(group)
        cleaned_summary = cleaned_summary.replace(group_text, f"[{new_number}]", 1)  
    
    return cleaned_summary, citations_list


def _find_keyword_by_number(assembled_data: Dict, keyword_num: int) -> Dict:
    for category_type in assembled_data.values():
        if isinstance(category_type, dict):
            for category_data in category_type.values():
                if isinstance(category_data, list):
                    for keyword_obj in category_data:
                        if keyword_obj.get("keyword_number") == keyword_num:
                            return keyword_obj
                elif isinstance(category_data, dict):
                    for sort_data in category_data.values():
                        if isinstance(sort_data, list):
                            for keyword_obj in sort_data:
                                if keyword_obj.get("keyword_number") == keyword_num:
                                    return keyword_obj
    return {}


def format_citations_for_thread(citations_list: List[Dict], max_citations_per_message: int = 4) -> List[str]:
    if not citations_list:
        return []
    
    messages = []
    current_lines = ["**Sources:**"]
    citations_in_current_message = 0
    
    for citation in citations_list:
        n = citation["n"]
        urls = citation["urls"]
        
        citation_lines = []
        if urls:
            formatted_urls = ", ".join([f"{url}" for url in urls])
            citation_lines.append(f"[{n}] {formatted_urls}")
        else:
            citation_lines.append(f"[{n}] (source not found)")
        
        if citations_in_current_message >= max_citations_per_message and len(current_lines) > 1:
            messages.append("\n".join(current_lines))
            current_lines = []
            citations_in_current_message = 0
        
        current_lines.extend(citation_lines)
        citations_in_current_message += 1
    
    if current_lines:
        messages.append("\n".join(current_lines))
    
    return messages
