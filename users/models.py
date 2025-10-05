from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Permission, Group
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class UserRole(models.TextChoices):
    """User role choices."""
    ADMIN = 'admin', _('Admin')
    STAFF = 'staff', _('Staff')
    SELLER = 'seller', _('Seller')
    CLIENT = 'client', _('Client')
    USER = 'user', _('User')


class User(AbstractUser):
    """Custom User model with email as the unique identifier and role-based permissions."""
    username = None
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.USER,
    )
    is_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    
    # 2FA fields
    is_2fa_enabled = models.BooleanField(default=False)
    otp_secret = models.CharField(max_length=16, blank=True, null=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    otp_attempts = models.PositiveSmallIntegerField(default=0)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the user's full name."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email
    
    def is_admin(self):
        """Check if the user is an admin."""
        return self.role == UserRole.ADMIN or self.is_superuser
    
    def is_staff_member(self):
        """Check if the user is a staff member."""
        return self.role == UserRole.STAFF or self.is_staff
    
    def is_seller(self):
        """Check if the user is a seller."""
        return self.role == UserRole.SELLER
    
    def is_client(self):
        """Check if the user is a client."""
        return self.role == UserRole.CLIENT
    
    def generate_email_verification_token(self):
        """Generate a new email verification token."""
        self.email_verification_token = uuid.uuid4()
        self.email_verification_sent_at = timezone.now()
        self.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
        return self.email_verification_token
    
    def verify_email(self):
        """Mark the user's email as verified."""
        self.is_verified = True
        self.email_verification_token = None
        self.email_verification_sent_at = None
        self.save(update_fields=['is_verified', 'email_verification_token', 'email_verification_sent_at'])
    
    def generate_otp(self):
        """Generate a new OTP for 2FA."""
        import random
        import string
        
        # Generate a 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Store the OTP hash
        self.otp_secret = otp
        self.otp_created_at = timezone.now()
        self.otp_attempts = 0
        self.save(update_fields=['otp_secret', 'otp_created_at', 'otp_attempts'])
        
        return otp
    
    def verify_otp(self, otp):
        """Verify the OTP for 2FA."""
        # Check if OTP is expired (10 minutes)
        if not self.otp_created_at or (timezone.now() - self.otp_created_at).total_seconds() > 600:
            return False
        
        # Check if too many attempts
        if self.otp_attempts >= 5:
            return False
        
        # Increment attempts
        self.otp_attempts += 1
        self.save(update_fields=['otp_attempts'])
        
        # Check if OTP matches
        return self.otp_secret == otp


class UserProfile(models.Model):
    """Extended profile information for users."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    social_media_links = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}'s Profile"
