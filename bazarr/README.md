
NOTE: must use python 3.12

If your on mac you may need to change the `python` below to `python3.12`

# Create a virtual environment

python -m venv venv

# Activate the virtual environment

source venv/bin/activate

# Install the dependencies

pip install -r requirements.txt

# Run

python bazarr/main.py --no-update
