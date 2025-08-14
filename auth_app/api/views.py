from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .serializers import RegisterSerializer, LoginSerializer
from auth_app.tasks import send_activation_email

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        data = {}
        if serializer.is_valid():
            saved_account = serializer.save()
            uid = urlsafe_base64_encode(force_bytes(saved_account.pk))
            token = default_token_generator.make_token(saved_account)
            current_site = get_current_site(self.request)
            activation_link = (
                f"http://{current_site.domain}"
                f"{reverse('activate', kwargs={'uidb64': uid, 'token': token})}"
            )
            send_activation_email(saved_account.email, activation_link)
            data = {
                "user": {
                    "id": saved_account.pk,
                    "email": saved_account.email
                },
                "token": token
            }
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivateAccountView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({"message": "Account activated successfully."}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid activation link."}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            data = response.data
            refresh = data.get("refresh")
            access = data.get("access")
            user = data.get("user")
            response = Response({
                "detail": "Login successful",
                "user": user
            }, status=status.HTTP_200_OK)
            response.set_cookie(
                key='refresh_token',
                value=refresh,
                httponly=True,
                secure=True,
                samesite='Lax'
            )
            response.set_cookie(
                key='access_token',
                value=access,
                httponly=True,
                secure=True,
                samesite='Lax'
            )
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token is None:
            return Response({"detail": "Refresh token not found."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Token invalid"}, status=status.HTTP_400_BAD_REQUEST)
        
        response = Response({"detail": "Logout successful"}, status=status.HTTP_200_OK)
        response.delete_cookie('refresh_token')
        response.delete_cookie('access_token')
        return response
