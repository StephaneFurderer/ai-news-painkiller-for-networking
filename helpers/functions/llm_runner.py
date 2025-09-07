import os
import traceback
from typing import Type, Any
import json
from llama_index.llms.gemini import Gemini
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.llms.openai import OpenAI as OpenAILLM

def run_llm_structured(
    prompt_template: str,
    output_cls: Type[Any],
    variables: dict,
    model: str | None = None,
    provider: str = "gemini",
    retries: int = 2,
    system_template: str | None = None
):
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            if provider == "gemini":
                api_key = os.environ.get("GOOGLE_API_KEY")
                llm = Gemini(
                    api_key=api_key,
                    model=model or "models/gemini-2.5-flash",
                    temperature=0.2,
                    max_tokens=1024,
                )
            elif provider == "openai":
                api_key = os.environ.get("OPENAI_API_KEY")
                llm_kwargs = {
                    "api_key": api_key,
                    "model": model or "gpt-4o-mini",
                    'json_mode': True,
                    "temperature": 0.2,
                    "max_tokens": 1024,
                }
                llm = OpenAILLM(**llm_kwargs)
            else:
                raise ValueError(f"Unknown provider: {provider}")

            formatted_prompt = system_template + "\n\n" + prompt_template.format(**variables)

            print(f"LLM formatted prompt: {formatted_prompt}")
            program_kwargs = {
                "output_cls": output_cls,
                "prompt_template_str": formatted_prompt,
                "llm": llm,
            }
            
            program = LLMTextCompletionProgram.from_defaults(**program_kwargs)
            result = program()

            if isinstance(result, output_cls):
                return result
            if isinstance(result, dict):
                return output_cls(**result)
            if isinstance(result, str):
                try:
                    data = json.loads(result)
                except Exception:
                    start = result.find("{")
                    end = result.rfind("}")
                    if start != -1 and end != -1 and end > start:
                        data = json.loads(result[start : end + 1])
                    else:
                        raise ValueError("Model output is not valid JSON string")
                return output_cls(**data)

            raise TypeError(f"Unexpected program output type: {type(result)}")
        except Exception as e:
            last_error = e
            print(f"run_llm_structured attempt {attempt + 1} failed: {e}")
            print(traceback.format_exc())
            continue
    raise last_error if last_error else RuntimeError("Unknown error in run_llm_structured")


