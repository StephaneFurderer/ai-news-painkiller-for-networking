from typing import Dict

def count_total_citations(assembled: Dict) -> int:
    total_count = 0
    for category_type in assembled.values():
        if isinstance(category_type, dict):
            for category_data in category_type.values():
                if isinstance(category_data, list):
                    for keyword_obj in category_data:
                        citations = keyword_obj.get("citations", [])
                        total_count += len(citations)
                elif isinstance(category_data, dict):
                    for sort_data in category_data.values():
                        if isinstance(sort_data, list):
                            for keyword_obj in sort_data:
                                citations = keyword_obj.get("citations", [])
                                total_count += len(citations)
    
    return total_count
