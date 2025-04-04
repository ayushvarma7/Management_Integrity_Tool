# app.py
import streamlit as st
import pdfplumber
import re
from typing import Dict, List

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
    """Extracts key data using regex tailored to the research report."""
    info = {}
    
    # Price Target
    info["price_target"] = re.search(r"Target[:\s]*INR(\d+)", text, re.IGNORECASE)
    
    # Recommendation
    info["recommendation"] = re.search(r"Rating[:\s]*(BUY|SELL|HOLD)", text, re.IGNORECASE)
    
    # Revenue (latest year, e.g., FY27E)
    revenue_match = re.search(r"Revenue \(INR cr\)\s*[\d\s-]+\s(\d+)", text, re.IGNORECASE)
    info["revenue"] = revenue_match if revenue_match else None
    
    # Net Income (latest year, e.g., FY27E)
    net_income_match = re.search(r"Net profit \(INR cr\)\s*-?[\d\s-]+\s(-?\d+)", text, re.IGNORECASE)
    info["net_income"] = net_income_match if net_income_match else None
    
    # EPS (if present, fallback)
    info["eps"] = re.search(r"Earnings Per Share[:\s]*INR?(\d+\.?\d*)", text, re.IGNORECASE)
    
    # Clean up extracted values
    for key, match in info.items():
        if match:
            info[key] = match.group(1)
        else:
            info[key] = "Not Found"
    
    return info

def extract_pros_and_cons(text: str) -> Dict:
    """Extracts pros and cons based on keywords and context."""
    pros = []
    cons = []
    
    # Pros (positive indicators)
    if re.search(r"strong growth|healthy store economics|valuation re-rating|aggressive growth", text, re.IGNORECASE):
        pros.append("Strong growth potential and healthy store economics")
    if re.search(r"internal accruals", text, re.IGNORECASE):
        pros.append("Self-funded expansion through internal accruals")
    if re.search(r"BUY", text, re.IGNORECASE):
        pros.append("Positive analyst recommendation (BUY)")
    
    # Cons (risks or negatives)
    if re.search(r"intense competition", text, re.IGNORECASE):
        cons.append("Intense competition in the value retail space")
    if re.search(r"store closure", text, re.IGNORECASE):
        cons.append("Risk of store closures (historical rate <2%)")
    if "Not Found" in extract_key_info(text).values():
        cons.append("Incomplete financial data in report")
    
    return {"pros": pros if pros else ["No specific pros identified"], "cons": cons if cons else ["No specific cons identified"]}

def extract_valuations(text: str) -> Dict:
    """Extracts valuation metrics from the report."""
    valuations = {}
    
    # EV/EBITDA
    ev_ebitda = re.search(r"EV/EBITDA\s*\(x\)\s*[\d\.\s-]+\s(\d+\.\d+)", text, re.IGNORECASE)
    valuations["ev_ebitda"] = ev_ebitda.group(1) if ev_ebitda else "Not Found"
    
    # P/E Ratio (latest year)
    pe_ratio = re.search(r"P/E ratio\s*\(x\)\s*[\d\.\s-]+\s(\d+\.\d+)", text, re.IGNORECASE)
    valuations["pe_ratio"] = pe_ratio.group(1) if pe_ratio else "Not Found"
    
    # RoCE (latest year)
    roce = re.search(r"RoACE\s*\(%\)\s*[\d\.\s-]+\s(\d+\.\d+)", text, re.IGNORECASE)
    valuations["roce"] = roce.group(1) if roce else "Not Found"
    
    return valuations

def analyze_research_report(pdf_path: str) -> Dict:
    """Analyzes a research report PDF and returns key info, pros/cons, and valuations."""
    text = extract_text_from_pdf(pdf_path)
    info = extract_key_info(text)
    pros_cons = extract_pros_and_cons(text)
    valuations = extract_valuations(text)
    return {
        "key_info": info,
        "pros_cons": pros_cons,
        "valuations": valuations,
        "raw_text": text  # For debugging
    }

# Streamlit app
st.title("Research Report Analyzer (Basic)")
st.write("Upload a research report PDF to extract key details, pros/cons, and valuations.")

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
        st.subheader("Pros and Cons")
        st.write("**Pros:**", results["pros_cons"]["pros"])
        st.write("**Cons:**", results["pros_cons"]["cons"])
        st.subheader("Valuations")
        st.write("**Valuation Metrics:**", results["valuations"])
        st.subheader("Raw Extracted Text (for debugging)")
        st.text_area("Raw Text", results["raw_text"], height=200)