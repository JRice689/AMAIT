.venv\scripts\activate
pip install -r requirement.txt
python manage.py makemirgrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver