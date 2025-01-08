# app.py
import streamlit as st
import asyncio
from gpc_technical import check_gpc_compliance, score_technical_compliance
from gpc_policy import find_privacy_policy_url, get_policy_text, analyze_policy_text_llm
import os
from playwright.__main__ import main as playwright_main


# Check if Playwright browsers are installed
if not os.path.exists(os.path.expanduser("~/.cache/ms-playwright")):
    print("Installing Playwright browsers...")
    playwright_main(["install", "chromium"])  # Install Chromium browser
    
# Optionally, load environment variables from a .env file
from dotenv import load_dotenv
load_dotenv()

# Set OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Streamlit App Title
st.title("GPC Compliance Checker")

# User Input: Website URL
url = st.text_input("Enter the website URL to check for GPC compliance:", value="https://example.com")

# Button to trigger the compliance check
if st.button("Check Compliance"):
    if url:
        with st.spinner("Analyzing compliance..."):
            # Step 1: Find Privacy Policy URL
            policy_url = asyncio.run(find_privacy_policy_url(url))
            
            # Step 2: Get Policy Text and Analyze with LLM
            policy_text = asyncio.run(get_policy_text(policy_url))
            policy_score, policy_summary = asyncio.run(analyze_policy_text_llm(policy_text))
            
            # Step 3: GPC Technical Test
            technical_data = asyncio.run(check_gpc_compliance(url))
            tech_score, tech_summary = score_technical_compliance(technical_data)
            
            # Step 4: Combine Scores
            final_score = (policy_score + tech_score) / 2.0
            
            # Display Results
            st.header("GPC Compliance Report")
            st.markdown(f"**Website:** {url}")
            st.markdown(f"**Policy URL:** [Link]({policy_url})")
            st.markdown(f"**Policy Score:** {policy_score}")
            st.markdown(f"**Policy Summary:** {policy_summary}")
            st.markdown(f"**Technical Score:** {tech_score}")
            st.markdown(f"**Technical Summary:** {tech_summary}")
            st.markdown(f"**Final Score:** {final_score:.2f}")
            
            st.subheader("Technical Data:")
            st.json({
                "Cookies": technical_data.get("cookies"),
                "Requests (sample of 5)": technical_data.get("requests_made", [])[:5],
                "Error": technical_data.get("error")
            })
    else:
        st.warning("Please enter a valid website URL.")
