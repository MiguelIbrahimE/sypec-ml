"""
Thin wrapper around the OpenAI client.
Keeps your creds in env vars.  Handles retries + rate limits.
"""
from __future__ import annotations
import os
import openai
from tenacity import retry, wait_fixed, stop_after_attempt  # pip install tenacity

openai.api_key = os.getenv("API_KEY")  # set via .env


@retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
def draft_recommendations(code_metrics: dict, energy_projection: dict) -> dict:
    """
    Calls the LLM once and returns:
    * bullets   – list[str] recommendations
    * score     – int 0-100
    """
    prompt = (
        "Given these metrics:\n"
        f"{code_metrics}\n\nEnergy projection:\n{energy_projection}\n\n"
        "Return JSON with keys bullets (≤6 bullet points) and score (0-100)."
    )
    completion = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a seasoned sustainability engineer."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    return completion.choices[0].message.json()
