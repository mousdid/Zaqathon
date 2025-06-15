# Zaqathon Order Processing System

## Overview

Zaqathon Order Processing System is an AI-powered solution that automates the processing of purchase orders received via email. The system extracts product information, validates it against an existing product catalog, and provides business insights.

### Key Features

- **Email Processing**: Extract structured data from unstructured email content
- **Product Validation**: Verify products against catalog for existence, minimum order quantities, and availability
- **Automated Insights**: Generate business insights and recommendations
- **Web Interface**: User-friendly upload and viewing of results
- **API Access**: Programmatic access to processing capabilities

## Architecture

The system uses a modular agent-based architecture with:

- **Email Agent**: Parses emails to extract order information
- **Lookup Agent**: Validates products against the catalog and generates insights
- **Orchestrator**: Coordinates workflow between agents using LangGraph
- **Web Interface**: Flask-based UI for interaction

## Installation

### Prerequisites

- Python 3.9+
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Zaqathon.git
cd Zaqathon
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your API keys:
   - Create a `llm_keys.txt` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

### Web Interface

1. Start the Flask app:
```bash
python -m src.interface.app
```

2. Open your browser and navigate to `http://127.0.0.1:5000/`

3. Upload email files (TXT format) containing purchase order information

4. View the processing results and insights

### Directory Structure

```
Zaqathon/
├── data/
│   ├── catalogs/      # Product catalog files
│   ├── database/      # Product catalog and other data
│   ├── downloads/
│   └── uploads/       # Uploaded email files
├── notebooks/
│   └── main.ipynb
├── src/
│   ├── interface/
│   │   ├── static/        # CSS, JavaScript files
│   │   ├── templates/     # HTML templates
│   │   └── app.py         # Flask app
│   ├── ochestration/
│   │   └── orchestrator.py
│   └── utils/
│       ├── agents/
│       │   ├── email_agent.py
│       │   └── lookup_agent.py
│       ├── config.py
│       ├── data_loader.py
│       ├── data_preprocessing.py
│       └── prompt_template.py
├── venv/
├── .gitignore
├── llm_keys.txt
├── README.md
```

