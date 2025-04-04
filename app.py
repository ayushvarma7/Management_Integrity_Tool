# app.py
import streamlit as st
import pdfplumber
from transformers import pipeline
import re
import pandas as pd
from typing import Dict, List, Tuple

# Initialize sentiment analysis pipeline
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# Helper functions (same as before)
def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_key_info(text: str) -> Dict:
    info = {}
    info["price_target"] = re.search(r"Price Target[:\s]*\$?(\d+\.?\d*)", text, re.IGNORECASE)
    info["recommendation"] = re.search(r"Recommendation[:\s]*(Buy|Sell|Hold)", text, re.IGNORECASE)
    info["revenue"] = re.search(r"Revenue[:\s]*\$?(\d+\.?\d*[BM]?)", text, re.IGNORECASE)
    info["net_income"] = re.search(r"Net Income[:\s]*\$?(\d+\.?\d*[BM]?)", text, re.IGNORECASE)
    info["eps"] = re.search(r"EPS[:\s]*\$?(\d+\.?\d*)", text, re.IGNORECASE)
    for key, match in info.items():
        if match:
            info[key] = match.group(1)
        else:
            info[key] = "Not Found"
    return info

def analyze_sentiment(text: str) -> Dict:
    sentiment = sentiment_analyzer(text[:512])
    return {"sentiment": sentiment[0]["label"], "confidence": sentiment[0]["score"]}

def extract_financial_summary(pdf_path: str) -> pd.DataFrame:
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                return pd.DataFrame(tables[0][1:], columns=tables[0][0])
    return pd.DataFrame()

def calculate_investment_score(info: Dict, sentiment: Dict, financials: pd.DataFrame) -> Tuple[float, str]:
    score = 0
    risk = "Moderate"
    if info["recommendation"] == "Buy":
        score += 30
    elif info["recommendation"] == "Hold":
        score += 15
    if sentiment["sentiment"] == "POSITIVE":
        score += 20
    if info["price_target"] != "Not Found" and float(info["price_target"]) > 0:
        score += 20
    if not financials.empty and "Revenue" in financials.columns:
        score += 20
    if sentiment["confidence"] < 0.7:
        risk = "High"
    elif info["recommendation"] == "Sell" or financials.empty:
        risk = "High"
    elif score > 70:
        risk = "Low"
    return min(score, 100), risk

def buffet_lynch_analysis(info: Dict, financials: pd.DataFrame) -> Dict:
    analysis = {"buffett": "Uncertain", "lynch": "Uncertain"}
    if (info["revenue"] != "Not Found" and float(re.sub(r'[BM]', '', info["revenue"])) > 1 and
        info["net_income"] != "Not Found" and float(re.sub(r'[BM]', '', info["net_income"])) > 0):
        analysis["buffett"] = "Likely"
    if info["eps"] != "Not Found" and float(info["eps"]) > 0:
        analysis["lynch"] = "Likely"
    return analysis

def assess_growth_and_risks(info: Dict, sentiment: Dict, financials: pd.DataFrame) -> Dict:
    growth = "Moderate"
    risks = []
    if sentiment["sentiment"] == "POSITIVE" and info["recommendation"] == "Buy":
        growth = "High"
    elif info["recommendation"] == "Sell":
        growth = "Low"
    if sentiment["confidence"] < 0.7:
        risks.append("Uncertain sentiment")
    if financials.empty:
        risks.append("Missing financial data")
    if info["price_target"] == "Not Found":
        risks.append("No price target provided")
    return {"growth_prospects": growth, "risks": risks}

def Ok(pdf_path: str) -> Dict:
    text = extract_text_from_pdf(pdf_path)
    info = extract_key_info(text)
    financials = extract_financial_summary(pdf_path)
    sentiment = analyze_sentiment(text)
    score, risk = calculate_investment_score(info, sentiment, financials)
    investment_styles = buffet_lynch_analysis(info, financials)
    growth_risks = assess_growth_and_risks(info, sentiment, financials)
    return {
        "key_info": info,
        "financial_summary": financials.to_dict() if not financials.empty else "Not Found",
        "sentiment": sentiment,
        "investment_score": score,
        "risk_level": risk,
        "buffett_likely": investment_styles["buffett"],
        "lynch_likely": investment_styles["lynch"],
        "growth_prospects": growth_risks["growth_prospects"],
        "risks": growth_risks["risks"]
    }

# Streamlit app
st.title("Research Report Analyzer")
st.write("Upload a research report PDF to get a detailed analysis.")

# File uploader
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    # Save the uploaded file temporarily
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Analyze the report
    with st.spinner("Analyzing the report..."):
        results = analyze_research_report("temp.pdf")
    
    # Display results
    st.subheader("Analysis Results")
    st.write("**Key Information:**", results["key_info"])
    st.write("**Financial Summary:**", results["financial_summary"])
    st.write("**Sentiment:**", results["sentiment"])
    st.write(f"**Investment Score:** {results['investment_score']}/100")
    st.write("**Risk Level:**", results["risk_level"])
    st.write("**Warren Buffett Likely?:**", results["buffett_likely"])
    st.write("**Peter Lynch Likely?:**", results["lynch_likely"])
    st.write("**Growth Prospects:**", results["growth_prospects"])
    st.write("**Risks:**", results["risks"])