pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.filter(email='ktq2590324@stu.o-hara.ac.jp').first()
if u:
    u.is_staff = True
    u.is_superuser = True
    u.save()
    print('done')
else:
    print('user not found')
"