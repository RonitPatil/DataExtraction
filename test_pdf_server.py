import requests
import os
import sys

def test_pdf_server():
    """Test if the PDF server is running and accessible"""
    
    print("Testing PDF server...")
    
    # Test 1: Health check
    try:
        response = requests.get("http://localhost:5001/health", timeout=5)
        print(f"✅ Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Server status: {data.get('status')}")
            print(f"   Files count: {data.get('files_count')}")
            print(f"   Storage dir: {data.get('storage_dir')}")
        else:
            print(f"❌ Health check failed with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        print("   Make sure to start the PDF server with 'python pdf_server.py'")
        return False
    
    # Test 2: List PDFs
    try:
        response = requests.get("http://localhost:5001/list-pdfs", timeout=5)
        print(f"✅ List PDFs: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            pdfs = data.get('pdfs', [])
            print(f"   Available PDFs: {pdfs}")
        else:
            print(f"❌ List PDFs failed with status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ List PDFs failed: {e}")
    
    # Test 3: Check local storage directory
    storage_dir = "stored_pdfs"
    if os.path.exists(storage_dir):
        files = [f for f in os.listdir(storage_dir) if f.endswith('.pdf')]
        print(f"✅ Local storage directory exists")
        print(f"   PDF files found: {files}")
        
        # Test accessing specific PDF
        if files:
            test_pdf = files[0]
            try:
                response = requests.get(f"http://localhost:5001/pdf/{test_pdf}", timeout=5)
                print(f"✅ PDF access test ({test_pdf}): {response.status_code}")
                if response.status_code == 200:
                    print(f"   Content-Type: {response.headers.get('Content-Type')}")
                    print(f"   Content-Length: {response.headers.get('Content-Length')}")
                else:
                    print(f"❌ PDF access failed with status: {response.status_code}")
                    print(f"   Response: {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"❌ PDF access failed: {e}")
    else:
        print(f"❌ Local storage directory '{storage_dir}' does not exist")
    
    print("\nTest completed!")
    return True

if __name__ == "__main__":
    success = test_pdf_server()
    sys.exit(0 if success else 1) 