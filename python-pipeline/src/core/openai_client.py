from openai import AsyncOpenAI
from loguru import logger
from typing import Optional
from ..config.settings import settings
from ..config.prompts import CONTENT_WRITER_PROMPT

class OpenAIClient:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_content(self, user_input: str, context: Optional[str] = None) -> str:
        """Generate content using OpenAI API with the content writer prompt"""
        try:
            messages = [
                {"role": "system", "content": CONTENT_WRITER_PROMPT},
                {"role": "user", "content": user_input}
            ]

            if context:
                messages.insert(1, {"role": "system", "content": f"Context: {context}"})

            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                max_tokens=2000,
                temperature=0.7
            )

            content = response.choices[0].message.content
            logger.info(f"Generated content of length: {len(content)}")
            return content

        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise

    async def validate_input(self, user_input: str) -> bool:
        """Validate if the input is appropriate for content generation"""
        try:
            validation_prompt = """
            Analyze the following input and determine if it's appropriate for content writing.
            Respond with only 'YES' or 'NO'.

            Criteria:
            - Not spam or gibberish
            - Contains meaningful content request
            - Not harmful or inappropriate

            Input: {input}
            """.format(input=user_input)

            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": validation_prompt}],
                max_tokens=10,
                temperature=0
            )

            result = response.choices[0].message.content.strip().upper()
            return result == "YES"

        except Exception as e:
            logger.error(f"Error validating input: {e}")
            return False