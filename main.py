import sys
import os

# Dynamic path resolution to find and load the V5.0 application
v5_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Mint-Frost-AI_V5.0'))
sys.path.insert(0, v5_dir)

# Import the Flask application from V5.0
from app import app

# For direct local runner executions (fallback)
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
