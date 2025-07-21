# NCC Text Extraction with Clickable Page Numbers

This application processes PDF tender documents and fills Excel templates with extracted information. The page numbers in the Excel output are now clickable and will open the corresponding PDF page in a new tab.

## Features

- 📄 **PDF Processing**: Upload and process PDF tender documents
- 📊 **Excel Auto-fill**: Automatically fill Excel templates with extracted information
- 🔗 **Clickable Page Numbers**: Click on page numbers in the Excel output to open the PDF at that specific page
- 💬 **RAG Chat**: Ask questions about the uploaded documents

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Starting the Application

**Option 1: Using the batch file (Windows)**
```bash
start_servers.bat
```

**Option 2: Using Python**
```bash
python run_servers.py
```

**Option 3: Manual startup**
```bash
# Terminal 1: Start PDF server
python pdf_server.py

# Terminal 2: Start Streamlit app
streamlit run app.py
```

### Using the Application

1. **Upload Files**: Upload your PDF tender document and Excel template
2. **Processing**: The system will process the PDF and fill the Excel template
3. **View Results**: The filled Excel data will be displayed with clickable page numbers
4. **Click Page Numbers**: Click on any page number to open the PDF at that specific page in a new tab
5. **Download**: Download the filled Excel file for offline use

## Technical Details

### Architecture
- **Streamlit App** (port 8501): Main web interface
- **Flask PDF Server** (port 5001): Serves PDF files with proper headers
- **Faiss**: Local vector storage for document embeddings
- **OpenAI**: LLM for text extraction and chat functionality

### How Clickable Pages Work
1. PDFs are stored permanently in the `stored_pdfs/` directory
2. Page numbers in the Excel output are converted to clickable HTML links
3. Clicking a page number opens the PDF at that specific page using the URL fragment `#page=N`
4. The Flask server serves PDFs with proper MIME types for browser viewing

## File Structure
```
├── app.py                  # Main Streamlit application
├── pdf_server.py          # Flask server for serving PDFs
├── run_servers.py         # Script to start both servers
├── start_servers.bat      # Windows batch file
├── excel_filler.py        # Excel processing logic
├── chat.py                # RAG chat functionality
├── embedder.py            # PDF processing and embedding
├── stored_pdfs/           # Directory for stored PDF files
└── requirements.txt       # Python dependencies
```

## Troubleshooting

### 403 Error when clicking page numbers
If you get a 403 error when clicking page numbers:

1. **Test the PDF server**:
   ```bash
   python test_pdf_server.py
   ```

2. **Check if both servers are running**:
   - Use `python run_servers.py` to start both servers
   - Or use the batch file option 1: `start_servers.bat`

3. **Verify PDF file exists**:
   - Check that the PDF file exists in the `stored_pdfs/` directory
   - The PDF should be automatically copied there after upload

4. **Check browser console**:
   - Open browser developer tools (F12)
   - Look for JavaScript errors in the console
   - Check network tab for failed requests

### Other Issues

- **Port conflicts**: If port 5001 is already in use, modify the port in `pdf_server.py`
- **PDF not opening**: Ensure the Flask server is running and check browser pop-up settings
- **Page numbers not clickable**: Verify that the Excel file has page numbers in the correct column
- **CORS errors**: Make sure both servers are running on the correct ports (Streamlit: 8501, Flask: 5001)

### Testing Commands

```bash
# Test PDF server only
python test_pdf_server.py

# Start PDF server only
python pdf_server.py

# Start Streamlit app only
streamlit run app.py

# Start both servers
python run_servers.py
``` 