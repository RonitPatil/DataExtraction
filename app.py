import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

from embedder import process_pdf, upload_chunks_to_astradb, is_pdf_already_uploaded, mark_pdf_as_uploaded, get_uploaded_pdfs_list, clear_uploaded_pdfs, clear_astra_collection
from excel_filler import fill_excel_with_rag
from chat import rag_chat
import pandas as pd
import tempfile
import shutil
from pathlib import Path

PDF_STORAGE_DIR = "stored_pdfs"
os.makedirs(PDF_STORAGE_DIR, exist_ok=True)

def store_pdf_permanently(temp_pdf_path, pdf_filename):
    """Store PDF permanently and return the stored path"""
    stored_path = os.path.join(PDF_STORAGE_DIR, pdf_filename)
    shutil.copy2(temp_pdf_path, stored_path)
    return stored_path

def get_stored_pdf_path(pdf_filename):
    """Get the path to stored PDF"""
    return os.path.join(PDF_STORAGE_DIR, pdf_filename)

def make_page_numbers_clickable(df, pdf_filename):
    display_df = df.copy()

    # find the "page" column
    page_col = next(
        (col for col in display_df.columns
         if 'page' in col.lower() or display_df.columns.get_loc(col) == 2),
        None
    )

    if page_col:
        def linkify(pages):
            if pd.isna(pages) or pages == '':
                return ''
            links = []
            for page in str(pages).split(','):
                page = page.strip()
                if page.isdigit():
                    # direct URL – no JS needed
                    url = f'http://localhost:5001/pdf/{pdf_filename}#page={page}'
                    links.append(f'<a href="{url}" target="_blank">{page}</a>')
            return ' '.join(links)

        display_df[page_col] = display_df[page_col].apply(linkify)

    return display_df

def make_page_numbers_clickable_multi(df, pdf_filenames):
    display_df = df.copy()

    # find the "page" column and document name column
    page_col = next(
        (col for col in display_df.columns
         if 'page' in col.lower() or display_df.columns.get_loc(col) == 2),
        None
    )
    
    doc_col = next(
        (col for col in display_df.columns
         if 'document' in col.lower() or display_df.columns.get_loc(col) == 1),
        None
    )

    if page_col:
        def linkify_multi(row):
            pages = row[page_col] if page_col else ''
            doc_name = row[doc_col] if doc_col else (pdf_filenames[0] if pdf_filenames else 'unknown.pdf')
            
            if pd.isna(pages) or pages == '':
                return ''
            
            # Ensure doc_name has .pdf extension
            if not str(doc_name).endswith('.pdf'):
                doc_name = f"{doc_name}.pdf"
            
            links = []
            for page in str(pages).split(','):
                page = page.strip()
                if page.isdigit():
                    # direct URL – no JS needed
                    url = f'http://localhost:5001/pdf/{doc_name}#page={page}'
                    links.append(f'<a href="{url}" target="_blank">{page}</a>')
            return ' '.join(links)

        display_df[page_col] = display_df.apply(linkify_multi, axis=1)

    return display_df


import streamlit as st
st.set_page_config(page_title="Tender Document Auto-Fill", layout="wide")

# Remove top padding via CSS + Add JavaScript for PDF opening
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
        }
        
        .pdf-modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0,0,0,0.9);
        }
        
        .pdf-modal-content {
            background-color: #fefefe;
            margin: 2% auto;
            padding: 0;
            border: 1px solid #888;
            width: 90%;
            height: 90%;
            position: relative;
        }
        
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            position: absolute;
            right: 15px;
            top: 10px;
            z-index: 1001;
            background: white;
            border-radius: 50%;
            width: 35px;
            height: 35px;
            text-align: center;
            line-height: 35px;
            cursor: pointer;
        }
        
        .close:hover,
        .close:focus {
            color: black;
            text-decoration: none;
            cursor: pointer;
        }
    </style>
    <div id="pdfModal" class="pdf-modal">
        <div class="pdf-modal-content">
            <span class="close" onclick="closePdfModal()">&times;</span>
            <iframe id="pdfFrame" width="100%" height="100%" frameborder="0"></iframe>
        </div>
    </div>
    <script>
        function openPdfAtPage(filename, page) {
            // Test if PDF server is accessible first
            fetch(`http://localhost:5001/health`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('PDF server not accessible');
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('PDF server status:', data);
                    // Use a more reliable PDF opening approach
                    openPdfDirectly(filename, page);
                })
                .catch(error => {
                    console.error('Error accessing PDF server:', error);
                    alert('Error: PDF server is not running. Please ensure both servers are started using "python run_servers.py"');
                });
        }
        
        function openPdfDirectly(filename, page) {
            const baseUrl = `http://localhost:5001/pdf/${filename}`;
            
            console.log(`Attempting to open PDF: ${baseUrl} at page ${page}`);
            
            // First, test if the PDF is accessible
            fetch(`http://localhost:5001/test-pdf/${filename}`)
                .then(response => response.json())
                .then(data => {
                    console.log('PDF test result:', data);
                    if (data.exists && data.readable) {
                        // PDF is accessible, try to open it
                        tryOpenPdfWindow(baseUrl, page);
                    } else {
                        alert('PDF file is not accessible or readable');
                    }
                })
                .catch(error => {
                    console.error('Error testing PDF:', error);
                    // Still try to open it even if test fails
                    tryOpenPdfWindow(baseUrl, page);
                });
        }
        
        function tryOpenPdfWindow(baseUrl, page) {
            console.log(`Opening PDF window: ${baseUrl}`);
            
            // Try multiple approaches
            const approaches = [
                // Approach 1: Simple window.open
                () => {
                    const newWindow = window.open(baseUrl, '_blank', 'width=800,height=600');
                    if (newWindow) {
                        console.log('PDF opened successfully with window.open');
                        setTimeout(() => {
                            if (page > 1) {
                                try {
                                    newWindow.location.hash = `page=${page}`;
                                } catch (e) {
                                    console.log('Could not navigate to specific page:', e);
                                }
                            }
                        }, 1000);
                        return true;
                    }
                    return false;
                },
                
                // Approach 2: Create link and click
                () => {
                    const link = document.createElement('a');
                    link.href = baseUrl;
                    link.target = '_blank';
                    link.rel = 'noopener noreferrer';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    console.log('PDF opened by clicking link');
                    return true;
                },
                
                // Approach 3: Modal fallback
                () => {
                    console.log('Using modal fallback');
                    showPdfModal(baseUrl, page);
                    return true;
                }
            ];
            
            // Try each approach
            for (let i = 0; i < approaches.length; i++) {
                try {
                    if (approaches[i]()) {
                        break;
                    }
                } catch (e) {
                    console.error(`Approach ${i + 1} failed:`, e);
                }
            }
        }
        
        function showPdfModal(baseUrl, page) {
            const modal = document.getElementById('pdfModal');
            const frame = document.getElementById('pdfFrame');
            
            // Set the PDF source directly
            frame.src = baseUrl;
            modal.style.display = 'block';
            
            // Try to navigate to page after loading
            frame.onload = function() {
                try {
                    if (page > 1) {
                        frame.contentWindow.location.hash = `page=${page}`;
                    }
                } catch (e) {
                    console.log('Could not navigate to specific page in modal:', e);
                }
            };
        }
        
        function closePdfModal() {
            const modal = document.getElementById('pdfModal');
            const frame = document.getElementById('pdfFrame');
            
            modal.style.display = 'none';
            frame.src = '';
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('pdfModal');
            if (event.target == modal) {
                closePdfModal();
            }
        }
        
        function testPdfServer() {
            fetch(`http://localhost:5001/health`)
                .then(response => response.json())
                .then(data => {
                    console.log('PDF server health:', data);
                    alert('PDF server is running! Files: ' + data.files_count);
                })
                .catch(error => {
                    console.error('PDF server not accessible:', error);
                    alert('PDF server is not running. Please start it using "python run_servers.py"');
                });
        }
        
        // Make functions globally available
        window.openPdfAtPage = openPdfAtPage;
        window.testPdfServer = testPdfServer;
    </script>
""", unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "excel_filled" not in st.session_state:
    st.session_state.excel_filled = False

if "current_files" not in st.session_state:
    st.session_state.current_files = {"pdfs": [], "excel": None}

if "filled_excel_data" not in st.session_state:
    st.session_state.filled_excel_data = None

if "filled_excel_path" not in st.session_state:
    st.session_state.filled_excel_path = None


chat_header_col1, chat_header_col2 = st.columns([3, 1])
with chat_header_col1:
    st.title("Tender Document Auto-Fill with AI")
with chat_header_col2:
    if st.button("🗑️", key="clear_chat", help="Clear chat history"):
        st.session_state.chat_history = []
        st.session_state.excel_filled = False
        st.session_state.current_files = {"pdfs": [], "excel": None}
        st.session_state.filled_excel_data = None
        st.session_state.filled_excel_path = None
        st.rerun()


st.sidebar.header("File Upload")
uploaded_pdfs = st.sidebar.file_uploader("Upload Tender PDFs", type=["pdf"], accept_multiple_files=True)
uploaded_excel = st.sidebar.file_uploader("Upload Excel (tender_data_format.xlsx)", type=["xlsx"])

st.sidebar.header("PDF Server Status")
if st.sidebar.button("🔍 Test PDF Server"):
    st.sidebar.markdown("""
    <script>
        testPdfServer();
    </script>
    """, unsafe_allow_html=True)
    st.sidebar.info("Check browser console for server status")

st.sidebar.header("Uploaded PDFs")
uploaded_pdfs_list = get_uploaded_pdfs_list()
if uploaded_pdfs_list:
    st.sidebar.write("✅ **Already processed:**")
    for pdf in uploaded_pdfs_list:
        st.sidebar.write(f"• {pdf}")
    if st.sidebar.button("🗑️ Clear All Uploaded PDFs"):
        clear_uploaded_pdfs()
        st.sidebar.success("All uploaded PDFs cleared!")
        st.rerun()
else:
    st.sidebar.write("No PDFs uploaded yet")

# Show currently selected PDFs
if uploaded_pdfs:
    st.sidebar.header("Current Session")
    st.sidebar.write(f"📁 **Selected PDFs ({len(uploaded_pdfs)}):**")
    for pdf in uploaded_pdfs:
        st.sidebar.write(f"• {pdf.name}")
    if uploaded_excel:
        st.sidebar.write(f"📊 **Excel:** {uploaded_excel.name}")

if uploaded_pdfs and uploaded_excel:
    # Check if these are new files
    current_pdf_names = [pdf.name for pdf in uploaded_pdfs]
    current_excel_name = uploaded_excel.name
    
    files_changed = (
        st.session_state.current_files["pdfs"] != current_pdf_names or 
        st.session_state.current_files["excel"] != current_excel_name
    )
    
    if files_changed:
        st.session_state.excel_filled = False
        st.session_state.current_files = {"pdfs": current_pdf_names, "excel": current_excel_name}
    
    # Process Excel file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as excel_temp:
        excel_temp.write(uploaded_excel.read())
        excel_path = excel_temp.name

    # Process all PDFs
    pdf_filenames = []
    temp_pdf_paths = []
    
    for uploaded_pdf in uploaded_pdfs:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_temp:
            pdf_temp.write(uploaded_pdf.read())
            temp_pdf_paths.append(pdf_temp.name)
            pdf_filenames.append(uploaded_pdf.name)
            
            # Store PDF permanently for serving
            store_pdf_permanently(pdf_temp.name, uploaded_pdf.name)
    
    # Process each PDF for embeddings
    for i, (pdf_path, pdf_filename) in enumerate(zip(temp_pdf_paths, pdf_filenames)):
        if is_pdf_already_uploaded(pdf_path, pdf_filename):
            st.warning(f"📋 PDF '{pdf_filename}' has already been processed and uploaded to database.")
        else:
            st.info(f"🔄 Processing PDF {i+1}/{len(pdf_filenames)}: '{pdf_filename}'...")
            chunks, metadatas = process_pdf(pdf_path, pdf_filename)
            upload_chunks_to_astradb(chunks, metadatas, pdf_filename)
            mark_pdf_as_uploaded(pdf_path, pdf_filename)
            st.success(f"✅ Successfully processed and uploaded '{pdf_filename}'")

    # Only fill Excel if it hasn't been filled yet or files changed
    if not st.session_state.excel_filled or files_changed:
        with st.expander("📊 View Filled Excel Data", expanded=False):
            st.info(f"📊 Filling Excel file using AI from {len(pdf_filenames)} PDF(s)...")
            # Use the first PDF filename as fallback, but the function will use actual document names from metadata
            filled_excel_path = fill_excel_with_rag(excel_path, pdf_filenames[0] if pdf_filenames else "multiple_pdfs")
            filled_df = pd.read_excel(filled_excel_path)
            
            # Store ORIGINAL data in session state (without HTML processing)
            st.session_state.filled_excel_data = filled_df
            st.session_state.filled_excel_path = filled_excel_path
            
            # Create display version with clickable links for multiple PDFs
            display_df = make_page_numbers_clickable_multi(filled_df, pdf_filenames)
            
            # Display download button first
            with open(filled_excel_path, "rb") as f:
                st.download_button("📥 Download Filled Excel", f, file_name="filled_tender_data.xlsx")
            
            # Display with HTML to render clickable links
            st.markdown("**Filled Excel Data (Click page numbers to open PDF):**")
            st.markdown(display_df.to_html(escape=False), unsafe_allow_html=True)
            
            st.session_state.excel_filled = True
    else:
        # Display previously filled data
        if st.session_state.filled_excel_data is not None:
            with st.expander("📊 View Filled Excel Data", expanded=False):
                # Display download button first
                if st.session_state.filled_excel_path and os.path.exists(st.session_state.filled_excel_path):
                    with open(st.session_state.filled_excel_path, "rb") as f:
                        st.download_button("📥 Download Filled Excel", f, file_name="filled_tender_data.xlsx")
                
                # Use original data and create fresh display version with clickable links
                display_df = make_page_numbers_clickable_multi(st.session_state.filled_excel_data, current_pdf_names)
                st.markdown("**Filled Excel Data (Click page numbers to open PDF):**")
                st.markdown(display_df.to_html(escape=False), unsafe_allow_html=True)
        
        st.success("✅ Excel file has already been filled. Use the chat below to ask questions about the documents.")

    # Only delete the temporary uploaded files, not the stored PDFs
    for temp_path in temp_pdf_paths:
        os.unlink(temp_path)
    os.unlink(excel_path)

chat_container = st.container(height=350)
with chat_container:
    if st.session_state.chat_history:
        for i, (user_msg, bot_msg, sources) in enumerate(st.session_state.chat_history):
            st.markdown(f"""
            <div style="display: flex; margin-bottom: 10px; justify-content: flex-end;">
                <div style="background-color: #dcf8c6; padding: 15px; border-radius: 15px; max-width: 70%; margin-left: 30%;">
                    <strong>You:</strong> {user_msg}
                </div>
                <div style="margin-left: 15px; font-size: 24px;">👤</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="display: flex; margin-bottom: 20px;">
                <div style="margin-right: 15px; font-size: 24px;">🤖</div>
                <div style="background-color: #f1f1f1; padding: 15px; border-radius: 15px; max-width: 70%;">
                    <strong>Assistant:</strong> {bot_msg}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if sources:
                st.markdown(f"""
                <div style="margin-left: 50px; margin-bottom: 15px;">
                    <small style="color: #666;">📄 Source page(s): {', '.join(map(str, sources))}</small>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("💡 Start a conversation by typing a message below!")

st.markdown("---")

if 'processing' not in st.session_state:
    st.session_state.processing = False

def process_message():
    user_input = st.session_state.current_input
    if user_input and not st.session_state.processing:
        if uploaded_pdfs_list or (uploaded_pdfs and uploaded_excel):
            st.session_state.processing = True
            try:
                answer, sources = rag_chat(user_input, st.session_state.chat_history)
                st.session_state.chat_history.append((user_input, answer, sources))
                st.session_state.current_input = ""
            except Exception as e:
                st.error(f"Error processing message: {e}")
            finally:
                st.session_state.processing = False
        else:
            st.warning("⚠️ Please upload and process documents first!")

user_input = st.text_input("", key="current_input", placeholder="Ask about the tender document...", label_visibility="collapsed", disabled=st.session_state.processing, on_change=process_message)

if st.session_state.processing:
    st.info("🤔 Processing your message...") 