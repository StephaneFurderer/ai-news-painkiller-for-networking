
import os
import argparse
from pydantic import BaseModel
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Enhanced completion with output format (Pydantic)
class Limerick(BaseModel):
    style: str
    confidence: int  # between 0 and 100
    limerick: str

def main(**kwargs):
    PROMPT_USER = """
    You're a helpful writer. 
    You are writing in a style of {style} and you are {confidence}% confident in your answer.
    """

    PROMPT_SYSTEM = """
    # Role
    You're a helpful assistant. 
    
    # Goal
    You are writing a short story for 5-yo about the Python programming language.

    # Instructions
    - Write a short story for 5-yo about the Python programming language.
    - The story should be in a style given by the user.
    - You are confident in your answer given by the user.

    # Final thoughts
    - respond with a json object that matches the given schema
    """
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", 
            "content": PROMPT_SYSTEM
            },
            {"role": "user",
            "content": PROMPT_USER.format(**kwargs),
            },
        ],
        response_format=Limerick,
    )
    return completion.choices[0].message.parsed

if __name__ == "__main__":
    # pass paramters to the main let's say sandbox --style=funny --confidence=90
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--style", type=str, default="funny")
    parser.add_argument("--confidence", type=int, default=90)
    args = parser.parse_args()
    result = main(**args.__dict__)
    print(result)

    