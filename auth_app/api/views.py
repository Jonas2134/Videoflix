from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token


class RegisterView(generics.CreateAPIView):
    pass
