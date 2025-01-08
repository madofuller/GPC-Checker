import asyncio

from gpc_technical import check_gpc_compliance, score_technical_compliance
from gpc_policy import (
    find_privacy_policy_url, 
    get_policy_text, 
    analyze_policy_text_llm  # Updated function
)

def evaluate_website_gpc(url: str) -> dict:
    """
    1. Find the site's Privacy Policy URL
    2. Fetch and analyze policy text for GPC references using GPT
    3. Run technical test with GPC enabled
    4. Score both policy and technical behavior
    5. Return final combined result
    """
    # Step 1: Attempt to find privacy policy URL
    policy_url = find_privacy_policy_url(url)

    # Step 2: Get policy text and do GPT-based analysis
    policy_text = get_policy_text(policy_url)
    policy_score, policy_summary = analyze_policy_text_llm(policy_text)

    # Step 3: GPC technical test
    data = asyncio.run(check_gpc_compliance(url))
    tech_score, tech_summary = score_technical_compliance(data)

    # Combine scores (example: average them)
    final_score = (policy_score + tech_score) / 2.0

    # Prepare a structured result
    result = {
        "website": url,
        "policy_url": policy_url,
        "policy_score": policy_score,
        "policy_summary": policy_summary,
        "tech_score": tech_score,
        "tech_summary": tech_summary,
        "final_score": final_score,
        "technical_data": data
    }
    return result

if __name__ == "__main__":
    test_url = "https://example.com"
    report = evaluate_website_gpc(test_url)

    print("==== GPC Compliance Report ====")
    print(f"Website: {report['website']}")
    print(f"Policy URL: {report['policy_url']}")
    print(f"Policy Score: {report['policy_score']}")
    print(f"Policy Summary: {report['policy_summary']}")
    print(f"Tech Score: {report['tech_score']}")
    print(f"Tech Summary: {report['tech_summary']}")
    print(f"Final Score: {report['final_score']:.2f}")
    print("\nTechnical Data:")
    print(f"  - Cookies: {report['technical_data']['cookies']}")
    print(f"  - Requests (sample of 5): {report['technical_data']['requests_made'][:5]}")
    if report['technical_data']['error']:
        print(f"  - Error: {report['technical_data']['error']}")
