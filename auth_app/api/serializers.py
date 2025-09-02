import random
import string
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Checks for unique email and matching passwords.
    Generates a unique username with email.

    Fields:
        confirmed_password (str): Write-only field to confirm the password.
    """
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        """
        Meta class for RegisterSerializer.

        Attributes:
            model (User): The user model.
            fields (tuple): The fields to include in the serialization.
            extra_kwargs (dict): Additional keyword arguments for the fields.
        """
        model = User
        fields = ('email', 'password', 'confirmed_password')
        extra_kwargs = {
            'password': {'write_only': True},
            'confirmed_password': {'write_only': True}
        }

    def validate_confirmed_password(self, value):
        """Check if confirmed password matches the password."""
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError("Passwords do not match.")
        return value

    def validate_email(self, value):
        """Check if email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def generate_username(self, email):
        """Generate a unique username based on the email."""
        local_part, domain_part = email.split("@", 1)
        domain_clean = domain_part.split(".")[0]
        base_username = f"{local_part}{domain_clean}"
        base_username = "".join(ch for ch in base_username.lower() if ch.isalnum())
        username = base_username
        while User.objects.filter(username=username).exists():
            suffix = ''.join(random.choices(string.digits, k=3))
            username = f"{base_username}{suffix}"
        return username

    def save(self):
        """Create a new user account."""
        super().save()
        pw = self.validated_data['password']
        email = self.validated_data['email']
        username = self.generate_username(email)
        account = User(email=email, username=username, is_active=False)
        account.set_password(pw)
        account.save()
        return account


class LoginSerializer(TokenObtainPairSerializer):
    """
    Custom serializer for user login using email and password.
    Validates the credentials and returns JWT tokens along with user info.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        """Initialize LoginSerializer."""
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username']

    def validate(self, attrs):
        """Validate user credentials."""
        email = attrs.get('email')
        password = attrs.get('password')

        user = self._check_user_exist(email)
        self._check_password(user, password)

        attrs['username'] = user.username
        data = super().validate(attrs)
        data['user'] = {
            'id': user.id,
            'username': user.username
        }
        return data

    def _check_user_exist(self, email):
        """Return user if exists, else raise ValidationError."""
        try:
            user = User.objects.get(email=email)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

    def _check_password(self, user, password) -> None:
        """Raise ValidationError if password is incorrect."""
        if not user.check_password(password):
            raise serializers.ValidationError("Incorrect password.")


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for requesting a password reset."""
    email = serializers.EmailField()

    def validate_email(self, value):
        """Check if user exists and return user instance."""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class PasswordConfirmSerializer(serializers.Serializer):
    """Serializer for confirming and setting a new password."""
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_confirm_password(self, value):
        """Check if confirm password matches new password."""
        new_password = self.initial_data.get('new_password')
        if new_password and value and new_password != value:
            raise serializers.ValidationError("Passwords do not match.")
        return value

    def validate_new_password(self, value):
        """Check if new password is different from old password."""
        user = self.context.get('user')
        if user and user.check_password(value):
            raise serializers.ValidationError("New password must not be the same as the old password.")
        return value
