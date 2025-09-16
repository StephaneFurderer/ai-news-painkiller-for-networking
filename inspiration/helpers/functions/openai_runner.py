from typing import Type
from pydantic import BaseModel
import json, os, traceback
from openai import OpenAI

def run_openai_structured(
    system_prompt: str,
    user_prompt: str,
    output_cls: Type[BaseModel],
    model: str = "gpt-5",
    retries: int = 2,
    reasoning_effort: str = "medium",
):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    last_error = None

    for attempt in range(retries + 1):
        try:
            print(f"OpenAI attempt {attempt + 1}/{retries + 1}")

            schema_dict = output_cls.model_json_schema()
            schema_str = json.dumps(schema_dict, indent=2)
            
            response = client.responses.create(
                model=model,
                instructions=(
                    system_prompt
                    + f"\n\nYou must respond with valid json that matches this exact schema:\n{schema_str}."
                ),
                input=f"{user_prompt}. Return a json object that matches the provided schema exactly. No prose.",
                text={"format": {"type": "json_object"}, "verbosity": "medium"},
                reasoning={"effort": reasoning_effort},
                tools=[],
                include=["reasoning.encrypted_content"],
            )

            content = getattr(response, "output_text", None)
            if not content:
                content = ""
                for item in getattr(response, "output", []) or []:
                    for block in getattr(item, "content", []) or []:
                        if getattr(block, "type", "") in ("output_text", "input_text"):
                            content = getattr(block, "text", "") or ""
                            if content:
                                break
                    if content:
                        break

            if not content:
                raise ValueError("No textual content returned by Responses API.")

            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                start, end = content.find("{"), content.rfind("}")
                if start == -1 or end == -1 or end <= start:
                    raise
                data = json.loads(content[start : end + 1])

            try:
                return output_cls(**data)
            except Exception as validation_error:
                print(f"Pydantic validation failed: {validation_error}")
                raise validation_error

        except Exception as e:
            last_error = e
            print(f"OpenAI attempt {attempt + 1} failed: {e}")
            if "validation" in str(e).lower():
                print(f"This appears to be a schema mismatch - check field names in Pydantic model")
            print(traceback.format_exc())
            continue

    print(f"All OpenAI attempts failed. Last error: {last_error}")
    return None
