from flask import Flask, send_from_directory, abort, jsonify
from flask_cors import CORS
import os
import logging

app = Flask(__name__)
CORS(app, origins=["http://localhost:8501", "http://127.0.0.1:8501", "https://mozilla.github.io"], 
     resources={r"/pdf/*": {"origins": "*"}})

PDF_STORAGE_DIR = "stored_pdfs"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    """Serve PDF files with proper headers"""
    try:
        # Security: Only allow PDF files
        if not filename.lower().endswith('.pdf'):
            logger.warning(f"Attempted to access non-PDF file: {filename}")
            abort(403)
        
        # Check if file exists
        file_path = os.path.join(PDF_STORAGE_DIR, filename)
        if not os.path.exists(file_path):
            logger.error(f"PDF file not found: {file_path}")
            abort(404)
        
        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            logger.error(f"PDF file not readable: {file_path}")
            abort(403)
        
        logger.info(f"Serving PDF: {filename}")
        
        response = send_from_directory(
            PDF_STORAGE_DIR, 
            filename, 
            mimetype='application/pdf',
            as_attachment=False
        )
        
        # Enhanced headers for PDF.js compatibility
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Cache-Control'] = 'public, max-age=3600'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Range'
        response.headers['Access-Control-Expose-Headers'] = 'Accept-Ranges, Content-Length, Content-Range'
        
        return response
        
    except Exception as e:
        logger.error(f"Error serving PDF {filename}: {str(e)}")
        abort(500)

@app.route('/pdf/<filename>', methods=['OPTIONS'])
def serve_pdf_options(filename):
    """Handle OPTIONS requests for CORS"""
    response = jsonify({})
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Range'
    return response

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "message": "PDF server is running",
        "storage_dir": PDF_STORAGE_DIR,
        "files_count": len([f for f in os.listdir(PDF_STORAGE_DIR) if f.endswith('.pdf')]) if os.path.exists(PDF_STORAGE_DIR) else 0
    })

@app.route('/list-pdfs')
def list_pdfs():
    """List all available PDFs"""
    try:
        if not os.path.exists(PDF_STORAGE_DIR):
            return jsonify({"pdfs": []})
        
        pdfs = [f for f in os.listdir(PDF_STORAGE_DIR) if f.lower().endswith('.pdf')]
        return jsonify({"pdfs": pdfs})
    except Exception as e:
        logger.error(f"Error listing PDFs: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/test-pdf/<filename>')
def test_pdf(filename):
    """Test endpoint to check if PDF is accessible"""
    try:
        if not filename.lower().endswith('.pdf'):
            return jsonify({"error": "Not a PDF file"}), 400
        
        file_path = os.path.join(PDF_STORAGE_DIR, filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "PDF file not found"}), 404
        
        file_size = os.path.getsize(file_path)
        return jsonify({
            "filename": filename,
            "exists": True,
            "size_bytes": file_size,
            "readable": os.access(file_path, os.R_OK),
            "pdf_url": f"/pdf/{filename}"
        })
    except Exception as e:
        logger.error(f"Error testing PDF {filename}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(403)
def forbidden(error):
    return jsonify({"error": "Access forbidden"}), 403

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "File not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Ensure storage directory exists
    os.makedirs(PDF_STORAGE_DIR, exist_ok=True)
    
    logger.info(f"Starting PDF server on port 5001")
    logger.info(f"Storage directory: {os.path.abspath(PDF_STORAGE_DIR)}")
    
    app.run(host='0.0.0.0', port=5001, debug=True) 