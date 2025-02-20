
# Ensure Python 3.10+
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations (if needed)
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput
