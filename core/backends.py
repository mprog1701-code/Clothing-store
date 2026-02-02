from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class PhoneBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using their phone number.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user using phone number or username.
        """
        # Try to get user by phone number first
        try:
            if username and username.startswith('07'):
                user = User.objects.filter(phone=username).order_by('-is_superuser', '-is_staff', '-date_joined').first()
            else:
                user = User.objects.filter(username=username).order_by('-is_superuser', '-is_staff', '-date_joined').first()
            if not user:
                return None
            if user.check_password(password):
                return user
            return None
        except Exception:
            return None
    
    def get_user(self, user_id):
        """
        Retrieve a user by ID.
        """
        try:
            return User.objects.filter(pk=user_id).first()
        except Exception:
            return None
