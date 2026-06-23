"""
generate_script.py
Turns a raw headline/summary into:
  - an ORIGINAL ~45-55 second narration script (own words, not copied from the source)
  - a title, description, tags, and hashtags for the upload

Keeping this step "in our own words" is what makes the video non-infringing —
we're reporting on a fact, not republishing anyone's article or footage.
"""
import json
import os

import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You write scripts for a daily YouTube Shorts news-recap channel.

Rules:
- Always rewrite the story in completely original wording. Never copy phrases from the source summary.
- Be factual and neutral. Do not invent details that aren't in the source material.
- Hook viewers in the first 5-7 words, then deliver the story, then a one-line "why it matters" close.
- The script is spoken aloud, so write for the ear: short sentences, no headers, no bullet points.
- Target 110-130 words (about 45-55 seconds at a natural reading pace).
- The title must be accurate to the content — compelling is good, misleading is not.
- Output ONLY valid JSON, no markdown fences, no commentary, matching this exact shape:
{
  "title": "string, <=95 characters, includes a hook, no clickbait that misrepresents the story",
  "script": "string, the spoken narration only",
  "description": "string, 2-4 sentences summarizing the story plus one line inviting people to follow for daily recaps",
  "tags": ["8-12 lowercase keyword tags relevant to this specific story"],
  "hashtags": ["5-8 hashtags, each starting with #, relevant to this story; always include #shorts"]
}
"""


def generate_script_package(topic: dict, trending_keywords: list[str] | None = None) -> dict:
    trending_keywords = trending_keywords or []

    user_prompt = f"""Source headline: {topic['title']}
Source summary: {topic.get('summary', '(no summary available, work from the headline only)')}

Currently-trending YouTube keywords you may draw from IF genuinely relevant (do not force-fit ones that don't fit this story): {", ".join(trending_keywords) if trending_keywords else "(none provided)"}

Write the JSON package now."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = "".join(block.text for block in response.content if block.type == "text").strip()

    # Strip stray markdown fences just in case the model adds them
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text
        raw_text = raw_text.rsplit("```", 1)[0]

    package = json.loads(raw_text)

    # Always guarantee #shorts is present regardless of what the model produced
    if not any(h.lower() == "#shorts" for h in package.get("hashtags", [])):
        package.setdefault("hashtags", []).append("#shorts")

    return package


if __name__ == "__main__":
    demo_topic = {"title": "Example headline for a dry run", "summary": "Example summary text."}
    print(json.dumps(generate_script_package(demo_topic), indent=2))
