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

from .serializers import RegisterSerializer, LoginSerializer, PasswordResetSerializer, PasswordConfirmSerializer
from auth_app.tasks import send_activation_email, send_password_reset_email

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            saved_account = serializer.save()
            uid = urlsafe_base64_encode(force_bytes(saved_account.pk))
            token = default_token_generator.make_token(saved_account)
            current_site = get_current_site(self.request)
            activation_link = (
                f"http://{current_site.domain}"
                f"{reverse('activate', kwargs={'uidb64': uid, 'token': token})}"
            )
            send_activation_email(self.request, saved_account, activation_link)
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
    permission_classes = [IsAuthenticated]

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


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token is None:
            return Response({"detail": "Refresh token not found."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data={"refresh":refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_401_UNAUTHORIZED)
        access_token = serializer.validated_data.get("access")
        response = Response({"access": "Access Token refreshed successfully."}, status=status.HTTP_200_OK)
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=True,
            samesite='Lax'
        )
        return response


class PasswordResetView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        current_site = get_current_site(self.request)
        reset_link = (
            f"http://{current_site.domain}"
            f"{reverse('password_confirm', kwargs={'uidb64': uid, 'token': token})}"
        )
        send_password_reset_email(self.request, email, reset_link)
        return Response({"detail": "An email has been sent to reset your password."}, status=status.HTTP_200_OK)


class PasswordConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordConfirmSerializer

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"detail": "Invalid user."}, status=status.HTTP_400_BAD_REQUEST)

        if user is None or not default_token_generator.check_token(user, token):
            return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data, context={'user': user})
        if not serializer.is_valid():
            return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return Response({"detail": "Your Password has been successfully reset."}, status=status.HTTP_200_OK)
