import streamlit as st
import fitz  # PyMuPDF
import re
import json
import os
import time
from pathlib import Path
from google import genai
from typing import Dict
import tempfile

# Page configuration
st.set_page_config(
    page_title="PDF to JSON Extractor",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'results' not in st.session_state:
    st.session_state.results = None

# Configuration
MAX_RETRIES = 3
RETRY_DELAY = 2

# API Key Manager for multiple keys
class APIKeyManager:
    """Manages multiple API keys with rotation"""
    def __init__(self):
        self.keys = []
        self.current_index = 0
        self.failed_keys = set()  # Track keys that hit rate limits
        self.key_stats = {}  # Track usage per key
    
    def add_keys(self, keys: list):
        """Add multiple API keys"""
        self.keys = [k.strip() for k in keys if k.strip()]
        self.current_index = 0
        self.failed_keys.clear()
        self.key_stats = {k: {"uses": 0, "failures": 0} for k in self.keys}
    
    def get_next_key(self):
        """Get next available API key (round-robin)"""
        if not self.keys:
            return None
        
        # Try to find a key that hasn't failed
        attempts = 0
        while attempts < len(self.keys):
            key = self.keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.keys)
            
            if key not in self.failed_keys:
                return key
            
            attempts += 1
        
        # If all keys failed, reset and try again
        if len(self.failed_keys) == len(self.keys):
            self.failed_keys.clear()
            return self.keys[0]
        
        return self.keys[0]
    
    def mark_failed(self, key: str, reason: str = ""):
        """Mark a key as failed (e.g., rate limit)"""
        if "429" in reason or "RESOURCE_EXHAUSTED" in reason or "quota" in reason.lower():
            self.failed_keys.add(key)
            if key in self.key_stats:
                self.key_stats[key]["failures"] += 1
            return True
        return False
    
    def mark_success(self, key: str):
        """Mark a key as successfully used"""
        if key in self.key_stats:
            self.key_stats[key]["uses"] += 1
    
    def get_stats(self):
        """Get statistics about key usage"""
        return self.key_stats

# Global API key manager
if 'api_key_manager' not in st.session_state:
    st.session_state.api_key_manager = APIKeyManager()

# Initialize Gemini Client
def get_gemini_client(api_key: str = None):
    """Get Gemini client with API key"""
    if api_key:
        return genai.Client(api_key=api_key)
    
    # Try to get from secrets
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except:
        pass
    
    # Try to get from environment
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY", "")
    
    return genai.Client(api_key=api_key) if api_key else None

# Extract clean text from PDF
def extract_clean_text(pdf_path: str) -> str:
    """Extract text from PDF with better structure preservation."""
    try:
        doc = fitz.open(pdf_path)
        text_lines = []
        
        # Method 1: Extract by blocks (preserves structure better)
        for page_num, page in enumerate(doc):
            blocks = page.get_text("blocks")
            for block in blocks:
                if len(block) >= 5:  # Valid text block
                    text = block[4].strip()
                    if text:
                        text_lines.append(text)
        
        # Method 2: Fallback to word-based extraction if blocks are poor
        if len(text_lines) < 10:  # If too few lines, use word-based
            text_lines = []
            for page in doc:
                words = page.get_text("words")
                words.sort(key=lambda w: (round(w[1], 1), w[0]))
                
                line = []
                last_y = None
                for x0, y0, x1, y1, word, *_ in words:
                    if last_y is None or abs(y0 - last_y) < 5:
                        line.append(word)
                    else:
                        if line:
                            text_lines.append(" ".join(line))
                        line = [word]
                    last_y = y0
                if line:
                    text_lines.append(" ".join(line))
        
        doc.close()
        
        # Clean and preserve structure
        clean_text = "\n".join(text_lines)
        clean_text = re.sub(r"[ \t]+", " ", clean_text)
        clean_text = re.sub(r"\n{3,}", "\n\n", clean_text)
        return clean_text.strip()
    
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return ""

# Create extraction prompt
def create_extraction_prompt(pdf_text: str, ic_name: str) -> str:
    """Create a detailed extraction prompt"""
    
    schema = {
        "BROKER_NAME": "",
        "CC": "",
        "CGST": "",
        "CHASIS_NUMBER": "",
        "CITY_NAME": "",
        "COVER": "",
        "CUSTOMER_EMAIL": "",
        "CUSTOMER_NAME": "",
        "CV_TYPE": "",
        "ENGINE_NUMBER": "",
        "FINANCIER_NAME": "",
        "FUEL_TYPE": "",
        "GST": "",
        "GVW": "",
        "IDV_SUM_INSURED": "",
        "IGST": "",
        "INSURANCE_COMPANY_NAME": "",
        "COMPLETE_LOCATION_ADDRESS": "",
        "MOB_NO": "",
        "NCB": "",
        "NET_PREMIUM": "",
        "NOMINEE_NAME": "",
        "NOMINEE_RELATIONSHIP": "",
        "OD_EXPIRE_DATE": "",
        "OD_PREMIUM": "",
        "PINCODE": "",
        "POLICY_ISSUE_DATE": "",
        "POLICY_NO": "",
        "PRODUCT_CODE": "",
        "REGISTRATION_DATE": "",
        "REGISTRATION_NUMBER": "",
        "RISK_END_DATE": "",
        "RISK_START_DATE": "",
        "SGST": "",
        "STATE_NAME": "",
        "TOTAL_PREMIUM": "",
        "TP_ONLY_PREMIUM": "",
        "VEHICLE_MAKE": "",
        "VEHICLE_MODEL": "",
        "VEHICLE_SUB_TYPE": "",
        "VEHICLE_VARIANT": "",
        "YEAR_OF_MANUFACTURE": ""
    }

    if ic_name.lower() == "reliance":
        extraction_rules = """
CRITICAL EXTRACTION RULES FOR RELIANCE GENERAL INSURANCE:

1. POLICY_NO: Look for "Policy Number" or "Policy No" - Extract the exact alphanumeric value
2. CUSTOMER_NAME: Find "Insured Name" - Extract the full name as written
3. REGISTRATION_NUMBER: Find "Registration No" - Extract the vehicle registration number
4. ENGINE_NUMBER: From "Engine No. / Chassis No." - Extract the engine number (usually first part)
5. CHASIS_NUMBER: From "Engine No. / Chassis No." - Extract the chassis number (usually second part)
6. VEHICLE_MAKE: From "Make / Model & Variant" - Extract the manufacturer
7. VEHICLE_MODEL: From "Make / Model & Variant" - Extract the model name
8. VEHICLE_VARIANT: From "Make / Model & Variant" - Extract the variant
9. YEAR_OF_MANUFACTURE: From "Mfg. Month & Year" - Extract in format MON-YYYY
10. CC: From "CC / HP / Watt" - Extract the cubic capacity number only
11. PRODUCT_CODE: From "Vehicle Type" - Must be exactly: "Two Wheeler", "Four Wheeler", or "Commercial Vehicle"
12. IDV_SUM_INSURED: From "Vehicle IDV" - Extract the amount with commas if present
13. POLICY_ISSUE_DATE: From "Tax Invoice No. & Date" - Extract the date part only
14. REGISTRATION_DATE: From "Tax Invoice No. & Date" or find registration date separately
15. RISK_START_DATE: From "Own Damage - Section-I Period" - Extract start date
16. RISK_END_DATE: From "Own Damage - Section-I Period" - Extract end date
17. OD_EXPIRE_DATE: Same as RISK_END_DATE
18. OD_PREMIUM: From "TOTAL OWN DAMAGE PREMIUM" - Extract amount
19. TP_ONLY_PREMIUM: From "TOTAL LIABILITY PREMIUM" - Extract amount
20. NET_PREMIUM: From "TOTAL PACKAGE PREMIUM (Sec I + II + III)" - Extract amount
21. TOTAL_PREMIUM: From "TOTAL PREMIUM PAYABLE" - Extract amount
22. CGST: From "CGST (9.00%)" - Extract amount
23. SGST: From "SGST (9.00%)" - Extract amount
24. IGST: From "IGST" - Extract amount if present
25. NCB: From "NCB" - Extract percentage or value
26. COMPLETE_LOCATION_ADDRESS: From "Communication Address & Place of Supply" - Extract full address
27. PINCODE: From address section - Extract 6-digit pincode
28. CITY_NAME: From "RTO Location" - Extract city name
29. STATE_NAME: From "RTO Location" - Extract state name
30. MOB_NO: From "Mobile No" - Extract 10-digit number (may be masked)
31. CUSTOMER_EMAIL: From "Email-ID" - Extract email address
32. NOMINEE_NAME: From "PA-Nominee Details Name Age Relation" - Extract name
33. NOMINEE_RELATIONSHIP: From "PA-Nominee Details Name Age Relation" - Extract relationship
34. INSURANCE_COMPANY_NAME: Should always be "Reliance General Insurance"
35. FINANCIER_NAME: From "Financier" if present, else empty string
36. COVER: From "Cover" if present, else empty string
37. FUEL_TYPE: Extract if mentioned (Petrol/Diesel/CNG/LPG/Electric)
38. CV_TYPE: Only for commercial vehicles from "Vehicle Sub Type"
39. GVW: Only for commercial vehicles from "GVW"
40. BROKER_NAME: Extract if present, else empty string
41. GST: Extract if mentioned separately

IMPORTANT:
- Extract EXACT values as they appear in the PDF
- For dates, preserve the format found
- For amounts, preserve commas and decimals
- If a field is not found, return empty string ""
- Do NOT add any text that is not in the PDF
"""
    else:  # Shriram
        extraction_rules = """
CRITICAL EXTRACTION RULES FOR SHRIRAM GENERAL INSURANCE:

1. POLICY_NO: Look for "Policy No." - Extract the exact alphanumeric value
2. CUSTOMER_NAME: Find "Insured's Code/ Name" - Extract the name part
3. REGISTRATION_NUMBER: Find "REGISTRATION MARK & PLACE" - Extract registration number
4. ENGINE_NUMBER: From "ENGINE NO. & CHASSIS NO." - Extract engine number (first part)
5. CHASIS_NUMBER: From "ENGINE NO. & CHASSIS NO." - Extract chassis number (second part)
6. VEHICLE_MAKE: From "MAKE - MODEL" - Extract manufacturer
7. VEHICLE_MODEL: From "MAKE - MODEL" - Extract model
8. VEHICLE_VARIANT: From "MAKE - MODEL" - Extract variant if present
9. YEAR_OF_MANUFACTURE: From "CUBIC CAPACITY / WATT/YEAR OF MANF." - Extract year
10. CC: From "CUBIC CAPACITY / WATT/YEAR OF MANF." - Extract CC value
11. PRODUCT_CODE: From "Vehicle Type" - Must be exactly: "Two Wheeler", "Four Wheeler", or "Commercial Vehicle"
12. IDV_SUM_INSURED: From "TOTAL VALUE" in IDV section - Extract total amount
13. POLICY_ISSUE_DATE: From "Period of Insurance" - Extract issue date
14. REGISTRATION_DATE: From "DATE OF REGN. / DELIVERY" - Extract date
15. RISK_START_DATE: From "Own Damage Policy Period" - Extract start date
16. RISK_END_DATE: From "Own Damage Policy Period" - Extract end date
17. OD_EXPIRE_DATE: Same as RISK_END_DATE
18. OD_PREMIUM: From "OD TOTAL" - Extract amount
19. TP_ONLY_PREMIUM: From "TP TOTAL" - Extract amount
20. NET_PREMIUM: From "Total" - Extract net premium amount
21. TOTAL_PREMIUM: From "PREMIUM AMOUNT" - Extract total premium
22. IGST: From "ADD : IGST 18.00%" - Extract amount
23. NCB: From "NCB Discount (%)" - Extract percentage
24. COMPLETE_LOCATION_ADDRESS: From "Insured Address and Contact Details" - Extract full address
25. PINCODE: From address section - Extract 6-digit pincode
26. CITY_NAME: From address section - Extract city
27. STATE_NAME: From address section - Extract state
28. MOB_NO: From "Insured Address and Contact Details" - Extract mobile number
29. CUSTOMER_EMAIL: From "Insured Address and Contact Details" - Extract email
30. NOMINEE_NAME: From "Nominee for Owner/Driver" - Extract name
31. NOMINEE_RELATIONSHIP: From "Nominee Relationship" - Extract relationship
32. INSURANCE_COMPANY_NAME: Should always be "SHRIRAM GENERAL INSURANCE COMPANY LIMITED"
33. FINANCIER_NAME: From "Financier" if present
34. COVER: From "Cover" if present
35. FUEL_TYPE: From "TYPE OF BODY / FUEL TYPE" - Extract fuel type
36. CV_TYPE: From "TYPE OF BODY / FUEL TYPE" for commercial vehicles
37. GVW: From "GVW" for commercial vehicles
38. BROKER_NAME: From "Agent Details" if present
39. CGST: Usually empty for Shriram (IGST used instead)
40. SGST: Usually empty for Shriram (IGST used instead)
41. GST: Extract if mentioned

IMPORTANT:
- Extract EXACT values as they appear in the PDF
- For dates, preserve the format found
- For amounts, preserve commas and decimals
- If a field is not found, return empty string ""
- Do NOT add any text that is not in the PDF
"""

    prompt = f"""You are an expert at extracting structured data from insurance policy documents.

{extraction_rules}

TASK:
Extract all fields from the PDF text below and return ONLY a valid JSON object with the exact structure shown.
Do NOT include any explanations, markdown formatting, or additional text - ONLY the JSON object.

REQUIRED OUTPUT FORMAT:
{json.dumps(schema, indent=2)}

PDF TEXT TO EXTRACT FROM:
{pdf_text}

Return ONLY the JSON object with all extracted fields. Ensure all string values are properly quoted and escaped.
"""
    
    return prompt

# Extract JSON with retry logic and multiple API keys
def extract_json_with_gemini(pdf_text: str, ic_name: str, client=None, use_key_manager=False) -> Dict:
    """Extract structured JSON using Gemini with retry logic and multiple API key support"""
    
    if not pdf_text or len(pdf_text.strip()) < 50:
        st.warning("PDF text is too short or empty")
        return {}
    
    prompt = create_extraction_prompt(pdf_text, ic_name)
    manager = st.session_state.api_key_manager if use_key_manager else None
    
    # Try with multiple keys if manager is available
    max_key_attempts = len(manager.keys) if manager and manager.keys else 1
    
    for key_attempt in range(max_key_attempts):
        # Get client (either provided or from key manager)
        if use_key_manager and manager:
            api_key = manager.get_next_key()
            if not api_key:
                st.error("No available API keys. All keys have hit rate limits.")
                return {}
            current_client = genai.Client(api_key=api_key)
            st.info(f"Using API key {key_attempt + 1}/{max_key_attempts}")
        elif client:
            current_client = client
            api_key = "single_key"
        else:
            st.error("Gemini API key not configured.")
            return {}
        
        # Try with retries
        for attempt in range(MAX_RETRIES):
            try:
                with st.spinner(f"Extracting data (key {key_attempt + 1}, attempt {attempt + 1}/{MAX_RETRIES})..."):
                    response = current_client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )
                
                text = response.text.strip()
                
                # Find JSON in response
                start = text.find("{")
                end = text.rfind("}") + 1
                
                if start == -1 or end == 0:
                    raise ValueError("No JSON object found in response")
                
                json_text = text[start:end]
                data = json.loads(json_text)
                
                # Validate and clean data
                data = validate_and_clean_data(data, ic_name)
                
                # Mark success
                if manager and api_key:
                    manager.mark_success(api_key)
                
                return data
                
            except json.JSONDecodeError as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    # JSON decode error - try next key
                    if use_key_manager and manager and key_attempt < max_key_attempts - 1:
                        st.warning(f"JSON decode error with current key, trying next key...")
                        break
                    else:
                        st.error(f"Failed to parse JSON after {MAX_RETRIES} attempts: {e}")
                        st.code(text[:500] if 'text' in locals() else "No response")
                        return {}
            
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a rate limit error
                if manager and api_key and manager.mark_failed(api_key, error_str):
                    st.warning(f"Rate limit hit on current key. Switching to next key...")
                    time.sleep(1)  # Brief delay before switching keys
                    break  # Try next key
                
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    # If we have more keys, try them
                    if use_key_manager and manager and key_attempt < max_key_attempts - 1:
                        st.warning(f"Error with current key: {error_str[:100]}. Trying next key...")
                        break
                    else:
                        st.error(f"Error after {MAX_RETRIES} attempts: {error_str}")
                        return {}
    
    # If we get here, all keys failed
    if use_key_manager and manager:
        st.error("All API keys have been exhausted. Please wait or add more keys.")
    
    return {}

# Validate and clean data
def validate_and_clean_data(data: Dict, ic_name: str) -> Dict:
    """Validate and clean extracted data"""
    
    required_fields = [
        "BROKER_NAME", "CC", "CGST", "CHASIS_NUMBER", "CITY_NAME", "COVER",
        "CUSTOMER_EMAIL", "CUSTOMER_NAME", "CV_TYPE", "ENGINE_NUMBER",
        "FINANCIER_NAME", "FUEL_TYPE", "GST", "GVW", "IDV_SUM_INSURED",
        "IGST", "INSURANCE_COMPANY_NAME", "COMPLETE_LOCATION_ADDRESS",
        "MOB_NO", "NCB", "NET_PREMIUM", "NOMINEE_NAME", "NOMINEE_RELATIONSHIP",
        "OD_EXPIRE_DATE", "OD_PREMIUM", "PINCODE", "POLICY_ISSUE_DATE",
        "POLICY_NO", "PRODUCT_CODE", "REGISTRATION_DATE", "REGISTRATION_NUMBER",
        "RISK_END_DATE", "RISK_START_DATE", "SGST", "STATE_NAME",
        "TOTAL_PREMIUM", "TP_ONLY_PREMIUM", "VEHICLE_MAKE", "VEHICLE_MODEL",
        "VEHICLE_SUB_TYPE", "VEHICLE_VARIANT", "YEAR_OF_MANUFACTURE"
    ]
    
    # Initialize missing fields
    for field in required_fields:
        if field not in data:
            data[field] = ""
    
    # Clean string values
    for key, value in data.items():
        if isinstance(value, str):
            data[key] = " ".join(value.split())
            if value.lower() in ["none", "null", "n/a", "na"]:
                data[key] = ""
    
    # Validate insurance company name
    if ic_name.lower() == "reliance":
        if "reliance" not in data.get("INSURANCE_COMPANY_NAME", "").lower():
            data["INSURANCE_COMPANY_NAME"] = "Reliance General Insurance"
    elif ic_name.lower() == "shriram":
        if "shriram" not in data.get("INSURANCE_COMPANY_NAME", "").lower():
            data["INSURANCE_COMPANY_NAME"] = "SHRIRAM GENERAL INSURANCE COMPANY LIMITED"
    
    return data

# Main UI
def main():
    st.title("📄 PDF to JSON Extractor")
    st.markdown("Upload an insurance policy PDF and extract structured data using AI")
    
    # Sidebar for API key configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Multiple API Keys input
        st.subheader("🔑 API Keys")
        st.markdown("**Enter multiple API keys (one per line) to avoid rate limits**")
        
        api_keys_text = st.text_area(
            "Gemini API Keys",
            height=150,
            help="Enter multiple API keys, one per line. The app will automatically rotate between them when rate limits are hit.",
            placeholder="Enter your API keys here, one per line:\nkey1_here\nkey2_here\nkey3_here"
        )
        
        # Single API Key (backward compatibility)
        api_key_input = st.text_input(
            "Or Single API Key (optional)",
            type="password",
            help="Alternative: Enter a single API key here"
        )
        
        # Process API keys
        if api_keys_text:
            keys_list = [k.strip() for k in api_keys_text.split('\n') if k.strip()]
            if keys_list:
                st.session_state.api_key_manager.add_keys(keys_list)
                st.success(f"✅ {len(keys_list)} API key(s) configured!")
                st.caption(f"Keys will rotate automatically when rate limits are hit")
        
        if api_key_input:
            os.environ["GEMINI_API_KEY"] = api_key_input
            st.session_state.api_key_manager.add_keys([api_key_input])
            st.success("Single API Key set!")
        
        # Show key statistics
        if st.session_state.api_key_manager.keys:
            with st.expander("📊 API Key Statistics", expanded=False):
                stats = st.session_state.api_key_manager.get_stats()
                for idx, (key, stat) in enumerate(stats.items(), 1):
                    key_display = f"Key {idx}: {key[:10]}...{key[-4:]}" if len(key) > 14 else f"Key {idx}"
                    status = "❌ Rate Limited" if key in st.session_state.api_key_manager.failed_keys else "✅ Active"
                    st.write(f"{key_display} - {status}")
                    st.caption(f"  Uses: {stat['uses']} | Failures: {stat['failures']}")
        
        st.markdown("---")
        st.markdown("### 📋 Instructions")
        st.markdown("""
        1. Enter multiple Gemini API keys (one per line) for best results
        2. Select insurance company type
        3. Upload a PDF file
        4. Click 'Extract Data'
        5. View and download results
        """)
        
        st.markdown("---")
        st.markdown("### 💡 Tips")
        st.markdown("""
        - **Multiple keys**: Add 2-5 free API keys to avoid rate limits
        - **Auto-rotation**: App automatically switches keys when limits hit
        - **Get free keys**: https://ai.google.dev/
        """)
        
        st.markdown("---")
        st.markdown("### ℹ️ Supported Companies")
        st.markdown("- Reliance General Insurance")
        st.markdown("- Shriram General Insurance")
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        ic_name = st.selectbox(
            "Select Insurance Company",
            ["reliance", "shriram"],
            help="Choose the insurance company that issued the policy"
        )
    
    with col2:
        uploaded_file = st.file_uploader(
            "Upload PDF File",
            type=["pdf"],
            help="Upload an insurance policy PDF file"
        )
    
    # Process button
    if st.button("🚀 Extract Data", type="primary", use_container_width=True):
        if not uploaded_file:
            st.error("Please upload a PDF file first")
            return
        
        # Check if we have API keys
        has_keys = (api_keys_text and len([k for k in api_keys_text.split('\n') if k.strip()]) > 0) or api_key_input or os.getenv("GEMINI_API_KEY")
        if not has_keys:
            st.error("Please enter at least one Gemini API key in the sidebar")
            return
        
        # Use key manager if multiple keys provided
        use_key_manager = bool(api_keys_text and len([k for k in api_keys_text.split('\n') if k.strip()]) > 1)
        
        st.session_state.processing = True
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name
        
        try:
            # Extract text
            with st.spinner("Extracting text from PDF..."):
                pdf_text = extract_clean_text(tmp_path)
            
            if not pdf_text:
                st.error("Failed to extract text from PDF. Please check if the file is valid.")
                return
            
            # Show extracted text preview
            with st.expander("📝 View Extracted Text (Preview)", expanded=False):
                st.text_area("PDF Text", pdf_text[:2000] + "..." if len(pdf_text) > 2000 else pdf_text, height=200)
            
            # Get Gemini client (for single key mode)
            client = None
            if not use_key_manager:
                client = get_gemini_client(api_key_input if api_key_input else None)
            
            # Extract structured data
            structured_data = extract_json_with_gemini(pdf_text, ic_name, client, use_key_manager=use_key_manager)
            
            if structured_data:
                st.session_state.results = structured_data
                st.success("✅ Data extracted successfully!")
            else:
                st.error("Failed to extract data. Please try again.")
        
        except Exception as e:
            st.error(f"An error occurred: {e}")
        
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            st.session_state.processing = False
    
    # Display results
    if st.session_state.results:
        st.markdown("---")
        st.header("📊 Extracted Data")
        
        # Key information cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Policy Number", st.session_state.results.get("POLICY_NO", "N/A"))
        
        with col2:
            st.metric("Customer Name", st.session_state.results.get("CUSTOMER_NAME", "N/A")[:30] + "..." if len(st.session_state.results.get("CUSTOMER_NAME", "")) > 30 else st.session_state.results.get("CUSTOMER_NAME", "N/A"))
        
        with col3:
            st.metric("Total Premium", st.session_state.results.get("TOTAL_PREMIUM", "N/A"))
        
        with col4:
            st.metric("Vehicle", f"{st.session_state.results.get('VEHICLE_MAKE', '')} {st.session_state.results.get('VEHICLE_MODEL', '')}")
        
        # Detailed results
        st.subheader("Complete Data")
        
        # Display as JSON
        st.json(st.session_state.results)
        
        # Download button
        json_str = json.dumps(st.session_state.results, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name=f"extracted_{st.session_state.results.get('POLICY_NO', 'data')}.json",
            mime="application/json",
            use_container_width=True
        )
        
        # Clear results button
        if st.button("🔄 Process Another File", use_container_width=True):
            st.session_state.results = None
            st.rerun()

if __name__ == "__main__":
    main()

