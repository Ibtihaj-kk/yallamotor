from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import UserProfile, UserRole
from .serializers import (
    UserSerializer, 
    UserRegistrationSerializer,
    UserUpdateSerializer,
    PasswordChangeSerializer,
    UserProfileSerializer,
    CustomTokenObtainPairSerializer,
    VerifyOTPSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)
from core.permissions import IsAdminUser, IsOwnerOrAdmin

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """View for user registration."""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send verification email
        self.send_verification_email(user)
        
        # Generate tokens for the user
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user, context=self.get_serializer_context()).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'User registered successfully. Please verify your email.'
        }, status=status.HTTP_201_CREATED)
    
    def send_verification_email(self, user):
        """Send verification email to the user."""
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{user.email_verification_token}/"
        
        # In a real app, you would use a template and send a proper HTML email
        subject = 'Verify your email address'
        html_message = f'''
        <html>
            <body>
                <h2>Welcome to YallaMotor!</h2>
                <p>Thank you for registering. Please click the link below to verify your email address:</p>
                <p><a href="{verification_url}">Verify Email</a></p>
                <p>This link will expire in 24 hours.</p>
                <p>If you did not register for a YallaMotor account, please ignore this email.</p>
            </body>
        </html>
        '''
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            # Log the error but don't prevent user registration
            print(f"Error sending verification email: {e}")


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token view that uses our serializer."""
    serializer_class = CustomTokenObtainPairSerializer


class VerifyOTPView(generics.GenericAPIView):
    """View for OTP verification."""
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Clear OTP after successful verification
        user.otp_secret = None
        user.otp_created_at = None
        user.otp_attempts = 0
        user.save(update_fields=['otp_secret', 'otp_created_at', 'otp_attempts'])
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        })


class EmailVerificationView(generics.GenericAPIView):
    """View for email verification."""
    serializer_class = EmailVerificationSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        user.verify_email()
        
        return Response({
            'message': 'Email verified successfully.'
        })


class PasswordResetRequestView(generics.GenericAPIView):
    """View for password reset request."""
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            # Generate token
            token = user.generate_email_verification_token()
            
            # Send reset email
            self.send_reset_email(user, token)
            
            return Response({
                'message': 'Password reset email sent.'
            })
        except User.DoesNotExist:
            # Don't reveal that the user doesn't exist
            return Response({
                'message': 'Password reset email sent if the email exists.'
            })
    
    def send_reset_email(self, user, token):
        """Send password reset email to the user."""
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}/"
        
        subject = 'Reset your password'
        html_message = f'''
        <html>
            <body>
                <h2>Password Reset</h2>
                <p>You requested a password reset. Please click the link below to reset your password:</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                <p>This link will expire in 24 hours.</p>
                <p>If you did not request a password reset, please ignore this email.</p>
            </body>
        </html>
        '''
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            # Log the error
            print(f"Error sending reset email: {e}")


class PasswordResetConfirmView(generics.GenericAPIView):
    """View for password reset confirmation."""
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        password = serializer.validated_data['password']
        
        # Set new password
        user.set_password(password)
        
        # Clear token
        user.email_verification_token = None
        user.email_verification_sent_at = None
        
        user.save()
        
        return Response({
            'message': 'Password reset successfully.'
        })


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user operations."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return all users for staff/admin, only the current user for others."""
        user = self.request.user
        if user.is_admin() or user.is_staff_member():
            return User.objects.all()
        return User.objects.filter(id=user.id)
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrAdmin]
        elif self.action == 'create':
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Return the current user's profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        """Change user's password."""
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def enable_2fa(self, request):
        """Enable 2FA for the user."""
        user = request.user
        
        if user.is_2fa_enabled:
            return Response({'message': '2FA is already enabled.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate OTP
        otp = user.generate_otp()
        user.is_2fa_enabled = True
        user.save(update_fields=['is_2fa_enabled'])
        
        # In a real app, send OTP via email or SMS here
        try:
            subject = 'Your 2FA Setup Code'
            message = f'Your verification code is: {otp}. It will expire in 10 minutes.'
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            # Log the error
            print(f"Error sending 2FA setup email: {e}")
        
        return Response({
            'message': '2FA enabled successfully. Please verify with the OTP sent to your email.'
        })
    
    @action(detail=False, methods=['post'])
    def disable_2fa(self, request):
        """Disable 2FA for the user."""
        user = request.user
        
        if not user.is_2fa_enabled:
            return Response({'message': '2FA is not enabled.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_2fa_enabled = False
        user.otp_secret = None
        user.otp_created_at = None
        user.otp_attempts = 0
        user.save()
        
        return Response({'message': '2FA disabled successfully.'})
    
    @action(detail=False, methods=['post'])
    def upload_profile_picture(self, request):
        """Upload a profile picture."""
        if 'profile_picture' not in request.FILES:
            return Response({'profile_picture': ['No file was submitted.']}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        user.profile_picture = request.FILES['profile_picture']
        user.save()
        
        return Response({
            'message': 'Profile picture uploaded successfully.',
            'profile_picture': request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None
        })
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Blacklist the refresh token to logout."""
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
