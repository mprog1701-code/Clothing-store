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
            # If username looks like a phone number, try phone authentication
            if username and username.startswith('05'):
                user = User.objects.get(phone=username)
            else:
                # Try regular username authentication
                user = User.objects.get(username=username)
            
            # Check password
            if user.check_password(password):
                return user
            return None
        except User.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        """
        Retrieve a user by ID.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None