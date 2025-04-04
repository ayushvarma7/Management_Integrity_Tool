# app.py
import streamlit as st
import pdfplumber
import re
from typing import Dict

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts raw text from a PDF file."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return ""
    return text

def extract_key_info(text: str) -> Dict:
    """Extracts key data using regex."""
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

def analyze_research_report(pdf_path: str) -> Dict:
    """Analyzes a research report PDF and returns key info."""
    text = extract_text_from_pdf(pdf_path)
    info = extract_key_info(text)
    return {"key_info": info}

# Streamlit app
st.title("Research Report Analyzer (Basic)")
st.write("Upload a research report PDF to extract key details.")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    try:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
    except Exception as e:
        st.error(f"Error saving PDF: {str(e)}")
    else:
        with st.spinner("Extracting details..."):
            results = analyze_research_report("temp.pdf")
        
        st.subheader("Extracted Details")
        st.write("**Key Information:**", results["key_info"])