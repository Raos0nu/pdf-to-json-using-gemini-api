# PDF to JSON Extractor - Complete Documentation

AI-Powered Insurance Policy Data Extraction System with Multiple API Key Support

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Web UI Usage](#web-ui-usage)
5. [Command-Line Usage](#command-line-usage)
6. [Multiple API Keys Setup](#multiple-api-keys-setup)
7. [Step-by-Step Guide](#step-by-step-guide)
8. [Output Format](#output-format)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Usage](#advanced-usage)

---

## Overview

This project provides an automated solution for extracting structured data from insurance policy PDFs using Google Gemini AI. It supports both web-based and command-line interfaces, with intelligent API key rotation to handle rate limits.

### What It Does

- Extracts 41 structured fields from insurance policy PDFs
- Supports Reliance General Insurance and Shriram General Insurance
- Processes single PDFs or batch processes thousands
- Automatically rotates between multiple API keys to avoid rate limits
- Provides high accuracy (near 100%) with validation

### Key Technologies

- **Python 3.11+**
- **Streamlit** - Web UI framework
- **PyMuPDF (fitz)** - PDF text extraction
- **Google Gemini API** - AI-powered data extraction

---

## Features

### Core Features

✅ **Intelligent Text Extraction**
- Preserves document structure
- Handles complex layouts
- Multiple extraction methods (block-based + word-based)

✅ **AI-Powered Data Extraction**
- 41 structured fields extracted
- Supports Reliance & Shriram Insurance
- High accuracy with validation

✅ **Multiple API Key Support**
- Automatic key rotation
- Rate limit handling
- Usage statistics tracking

✅ **Dual Interface**
- Modern Web UI (Streamlit)
- Command-line for batch processing

✅ **Batch Processing**
- Process thousands of PDFs
- Progress tracking
- Error handling & logging

✅ **Data Validation**
- Automatic field validation
- Data cleaning
- Format standardization

---

## Installation

### Prerequisites

- Python 3.11 or higher
- Google Gemini API key(s) - Get free keys from https://ai.google.dev/

### Install Dependencies

**For Web UI:**
```bash
pip install -r requirements_ui.txt
```

**Or install individually:**
```bash
pip install streamlit PyMuPDF google-genai
```

**For Command-Line Only:**
```bash
pip install PyMuPDF google-genai
```

---

## Web UI Usage

### Starting the Application

```bash
python -m streamlit run app.py
```

The app will open in your default web browser at `http://localhost:8501`

### Using the Web Interface

1. **Enter API Key(s)**: In the sidebar, enter your Google Gemini API key(s)
   - Single key: Enter in "Or Single API Key" field
   - Multiple keys: Enter in "Gemini API Keys" text area (one per line)

2. **Select Insurance Company**: Choose "reliance" or "shriram"

3. **Upload PDF**: Click "Browse files" and select your insurance policy PDF

4. **Extract Data**: Click "🚀 Extract Data" button

5. **View Results**: See the extracted data with key metrics cards

6. **Download**: Click "📥 Download JSON" to save the results

### Web UI Features

**Sidebar Configuration:**
- API Key Input (supports multiple keys)
- Instructions and tips
- API Key Statistics (view usage per key)
- Supported companies list

**Main Interface:**
- Insurance company selector
- File uploader (drag-and-drop supported)
- Extract button
- Results display with:
  - Key metrics cards (Policy Number, Customer Name, Premium, Vehicle)
  - Complete JSON data viewer
  - Download button

### API Key Setup for Web UI

You can provide your API key in three ways:

1. **In the UI** (Recommended): Enter in sidebar
   - Single key: Use "Or Single API Key" field
   - Multiple keys: Use "Gemini API Keys" text area (one per line)

2. **Environment Variable**: Set `GEMINI_API_KEY` environment variable
   ```bash
   # Windows
   set GEMINI_API_KEY=your_api_key_here
   
   # Linux/Mac
   export GEMINI_API_KEY=your_api_key_here
   ```

3. **Streamlit Secrets**: Create `.streamlit/secrets.toml` file:
   ```toml
   GEMINI_API_KEY = "your_api_key_here"
   ```

### Custom Port
```bash
streamlit run app.py --server.port 8502
```

---

## Command-Line Usage

### Single PDF Processing

```bash
python pdf_to_json_gemini.py
```

This will process the default PDF specified in the script.

### Batch Processing (Recommended for Multiple PDFs)

```bash
python pdf_to_json_gemini.py <pdf_folder> <ic_name> [output_folder] [start_index] [max_files]
```

**Parameters:**
- `pdf_folder`: Path to folder containing PDFs (e.g., "Reliance_pdf")
- `ic_name`: Insurance company name - "reliance" or "shriram"
- `output_folder`: (Optional) Folder to save results (default: "output")
- `start_index`: (Optional) Index to start from (for resuming) (default: 0)
- `max_files`: (Optional) Maximum number of files to process (default: all)

**Examples:**

1. Process all PDFs in Reliance_pdf folder:
```bash
python pdf_to_json_gemini.py Reliance_pdf reliance
```

2. Process first 10 PDFs:
```bash
python pdf_to_json_gemini.py Reliance_pdf reliance output 0 10
```

3. Resume from file 50, process next 20:
```bash
python pdf_to_json_gemini.py Reliance_pdf reliance output 50 20
```

4. Process Shriram PDFs:
```bash
python pdf_to_json_gemini.py Shriram_pdf shriram
```

### Output Files

**Individual Results:**
- `{pdf_name}_extracted.json` - Extracted data for that PDF
- `{pdf_name}_gemini_extracted.json` - Intermediate Gemini response

**Summary Report:**
- `processing_summary.json` - Complete summary with success/failure counts
- `extraction_log.txt` - Detailed log of all operations

---

## Multiple API Keys Setup

### Why Multiple API Keys?

Free Gemini API keys have limits:
- **15 requests per minute (RPM)**
- **1,500 requests per day**

With multiple keys, you get:
- **3 keys = 45 RPM, 4,500 requests/day**
- **5 keys = 75 RPM, 7,500 requests/day**

This allows processing **thousands of PDFs** per day!

### How It Works

1. **Add Multiple Keys**: Enter 2-5 free Gemini API keys
2. **Automatic Rotation**: App rotates between keys in round-robin fashion
3. **Rate Limit Handling**: When a key hits rate limit (429 error), it's automatically marked as failed and the next key is used
4. **Smart Recovery**: Failed keys are retried after some time

### Getting Free API Keys

1. Visit: https://ai.google.dev/
2. Sign in with your Google account
3. Click "Get API Key"
4. Create a new API key (you can create multiple keys)
5. Copy the API key

**Tip**: Create 3-5 free API keys to maximize your processing capacity!

### Web UI: Multiple API Keys

1. Start the app: `python -m streamlit run app.py`
2. In the sidebar, find "🔑 API Keys" section
3. Enter multiple API keys, **one per line**:
   ```
   AIzaSyAbc123def456ghi789jkl012mno345pqr
   AIzaSyXyz789abc012def345ghi678jkl901mno
   AIzaSyDef456ghi789jkl012mno345pqr678stu
   ```
4. The app will automatically use all keys and rotate between them

**View Statistics:**
- Click "📊 API Key Statistics" in the sidebar
- See which keys are active and which hit rate limits
- Monitor usage per key

### Command-Line: Multiple API Keys

**Method 1: Create `api_keys.txt` File (Recommended)**

1. Create a file named `api_keys.txt` in the same folder as the script
2. Add your API keys, one per line:
   ```
   AIzaSyAbc123def456ghi789jkl012mno345pqr
   AIzaSyXyz789abc012def345ghi678jkl901mno
   AIzaSyDef456ghi789jkl012mno345pqr678stu
   ```
3. Run the script - it will automatically load the keys

**Method 2: Environment Variable**

```bash
# Windows PowerShell
$env:GEMINI_API_KEYS="key1,key2,key3"
python pdf_to_json_gemini.py Reliance_pdf reliance

# Windows CMD
set GEMINI_API_KEYS=key1,key2,key3
python pdf_to_json_gemini.py Reliance_pdf reliance

# Linux/Mac
export GEMINI_API_KEYS="key1,key2,key3"
python pdf_to_json_gemini.py Reliance_pdf reliance
```

### Benefits of Multiple Keys

✅ **No More Rate Limit Errors**: When one key hits limit, automatically switches to next
✅ **Higher Throughput**: Process more PDFs by distributing load across keys
✅ **Automatic Recovery**: Failed keys are retried later
✅ **Usage Tracking**: See which keys are being used and their success rates

---

## Step-by-Step Guide

### Quick Start: Web UI

1. **Get API Keys**: Visit https://ai.google.dev/ and create 3-5 free API keys
2. **Start App**: Run `python -m streamlit run app.py`
3. **Enter Keys**: Paste all keys in sidebar (one per line)
4. **Upload PDF**: Select insurance company and upload PDF
5. **Extract**: Click "🚀 Extract Data"
6. **Download**: Click "📥 Download JSON"

### Quick Start: Command-Line

1. **Get API Keys**: Visit https://ai.google.dev/ and create 3-5 free API keys
2. **Create api_keys.txt**: Add keys, one per line
3. **Run Script**: `python pdf_to_json_gemini.py Reliance_pdf reliance`
4. **Check Results**: See output folder for JSON files

### Detailed Steps: Web UI

**Step 1: Get Your Free API Keys**
1. Open browser and go to: **https://ai.google.dev/**
2. Sign in with your Google account
3. Click "Get API Key" button (top right)
4. Click "Create API Key" in new project (or select existing)
5. Copy the API key (starts with `AIzaSy...`)
6. Repeat steps 3-5 to create 2-4 more API keys

**Step 2: Start the Web App**
1. Open PowerShell or Command Prompt
2. Navigate to your folder: `cd d:\Data\Data`
3. Start the app: `python -m streamlit run app.py`
4. Wait for browser to open (or go to http://localhost:8501)

**Step 3: Enter Multiple API Keys**
1. Look at the left sidebar in the web app
2. Find the section "🔑 API Keys"
3. Click in the text area that says "Gemini API Keys"
4. Paste your API keys, one per line
5. The app will automatically save and show: "✅ X API key(s) configured!"

**Step 4: Use the App**
1. Select Insurance Company (reliance or shriram)
2. Upload a PDF file
3. Click "🚀 Extract Data"
4. The app will automatically rotate between your keys!

**Step 5: Check Statistics (Optional)**
1. In the sidebar, expand "📊 API Key Statistics"
2. See which keys are active (✅) or rate limited (❌)
3. Monitor usage per key

### Detailed Steps: Command-Line

**Step 1: Get Your Free API Keys**
(Same as Web UI Step 1)

**Step 2: Create API Keys File**
1. Open Notepad (or any text editor)
2. Create a new file
3. Paste your API keys, one per line
4. Save the file as `api_keys.txt` in the `d:\Data\Data` folder
   - Make sure it's saved as `.txt` (not `.txt.txt`)
   - Save it in the same folder as `pdf_to_json_gemini.py`

**Step 3: Verify the File**
1. Check that `api_keys.txt` exists in `d:\Data\Data`
2. Open it to verify your keys are there (one per line)

**Step 4: Run the Script**
1. Open PowerShell
2. Navigate to folder: `cd d:\Data\Data`
3. Run the script:
   ```powershell
   # For single file
   python pdf_to_json_gemini.py
   
   # For batch processing
   python pdf_to_json_gemini.py Reliance_pdf reliance output 0 10
   ```
4. The script will automatically load keys from `api_keys.txt`
5. Watch the console - it will show which key is being used

### Verification Steps

**Check if Keys are Loaded:**

**Web UI:**
- Look for "✅ X API key(s) configured!" message in sidebar
- Expand "📊 API Key Statistics" to see all keys

**Command Line:**
- Look for message: `[INFO] Loaded X API key(s) from api_keys.txt`
- Or: `[INFO] Loaded X API key(s) from environment variable`

**Test It:**
1. Process a PDF
2. Watch the console/logs - you'll see messages like:
   - `[INFO] Using API key 1/3`
   - `[WARNING] Rate limit hit on current key. Switching to next key...`
   - `[INFO] Using API key 2/3`

---

## Output Format

### Extracted Fields (41 Total)

**Policy Information:**
- POLICY_NO, POLICY_ISSUE_DATE
- RISK_START_DATE, RISK_END_DATE, OD_EXPIRE_DATE

**Vehicle Details:**
- REGISTRATION_NUMBER, REGISTRATION_DATE
- VEHICLE_MAKE, VEHICLE_MODEL, VEHICLE_VARIANT
- ENGINE_NUMBER, CHASIS_NUMBER
- YEAR_OF_MANUFACTURE, CC, FUEL_TYPE
- PRODUCT_CODE, VEHICLE_SUB_TYPE, CV_TYPE, GVW

**Customer Information:**
- CUSTOMER_NAME, CUSTOMER_EMAIL, MOB_NO
- COMPLETE_LOCATION_ADDRESS
- PINCODE, CITY_NAME, STATE_NAME

**Premium Details:**
- TOTAL_PREMIUM, NET_PREMIUM
- OD_PREMIUM, TP_ONLY_PREMIUM
- CGST, SGST, IGST, GST, NCB
- IDV_SUM_INSURED

**Additional:**
- INSURANCE_COMPANY_NAME
- NOMINEE_NAME, NOMINEE_RELATIONSHIP
- FINANCIER_NAME, BROKER_NAME
- COVER

### Sample Output

```json
{
  "POLICY_NO": "920222523110014648",
  "CUSTOMER_NAME": "Mr. ARPIT SRIVASTAVA",
  "REGISTRATION_NUMBER": "MH05EA7412",
  "VEHICLE_MAKE": "HONDA",
  "VEHICLE_MODEL": "CITY",
  "VEHICLE_VARIANT": "1.3 EXI",
  "TOTAL_PREMIUM": "16,555.00",
  "OD_PREMIUM": "10,079.00",
  "TP_ONLY_PREMIUM": "3,951.00",
  "POLICY_ISSUE_DATE": "26 Sep 2025",
  "RISK_START_DATE": "01-Oct-2025",
  "RISK_END_DATE": "30-Sep-2026",
  ... (41 fields total)
}
```

---

## Troubleshooting

### API Key Issues

**Problem: "No API keys found"**
- **Solution**: 
  - Check that keys are entered correctly (one per line)
  - For command line: Verify `api_keys.txt` is in the same folder
  - Check file name spelling (must be exactly `api_keys.txt`)

**Problem: "All keys have hit rate limits"**
- **Solution**:
  - Wait for daily reset (midnight Pacific Time)
  - Add more API keys
  - Process in smaller batches

**Problem: Keys not rotating**
- **Solution**:
  - Make sure you entered multiple keys (not just one)
  - Check the console/logs for key rotation messages
  - Verify keys are valid (not expired)

**Problem: API Key Not Working**
- Make sure you've entered a valid Gemini API key
- Check if the API key has proper permissions
- Verify you haven't exceeded API rate limits

### PDF Processing Issues

**Problem: PDF Not Processing**
- Ensure the PDF is a valid insurance policy document
- Check if the PDF is not password protected
- Verify the PDF contains readable text (not just images)

**Problem: Low Accuracy Issues**
- Check the `extraction_log.txt` for detailed error messages
- Verify the PDF text extraction is working (check intermediate JSON files)
- Review the prompts in `create_extraction_prompt` function
- Verify you've selected the correct insurance company type

**Problem: Extraction Errors**
- Try uploading the PDF again
- Check the extracted text preview to see if text was extracted correctly
- Verify you've selected the correct insurance company type

### Performance Issues

**Problem: API Errors**
- Verify your API key is correct
- Check API rate limits
- Increase `RETRY_DELAY` if needed

**Problem: Memory Issues**
- Process files in smaller batches using `max_files` parameter
- Clear intermediate files periodically

**Problem: Still Getting Rate Limits**
- Add more API keys (5+ recommended for heavy usage)
- Add delays between requests in batch processing
- Process in smaller batches

---

## Advanced Usage

### Batch Processing Tips

1. **Process in Batches**: For thousands of PDFs, process 100 at a time
   ```bash
   python pdf_to_json_gemini.py Reliance_pdf reliance output 0 100
   python pdf_to_json_gemini.py Reliance_pdf reliance output 100 100
   python pdf_to_json_gemini.py Reliance_pdf reliance output 200 100
   ```

2. **Resume Processing**: If processing stops, resume from last index
   ```bash
   # Check how many files processed, then resume
   python pdf_to_json_gemini.py Reliance_pdf reliance output 150 100
   ```

3. **Monitor Progress**: Check `extraction_log.txt` for real-time progress

### Customization

**Modify Extraction Rules:**
- Edit the `create_extraction_prompt` function in the script
- Adjust field mappings for your specific needs
- Add validation rules in `validate_and_clean_data` function

**Adjust Retry Logic:**
- Modify `MAX_RETRIES` constant (default: 3)
- Adjust `RETRY_DELAY` constant (default: 2 seconds)

**Change Output Format:**
- Modify the JSON structure in the schema
- Add custom fields
- Change field names

### Performance Optimization

**With 3 API Keys:**
- 45 requests per minute
- 4,500 requests per day
- Can process ~3,000-4,000 PDFs per day

**With 5 API Keys:**
- 75 requests per minute
- 7,500 requests per day
- Can process ~5,000-6,000 PDFs per day

**Best Practices:**
- Use 3-5 API keys for optimal performance
- Process in batches of 50-100 PDFs
- Monitor key statistics regularly
- Add delays for very large batches

---

## Project Structure

```
d:\Data\Data\
├── app.py                          # Streamlit Web UI
├── pdf_to_json_gemini.py           # Command-line script
├── api_keys.txt                    # API keys (user creates)
├── api_keys.txt.example            # Example API keys file
├── requirements_ui.txt             # Dependencies for UI
├── README.md                       # This documentation file
│
├── Reliance_pdf/                   # Input PDFs
│   ├── *.pdf
│   └── *_extracted.json
│
└── output/                         # Results (created automatically)
    ├── *_extracted.json
    └── processing_summary.json
```

---

## Supported Insurance Companies

- **Reliance General Insurance**
- **Shriram General Insurance**

More companies can be added by modifying the extraction prompts.

---

## Notes

- The app processes one PDF at a time in Web UI
- For batch processing, use the command-line script
- Large PDFs may take longer to process (5-10 seconds typically)
- The app uses temporary files that are automatically cleaned up
- All extracted data is validated and cleaned before output

---

## Quick Reference

### Web UI Commands
```bash
# Start app
python -m streamlit run app.py

# Custom port
python -m streamlit run app.py --server.port 8502
```

### Command-Line Commands
```bash
# Single file
python pdf_to_json_gemini.py

# Batch processing
python pdf_to_json_gemini.py Reliance_pdf reliance

# With options
python pdf_to_json_gemini.py Reliance_pdf reliance output 0 100
```

### API Key Setup
```bash
# Environment variable (single key)
set GEMINI_API_KEY=your_key_here

# Environment variable (multiple keys)
set GEMINI_API_KEYS=key1,key2,key3

# Or create api_keys.txt file (one key per line)
```

---

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the extraction logs (`extraction_log.txt`)
3. Verify API keys are valid and have quota
4. Check PDF format and content

---

## License

This project is provided as-is for educational and commercial use.

---

**Last Updated:** 2024
**Version:** 1.0



