from typing import Dict
from helpers.functions.openai_runner import run_openai_structured
from helpers.config.llm_schemas import AnalysisResponse, SummaryResponse, PROMPT_ANALYSIS_SYSTEM, PROMPT_THEME_SUMMARY_SYSTEM

def analyze_themes(formatted_data: str, profile: Dict, time_period: str) -> AnalysisResponse | None:
    """Analyze keyword data to identify relevant themes using medium reasoning."""
    try:
        system_variables = {
            "name": profile.get("name") or profile.get("username", ""),
            "personality": profile.get("personality", ""),
            "user_interests": profile.get("interests", ""),
            "time_period": time_period
        }
        
        system_prompt = PROMPT_ANALYSIS_SYSTEM.format(**system_variables)
        user_prompt = f"Analyze this keyword data and identify the most relevant themes: {formatted_data}"
        
        analysis_result: AnalysisResponse = run_openai_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_cls=AnalysisResponse,
            model="gpt-5",
            reasoning_effort="medium"
        )
        
        print(f"Analysis result: {len(analysis_result.themes)} themes identified")
        for theme in analysis_result.themes:
            print(f"Theme: {theme.title} (Score: {theme.relevance}/10)")
        return analysis_result
    except Exception as e:
        print(f"Theme analysis failed: {e}")
        return None

def generate_summary_from_analysis(analysis: AnalysisResponse, formatted_data: str, profile: Dict, time_period: str) -> SummaryResponse | None:
    """Generate summaries from theme analysis using high reasoning."""
    try:
        system_variables = {
            "name": profile.get("name") or profile.get("username", ""),
            "personality": profile.get("personality", ""),
            "user_interests": profile.get("interests", ""),
            "concise_summaries": profile.get("concise_summaries", False),
            "time_period": time_period
        }
        
        system_prompt = PROMPT_THEME_SUMMARY_SYSTEM.format(**system_variables)
        themes_text = "\n".join([
            f"Theme: {theme.title} (Relevance: {theme.relevance}/10)\n"
            f"Key points: {', '.join(theme.key_points)}\n"
            f"Keywords: {', '.join(theme.supporting_keywords)}\n"
            for theme in analysis.themes
        ])
        
        user_prompt = f"""Based on this theme analysis:
            {themes_text}

            Overall focus: {analysis.overall_focus}
            Priority reasoning: {analysis.user_priority_reasoning}

            And this full data: {formatted_data}

            Write comprehensive long_summary and concise_summary focusing on the identified themes. Keep citations intact [n:n] format. Return a title too."""
                        
        summary_result: SummaryResponse = run_openai_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_cls=SummaryResponse,
            model="gpt-5",
            reasoning_effort="medium"
        )
        
        return summary_result
    except Exception as e:
        print(f"Summary generation from analysis failed: {e}")
        return None
