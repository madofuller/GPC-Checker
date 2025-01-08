import openai
import requests
from bs4 import BeautifulSoup
import os

openai.api_key = "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"

async def find_privacy_policy_url(base_url: str) -> str:
    """
    A naive approach: 
     1) check common endpoints (/privacy, /privacy-policy, /privacy_policy).
     2) if not found, fetch base page and look for 'privacy' link in the HTML.
    """
    common_paths = [
        "/privacy",
        "/privacy-policy",
        "/privacy_policy",
        "/legal/privacy-policy",
    ]
    
    # Try direct paths
    for path in common_paths:
        policy_url = base_url.rstrip("/") + path
        try:
            r = requests.get(policy_url, timeout=5)
            if r.status_code == 200 and len(r.text) > 100:
                return policy_url
        except:
            pass

    # Fallback: parse homepage for 'privacy' link
    try:
        r_home = requests.get(base_url, timeout=5)
        if r_home.status_code == 200:
            soup = BeautifulSoup(r_home.text, "html.parser")
            for link in soup.find_all("a", href=True):
                if "privacy" in link.get_text(strip=True).lower():
                    possible_url = link["href"]
                    # Attempt to resolve absolute URL
                    if possible_url.startswith("/"):
                        possible_url = base_url.rstrip("/") + possible_url
                    return possible_url
    except:
        pass

    # If all fails, return the base URL for analysis (not ideal)
    return base_url


async def get_policy_text(policy_url: str) -> str:
    """
    Fetches the policy page and returns the raw text (no HTML).
    """
    try:
        resp = requests.get(policy_url, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            return soup.get_text(separator=" ", strip=True)
    except:
        pass
    return ""


async def analyze_policy_text_llm(policy_text: str) -> (int, str):
    """
    Uses GPT to check if a website's privacy policy mentions or respects Global Privacy Control (GPC).
    Returns:
      - score: 0 or 2
      - summary: short text summarizing GPT's findings
    """
    if not policy_text or len(policy_text) < 30:
        # No/very short policy text => no insight
        return 0, "Policy text is empty or too short. No GPC mention detected."

    # Construct a prompt to ask GPT about GPC references
    system_message = {
        "role": "system",
        "content": (
            "You are a privacy compliance assistant. The user wants to know if this privacy policy text "
            "mentions or respects Global Privacy Control (GPC) or Do Not Sell clauses."
        )
    }

    user_message = {
        "role": "user",
        "content": (
            f"Here is the website's privacy policy:\n\n{policy_text}\n\n"
            "1. Does this policy mention or respect Global Privacy Control (GPC)?\n"
            "2. Does it reference any 'Do Not Sell' or user opt-out language?\n"
            "3. Provide a short summary of how the policy addresses (or does not address) these concepts."
        )
    }

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  
            messages=[system_message, user_message],
            temperature=0.3,
            max_tokens=400
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        return 0, f"OpenAI API error: {e}"

    # Simple scoring rule (you can refine this):
    # If GPT's answer contains phrases like 'mentions GPC' or 'do not sell', or explicitly states compliance.
    # We'll just check if the model says the policy "mentions" or "respects" GPC or Do Not Sell.
    lower_answer = answer.lower()
    if any(keyword in lower_answer for keyword in ["global privacy control", "gpc", "do not sell"]):
        return 2, f"GPT summary: {answer}"
    else:
        return 0, f"GPT summary: {answer}"
