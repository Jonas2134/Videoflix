from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .serializers import RegisterSerializer, LoginSerializer, PasswordResetSerializer, PasswordConfirmSerializer
from auth_app.tasks import send_email
from auth_app.utils import build_link

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """
    API view for user registration.

    On successful registration, sends an activation email to the user.

    Attributes:
        permission_classes (list): The permission classes for the view.
        serializer_class (RegisterSerializer): The serializer class for user registration.
    """
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        """
        Handle POST to user registration.

        1. Validate the request data using the serializer.
        2. If valid, save the new user account.
        3. Send an activation email to the user.
        4. Return a success response with user details.

        Returns:
            Response: The response containing user details or errors.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            saved_account = serializer.save()
            activation_link, token = build_link(saved_account, 'pages/auth/activate.html')
            try:
                send_email(
                    user=saved_account,
                    subject="Activate your account",
                    template_name="activation_email.html",
                    context={
                        "username": saved_account.username,
                        "activation_link": activation_link,
                    }
                )
            except Exception as e:
                return Response({"error": f"Failed to send activation email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
    """
    API view for activating user accounts.
    Activates the user account if the provided token is valid.

    Attributes:
        permission_classes (list): The permission classes for the view.
    """
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        """
        Handle GET request to activate user account.
    
        1. Decode the user ID from the URL.
        2. Retrieve the user and validate the token.
        3. If valid, activate the user account.
        4. Return a success or error response.
    
        Returns:
            Response: The response indicating success or failure of activation.
        """
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
    """
    API view for user login.
    The parent class is TokenObtainPairView.
    The view handles user login and returns JWT tokens.
    The view uses the TokenObtainPairSerializer to validate user credentials.
    On successful login, sets the tokens in HttpOnly cookies.

    Attributes:
        serializer_class (Serializer): The serializer class for the view.
        permission_classes (list): The permission classes for the view.
    """
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Handle POST request for user login.

        1. Validate user credentials.
        2. If valid, generate JWT tokens.
        3. Set tokens in HttpOnly cookies.
        4. Return a success response with user details.

        Returns:
            Response: The response containing user details or errors.
        """
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            data = response.data
            refresh = data.get("refresh")
            access = data.get("access")
            user = data.get("user")
            response = Response({"detail": "Login successful", "user": user}, status=status.HTTP_200_OK)
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
    """
    API view for user logout.
    The view handles user logout and invalidates the refresh token.

    Attributes:
        permission_classes (list): The permission classes for the view.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Handle POST request for user logout.

        1. Retrieve the refresh token from cookies.
        2. If not found, return an error response.
        3. If found, blacklist the token or respond an error because the token is already invalid.
        4. Make an response with status 200.
        5. Delete the refresh and access tokens from cookies.
        6. Return the response.

        Returns:
            Response: The response containing logout status.
        """
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
    """API view for refreshing access tokens."""
    def post(self, request, *args, **kwargs):
        """
        Handle POST request for refreshing access tokens.

        1. Retrieve the refresh token from cookies.
        2. If not found, return an error response.
        3. If found, validate the token and generate a new access token.
        4. Set the new access token in an HttpOnly cookie.
        5. Return a success response with the new access token.

        Returns:
            Response: The response containing the new access token or errors.
        """
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
    """
    API view for password reset.
    Validates the user's email and sends a password reset link in an email.

    Attributes:
        permission_classes (list): The permission classes for the view.
        serializer_class (Serializer): The serializer class for validating input data.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    def post(self, request, *args, **kwargs):
        """
        Handle POST request for password reset.

        1. Validate the user's email.
        2. If valid, build a password reset link with a uidb64 and token.
        3. Send the reset link to the user's email.
        4. Return a success response or an error response.

        Returns:
            Response: The response containing the password reset status.
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        reset_link, token = build_link(user, 'pages/auth/confirm_password.html')
        try:
            send_email(
                user=user,
                subject="Reset your password",
                template_name="reset_password.html",
                context={
                    "username": user.username,
                    "reset_link": reset_link,
                }
            )
        except Exception as e:
            return Response({"error": f"Failed to send reset email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"detail": "An email has been sent to reset your password."}, status=status.HTTP_200_OK)


class PasswordConfirmView(generics.GenericAPIView):
    """
    API view for confirming password reset.
    Validates the user's credentials and resets the password.

    Attributes:
        permission_classes (list): The permission classes for the view.
        serializer_class (Serializer): The serializer class for validating input data.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordConfirmSerializer

    def post(self, request, uidb64, token):
        """
        Handle POST request for confirming password reset.

        1. Decode the uidb64 to get the user ID.
        2. Validate the token.
        3. If valid, reset the user's password.
        4. Return a success response or an error response.

        Returns:
            Response: The response containing the password reset confirmation status.
        """
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
