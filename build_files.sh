
python3.10 -m venv venv

source venv/bin/activate

pip install --upgrade pip


pip install -r requirements.txt


python manage.py migrate


python manage.py collectstatic --noinput