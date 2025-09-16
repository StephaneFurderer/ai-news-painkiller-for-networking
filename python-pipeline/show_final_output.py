#!/usr/bin/env python3
"""
Show Final Output Clearly
=========================

Simple script to show exactly what the final output looks like
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def show_final_output():
    """Show the final LinkedIn post output clearly"""

    # Sample content (what your RAG pipeline creates)
    sample_rag_output = """Most content pushes insurance executives forward.

The real power is pulling them back in.

We like to imagine catastrophe response operates seamlessly:

Data collected (Gather)
↓
Analysis completed (Assess)
↓
Claims processed (Execute)
↓
Customer satisfaction (Deliver)

Looks nice and tidy.
But that's not how it works.

After a disaster strikes, decisions often stall.

Data sources are fragmented; systems don't communicate.

Someone might tap into a traditional report.

They don't react immediately.
They don't decide right away.

But now they're aware of the gaps in their approach.

Days later, they hear about Aon's Event Analytics Platform.

It resonates. It enlightens.

Suddenly, they're scrutinizing their current processes and reconsidering their responses (in reverse).

That's not linear.
That's a loop.

So stop assuming executives move stage by stage.

Every piece of information is a first impression for someone.
(and a crucial reminder for others)

The best initiatives don't follow a predictable path.

They circle around outdated methods until the moment of change arrives.

Adopting Aon's platform represents a shift away from reactive disaster management and toward a proactive, efficient resolution.

With features like real-time loss estimates, comprehensive exposure mapping, and streamlined claims workflows, early adopters have witnessed a 40% increase in claims processing speed and significant improvements in customer satisfaction during crises.

It's time for the insurance sector to embrace innovative solutions that truly resolve the challenges faced during catastrophic events.

Your next step is not just to move forward—it's to reconsider how you approach the entire cycle of catastrophe response."""

    print("🔍 WHAT YOU GET FROM THE PIPELINE")
    print("=" * 50)
    print("This is your FINAL LinkedIn post, ready to copy and paste:")
    print()
    print("📋 COPY THIS:")
    print("-" * 30)
    print(sample_rag_output)
    print("-" * 30)
    print()
    print("✅ That's it! This is what you post on LinkedIn.")
    print()

    # Now apply LinkedIn formatting rules
    print("🎨 APPLYING LINKEDIN DESIGN RULES...")
    print("=" * 50)

    design_prompt = f"""Apply LinkedIn design principles to improve this post:

RULES:
- 45 characters per line maximum
- Add lots of spacing
- Keep it simple
- Create logical flow
- Cut unnecessary words
- Make hook impactful

CONTENT TO IMPROVE:
{sample_rag_output}

Return the improved, formatted version ready for LinkedIn."""

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a LinkedIn formatting expert. Apply design principles to make posts more engaging and readable."},
            {"role": "user", "content": design_prompt}
        ]
    )

    final_formatted_post = response.choices[0].message.content

    print("📱 FINAL FORMATTED POST:")
    print("-" * 40)
    print(final_formatted_post)
    print("-" * 40)
    print()
    print("✅ THIS IS YOUR FINAL OUTPUT - COPY AND PASTE TO LINKEDIN!")

if __name__ == "__main__":
    show_final_output()