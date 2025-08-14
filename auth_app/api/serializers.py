import random
import string
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'confirmed_password')
        extra_kwargs = {
            'password': {'write_only': True},
            'confirmed_password': {'write_only': True}
        }

    def validate_confirmed_password(self, value):
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError("Passwords do not match.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def generate_username(self, email):
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
        pw = self.validated_data['password']
        email = self.validated_data['email']
        username = self.generate_username(email)
        account = User(email=email, username=username, is_active=False)
        account.set_password(pw)
        account.save()
        return account


class LoginSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username']

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        if not user.check_password(password):
            raise serializers.ValidationError("Incorrect password.")

        attrs['username'] = user.username
        data = super().validate(attrs)
        data['user'] = {
            'id': user.id,
            'username': user.username
        }
        return data
