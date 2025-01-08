import asyncio
import re
from playwright.async_api import async_playwright

async def check_gpc_compliance(url: str) -> dict:
    """
    Launches a headless browser with the Sec-GPC header set to '1',
    visits the URL, and analyzes cookies and network requests.
    
    Returns a dictionary with basic compliance data.
    """
    gpc_enabled_header = {"Sec-GPC": "1"}
    results = {
        "cookies": [],
        "requests_made": [],
        "tracking_detected": False,
        "error": None
    }

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(extra_http_headers=gpc_enabled_header)
            page = await context.new_page()

            # Collect requests
            network_requests = []
            page.on("request", lambda req: network_requests.append(req.url))

            # Go to the website
            await page.goto(url, timeout=30000)
            # Wait a bit for everything to load
            await page.wait_for_timeout(5000)

            # Check cookies
            cookies = await context.cookies()
            results["cookies"] = cookies

            # Simple check for known ad/tracking endpoints
            # (You can maintain a more robust blocklist or real-time detection.)
            known_ad_domains = ["doubleclick.net", "google-analytics.com", "facebook.com", "adservice"]
            tracking_found = any(
                any(domain in req_url for domain in known_ad_domains)
                for req_url in network_requests
            )

            results["requests_made"] = network_requests
            results["tracking_detected"] = tracking_found

            await browser.close()
    except Exception as e:
        results["error"] = str(e)

    return results


def score_technical_compliance(data: dict) -> (int, str):
    """
    Basic scoring logic:
      - 0 = GPC completely ignored (tracking found, no difference from normal).
      - 1 = Some partial blocking or unclear.
      - 2 = No tracking scripts found, GPC presumably respected.
    """
    if data["error"] is not None:
        return 0, f"Error occurred: {data['error']}"
    
    if data["tracking_detected"]:
        return 0, "Tracking scripts found. GPC not respected."
    else:
        return 2, "No known tracking scripts found. Potentially GPC-compliant."
