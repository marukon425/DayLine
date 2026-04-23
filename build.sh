pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='maruriku0655@gmail.com').exists():
    User.objects.create_superuser(email='maruriku0655@gmail.com', username='admin', password='admin')
print('done')
"