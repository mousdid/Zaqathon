import os
import json
from flask import Flask, render_template, request, jsonify, flash
from werkzeug.utils import secure_filename

# Import the orchestrator
from src.ochestration.orchestrator import OrderProcessingOrchestrator

app = Flask(__name__)
app.secret_key = 'zaqathon_secret_key'

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'uploads')
CATALOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'database', 'product_catalog.csv')

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure allowed file extensions
ALLOWED_EXTENSIONS = {'txt'}

# Initialize orchestrator
orchestrator = OrderProcessingOrchestrator(
    catalog_path=CATALOG_PATH,
    temperature=0.2
)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'email_file' not in request.files:
            flash('No file part')
            return render_template('index.html')
        
        file = request.files['email_file']
        
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return render_template('index.html')
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            # Read the email content
            with open(file_path, 'r') as f:
                email_content = f.read()
            
            # Process the email through the orchestrator
            result = orchestrator.process_email(email_content, filename)
            
            # Format the result for better display
            result_formatted = {
                "success": result["success"],
                "summary": result["summary"],
                "order": json.dumps(result["order"], indent=2),
                "validation": json.dumps(result["validation"], indent=2)
            }
            
            return render_template('index.html', result=result_formatted)
    
    return render_template('index.html')

@app.route('/api/process-email', methods=['POST'])
def process_email_api():
    # Check if the post request has the file part
    if 'email_file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['email_file']
    
    # If user does not select file, browser also submits an empty part without filename
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Read the email content
        with open(file_path, 'r') as f:
            email_content = f.read()
        
        # Process the email through the orchestrator
        result = orchestrator.process_email(email_content, filename)
        
        return jsonify(result)
    
    return jsonify({"error": "Invalid file type"}), 400

if __name__ == '__main__':
    app.run(debug=True)