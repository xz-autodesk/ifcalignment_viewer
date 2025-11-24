"""
IFC Alignment Viewer - Flask Web Application
Allows uploading IFC files and visualizing alignments interactively
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from werkzeug.utils import secure_filename
from utils.ifc_processor import IFCProcessor
from utils.visualizer import AlignmentVisualizer

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'ifc'}

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Store current session data
session_data = {}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle IFC file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only .ifc files are allowed'}), 400
    
    try:
        # Save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the IFC file to extract alignments
        processor = IFCProcessor(filepath)
        alignments = processor.get_alignments()
        
        # Store in session
        session_data['current_file'] = filepath
        session_data['filename'] = filename
        session_data['alignments'] = alignments
        
        return jsonify({
            'success': True,
            'filename': filename,
            'alignments': alignments
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/visualize/<alignment_id>', methods=['GET'])
def visualize_alignment(alignment_id):
    """Generate visualization for a specific alignment."""
    if 'current_file' not in session_data:
        return jsonify({'error': 'No file uploaded'}), 400
    
    try:
        filepath = session_data['current_file']
        
        # Create visualizer
        visualizer = AlignmentVisualizer(filepath)
        
        # Generate visualization and analysis
        result = visualizer.create_visualization(alignment_id, app.config['OUTPUT_FOLDER'])
        
        return jsonify({
            'success': True,
            'html_path': result['html_filename'],
            'summary': result['summary'],
            'base_segments': result['base_segments'],
            'vertical_segments': result['vertical_segments']
        })
    
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


@app.route('/output/<filename>')
def serve_output(filename):
    """Serve generated visualization files."""
    return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename))


@app.route('/get_visualization/<filename>')
def get_visualization(filename):
    """Get the visualization HTML content."""
    filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return content


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

