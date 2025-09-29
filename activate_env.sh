#!/bin/bash
# Script to activate virtual environment and ensure all dependencies are working
# Usage: source activate_env.sh

echo "Activating EmailParser virtual environment..."
source venv/bin/activate

echo "Virtual environment activated!"
echo "Python: $(which python)"
echo "Python version: $(python --version)"
echo "Pip location: $(which pip)"

# Test imports
echo "Testing imports..."
python -c "import numpy; print('✓ numpy:', numpy.__version__)" 2>/dev/null || echo "✗ numpy import failed"
python -c "import spacy; print('✓ spacy:', spacy.__version__)" 2>/dev/null || echo "✗ spacy import failed"
python -c "import spacy; spacy.load('en_core_web_sm'); print('✓ en_core_web_sm model loaded')" 2>/dev/null || echo "✗ en_core_web_sm model failed"

echo ""
echo "Environment ready! You can now run your commands."
echo "Example: python -c \"from Parser import convert; print(convert('emails/test0.txt'))\""