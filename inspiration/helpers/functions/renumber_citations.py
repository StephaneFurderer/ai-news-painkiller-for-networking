from typing import Dict, List, Any
import re


def renumber_keywords_and_citations(assembled: Dict) -> Dict:
    keyword_counter = 1
    for category_type in assembled.values():
        if isinstance(category_type, dict):
            for category_data in category_type.values():
                if isinstance(category_data, list):
                    for keyword_obj in category_data:
                        if keyword_obj.get("keyword"):
                            _process_keyword_object(keyword_obj, keyword_counter)
                            keyword_counter += 1
                elif isinstance(category_data, dict):
                    for sort_data in category_data.values():
                        if isinstance(sort_data, list):
                            for keyword_obj in sort_data:
                                if keyword_obj.get("keyword"):
                                    _process_keyword_object(keyword_obj, keyword_counter)
                                    keyword_counter += 1
    return assembled


def _process_keyword_object(keyword_obj: Dict, keyword_num: int) -> None:
    keyword_obj["keyword_number"] = keyword_num
    
    citations = keyword_obj.get("citations", [])
    if not citations:
        return
    
    old_to_new_citation = {}
    for i, citation in enumerate(citations, 1):
        old_n = citation.get("n")
        if old_n:
            new_citation_num = f"{keyword_num}:{i}"
            old_to_new_citation[old_n] = new_citation_num
            citation["n"] = new_citation_num
    
    summary = keyword_obj.get("summary", "")
    if summary:
        updated_summary = _update_inline_citations(summary, old_to_new_citation)
        keyword_obj["summary"] = updated_summary
    
    interesting = keyword_obj.get("interesting", [])
    if interesting:
        updated_interesting = []
        for item in interesting:
            updated_item = _update_inline_citations(item, old_to_new_citation)
            updated_interesting.append(updated_item)
        keyword_obj["interesting"] = updated_interesting

def _update_inline_citations(text: str, citation_mapping: Dict[int, str]) -> str:
    def replace_citation(match):
        old_num = int(match.group(1))
        new_citation = citation_mapping.get(old_num)
        if new_citation:
            return f"[{new_citation}]"
        return match.group(0)
    
    updated_text = re.sub(r'\[(\d+)\]', replace_citation, text)
    return updated_text
