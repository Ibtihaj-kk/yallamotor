from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils import timezone
from vehicles.models import VehicleSpecification, VehicleModel, Brand, FuelType, TransmissionType
from PIL import Image
import uuid
import os
from .validators import (
    validate_image_size, validate_video_size,
    validate_image_type, validate_video_type,
    validate_image_dimensions
)


class ListingStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PENDING_REVIEW = 'pending_review', 'Pending Review'
    PUBLISHED = 'published', 'Published'
    SOLD = 'sold', 'Sold'
    REJECTED = 'rejected', 'Rejected'
    EXPIRED = 'expired', 'Expired'
    SUSPENDED = 'suspended', 'Suspended'


class ConditionType(models.TextChoices):
    NEW = 'new', 'New'
    USED = 'used', 'Used'
    CERTIFIED_PRE_OWNED = 'certified_pre_owned', 'Certified Pre-Owned'


class PriceType(models.TextChoices):
    FIXED = 'fixed', 'Fixed Price'
    NEGOTIABLE = 'negotiable', 'Negotiable'
    CALL = 'call', 'Call for Price'


def get_upload_path(instance, filename):
    """Generate upload path for listing media files."""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('listings', str(instance.listing.id), filename)


class VehicleListing(models.Model):
    """Vehicle listing model for selling vehicles."""
    # Required fields
    title = models.CharField(max_length=255, help_text='Vehicle listing title')
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listings')
    description = models.TextField(help_text='Detailed description of the vehicle')
    price = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Vehicle price'
    )
    
    # Vehicle details (required)
    year = models.PositiveIntegerField(
        default=2020,
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(timezone.now().year + 2)
        ],
        help_text='Vehicle year'
    )
    make = models.CharField(max_length=100, default="Unknown", help_text='Vehicle make/brand')
    model = models.CharField(max_length=100, default="Unknown", help_text='Vehicle model')
    
    # Vehicle specifications
    kilometers = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Vehicle mileage in kilometers'
    )
    fuel_type = models.CharField(
        max_length=20,
        choices=[
            ('gasoline', 'Gasoline'),
            ('diesel', 'Diesel'),
            ('electric', 'Electric'),
            ('hybrid', 'Hybrid'),
            ('plug_in_hybrid', 'Plug-in Hybrid'),
            ('lpg', 'LPG'),
            ('cng', 'CNG'),
        ],
        default='gasoline',
        help_text='Vehicle fuel type'
    )
    condition = models.CharField(
        max_length=20, 
        choices=ConditionType.choices, 
        default=ConditionType.USED,
        help_text='Vehicle condition'
    )
    transmission = models.CharField(
        max_length=20,
        choices=[
            ('automatic', 'Automatic'),
            ('manual', 'Manual'),
            ('cvt', 'CVT'),
            ('semi_automatic', 'Semi-Automatic'),
        ],
        default='manual',
        help_text='Vehicle transmission type'
    )
    color = models.CharField(max_length=50, default="White", help_text='Vehicle color')
    
    # Additional vehicle details
    color_interior = models.CharField(max_length=50, blank=True, null=True)
    vin = models.CharField(max_length=17, blank=True, null=True, verbose_name='VIN')
    engine_size = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True, help_text='Engine size in liters')
    doors = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MinValueValidator(2), MaxValueValidator(6)])
    seats = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    
    # Listing management
    status = models.CharField(max_length=20, choices=ListingStatus.choices, default=ListingStatus.DRAFT)
    rejection_reason = models.TextField(blank=True, null=True, help_text='Admin feedback for rejected listings')
    
    # Location
    location_city = models.CharField(max_length=100)
    location_state = models.CharField(max_length=100, blank=True, null=True)
    location_country = models.CharField(max_length=100, default='UAE')
    
    # Additional features
    warranty_information = models.TextField(blank=True, null=True)
    additional_features = models.TextField(blank=True, null=True)
    seller_notes = models.TextField(blank=True, null=True)
    
    # Listing metadata
    is_featured = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    inquiries_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    # SEO fields
    meta_title = models.CharField(max_length=255, blank=True, null=True, help_text='Custom title for SEO purposes')
    meta_description = models.TextField(blank=True, null=True, help_text='Custom description for SEO purposes')
    meta_keywords = models.CharField(max_length=255, blank=True, null=True, help_text='Keywords for SEO purposes')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['is_premium']),
            models.Index(fields=['condition']),
            models.Index(fields=['fuel_type']),
            models.Index(fields=['transmission']),
            models.Index(fields=['make', 'model']),
            models.Index(fields=['year']),
            models.Index(fields=['price']),
            models.Index(fields=['kilometers']),
            models.Index(fields=['location_city', 'location_country']),
            models.Index(fields=['created_at']),
            models.Index(fields=['published_at']),
        ]

    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            base_slug = slugify(f"{self.make}-{self.model}-{self.year}")
            self.slug = f"{base_slug}-{self.id if self.id else ''}"
        
        # Set published_at when status changes to published
        if self.status == ListingStatus.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Update slug with ID for new listings
        if not self.slug.endswith(str(self.id)):
            self.slug = f"{slugify(f"{self.make}-{self.model}-{self.year}")}-{self.id}"
            super().save(update_fields=['slug'])

    def __str__(self):
        return self.title
    
    @property
    def is_published(self):
        """Check if listing is published and visible to public."""
        return self.status == ListingStatus.PUBLISHED
    
    @property
    def primary_image(self):
        """Get the primary image for this listing."""
        return self.images.filter(is_primary=True).first()
    
    @property
    def all_images(self):
        """Get all images ordered by primary first, then by order."""
        return self.images.all().order_by('-is_primary', 'order')
    
    def increment_views(self):
        """Increment the views count."""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def increment_inquiries(self):
        """Increment inquiry count."""
        self.inquiries_count += 1
        self.save(update_fields=['inquiries_count'])
    
    # Workflow methods
    def can_transition_to(self, status):
        """Check if this listing can transition to the given status."""
        from .status_manager import ListingStatusManager
        return ListingStatusManager.can_transition(self.status, status)
    
    def get_allowed_transitions(self):
        """Get allowed status transitions for this listing."""
        from .status_manager import ListingStatusManager
        return ListingStatusManager.get_allowed_transitions(self.status)
    
    def change_status(self, new_status, user=None, reason=None):
        """Change status of this listing."""
        from .status_manager import ListingStatusManager
        return ListingStatusManager.change_status(self, new_status, user, reason)
    
    def publish(self, user=None):
        """Publish this listing."""
        return self.change_status(ListingStatus.PUBLISHED, user)
    
    def reject(self, reason, user=None):
        """Reject this listing with a reason."""
        return self.change_status(ListingStatus.REJECTED, user, reason)
    
    def mark_as_sold(self, user=None):
        """Mark this listing as sold."""
        return self.change_status(ListingStatus.SOLD, user)
    
    def suspend(self, reason=None, user=None):
        """Suspend this listing."""
        return self.change_status(ListingStatus.SUSPENDED, user, reason)
    
    @property
    def is_editable(self):
        """Check if listing can be edited in current status."""
        return self.status in [ListingStatus.DRAFT, ListingStatus.REJECTED]
    
    @property
    def is_public(self):
        """Check if listing is visible to public."""
        return self.status == ListingStatus.PUBLISHED
    
    @property
    def needs_review(self):
        """Check if listing needs admin review."""
        return self.status == ListingStatus.PENDING_REVIEW


from io import BytesIO
from PIL import Image as PILImage
from django.core.files.base import ContentFile
import os


class ListingImage(models.Model):
    """Image model for vehicle listings with automatic optimization."""
    listing = models.ForeignKey(VehicleListing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(
        upload_to=get_upload_path,
        validators=[
            validate_image_size,
            validate_image_type,
            validate_image_dimensions,
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif'])
        ],
        help_text='Supported formats: JPEG, PNG, WebP, GIF. Max size: 10MB. Min dimensions: 400x300px'
    )
    # Multiple thumbnail sizes for different use cases
    thumbnail = models.ImageField(upload_to='listings/thumbnails/', blank=True, null=True)  # 300x300
    thumbnail_small = models.ImageField(upload_to='listings/thumbnails/small/', blank=True, null=True)  # 150x150
    thumbnail_medium = models.ImageField(upload_to='listings/thumbnails/medium/', blank=True, null=True)  # 600x400
    
    # WebP versions for better compression
    image_webp = models.ImageField(upload_to='listings/webp/', blank=True, null=True)
    thumbnail_webp = models.ImageField(upload_to='listings/thumbnails/webp/', blank=True, null=True)
    
    is_primary = models.BooleanField(default=False)
    caption = models.CharField(max_length=255, blank=True, null=True)
    order = models.PositiveSmallIntegerField(default=0)
    file_size = models.PositiveIntegerField(blank=True, null=True, help_text='File size in bytes')
    width = models.PositiveIntegerField(blank=True, null=True)
    height = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', 'order', 'created_at']
        indexes = [
            models.Index(fields=['listing', 'is_primary']),
            models.Index(fields=['listing', 'order']),
        ]

    def save(self, *args, **kwargs):
        # Ensure only one primary image per listing
        if self.is_primary:
            ListingImage.objects.filter(listing=self.listing, is_primary=True).update(is_primary=False)
        
        # Optimize and process image if it's new or changed
        if self.image and (not self.pk or 'image' in kwargs.get('update_fields', [])):
            self._optimize_main_image()
        
        # Set file metadata
        if self.image:
            self.file_size = self.image.size
            if hasattr(self.image, 'width') and hasattr(self.image, 'height'):
                self.width = self.image.width
                self.height = self.image.height
        
        super().save(*args, **kwargs)
        
        # Generate all thumbnails and WebP versions if not exists
        if self.image and not self.thumbnail:
            self._generate_all_thumbnails()

    def _optimize_main_image(self):
        """Optimize the main image for web delivery."""
        if not self.image:
            return
        
        try:
            # Open the image
            image = PILImage.open(self.image)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Get settings from Django settings
            max_width = getattr(settings, 'IMAGE_MAX_WIDTH', 1920)
            max_height = getattr(settings, 'IMAGE_MAX_HEIGHT', 1080)
            quality = getattr(settings, 'IMAGE_QUALITY', 85)
            
            # Resize if image is too large
            if image.width > max_width or image.height > max_height:
                image.thumbnail((max_width, max_height), PILImage.Resampling.LANCZOS)
            
            # Save optimized image
            img_io = BytesIO()
            image.save(img_io, format='JPEG', quality=quality, optimize=True)
            img_io.seek(0)
            
            # Replace the original image with optimized version
            name, ext = os.path.splitext(os.path.basename(self.image.name))
            optimized_filename = f"{name}_optimized.jpg"
            
            self.image.save(
                optimized_filename,
                ContentFile(img_io.read()),
                save=False
            )
            
        except Exception as e:
            print(f"Error optimizing main image: {e}")

    def _generate_all_thumbnails(self):
        """Generate all thumbnail sizes and WebP versions."""
        if not self.image:
            return
        
        try:
            # Open the image
            image = PILImage.open(self.image.path)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Generate different thumbnail sizes
            self._create_thumbnail_size(image, 'thumbnail', (300, 300))
            self._create_thumbnail_size(image, 'thumbnail_small', (150, 150))
            self._create_thumbnail_size(image, 'thumbnail_medium', (600, 400))
            
            # Generate WebP versions
            self._create_webp_version(image, 'image_webp', None)  # Full size WebP
            self._create_webp_version(image, 'thumbnail_webp', (300, 300))  # Thumbnail WebP
            
            # Save all changes
            super().save(update_fields=['thumbnail', 'thumbnail_small', 'thumbnail_medium', 'image_webp', 'thumbnail_webp'])
            
        except Exception as e:
            print(f"Error generating thumbnails: {e}")

    def _create_thumbnail_size(self, image, field_name, size):
        """Create a thumbnail of specific size."""
        try:
            # Create a copy of the image for this thumbnail
            thumb_image = image.copy()
            thumb_image.thumbnail(size, PILImage.Resampling.LANCZOS)
            
            # Save thumbnail
            thumb_io = BytesIO()
            thumb_image.save(thumb_io, format='JPEG', quality=85, optimize=True)
            thumb_io.seek(0)
            
            # Generate thumbnail filename
            name, ext = os.path.splitext(os.path.basename(self.image.name))
            thumb_filename = f"{name}_{size[0]}x{size[1]}.jpg"
            
            # Save thumbnail to the specified field
            field = getattr(self, field_name)
            field.save(
                thumb_filename,
                ContentFile(thumb_io.read()),
                save=False
            )
            
        except Exception as e:
            print(f"Error creating {field_name} thumbnail: {e}")

    def _create_webp_version(self, image, field_name, size=None):
        """Create WebP version for better compression."""
        try:
            # Create a copy of the image
            webp_image = image.copy()
            
            # Resize if size is specified
            if size:
                webp_image.thumbnail(size, PILImage.Resampling.LANCZOS)
            
            # Save as WebP
            webp_io = BytesIO()
            webp_image.save(webp_io, format='WebP', quality=80, optimize=True)
            webp_io.seek(0)
            
            # Generate WebP filename
            name, ext = os.path.splitext(os.path.basename(self.image.name))
            size_suffix = f"_{size[0]}x{size[1]}" if size else ""
            webp_filename = f"{name}{size_suffix}.webp"
            
            # Save WebP to the specified field
            field = getattr(self, field_name)
            field.save(
                webp_filename,
                ContentFile(webp_io.read()),
                save=False
            )
            
        except Exception as e:
            print(f"Error creating {field_name} WebP: {e}")

    def create_thumbnail(self):
        """Legacy method for backward compatibility - now calls the enhanced version."""
        self._generate_all_thumbnails()

    def get_optimized_image_url(self, prefer_webp=True):
        """Get the best optimized image URL based on browser support."""
        if prefer_webp and self.image_webp:
            return self.image_webp.url
        return self.image.url if self.image else None

    def get_thumbnail_url(self, size='medium', prefer_webp=True):
        """Get thumbnail URL for specified size."""
        if prefer_webp and self.thumbnail_webp:
            return self.thumbnail_webp.url
        
        if size == 'small' and self.thumbnail_small:
            return self.thumbnail_small.url
        elif size == 'medium' and self.thumbnail_medium:
            return self.thumbnail_medium.url
        elif self.thumbnail:
            return self.thumbnail.url
        
        return self.get_optimized_image_url(prefer_webp=False)

    def __str__(self):
        return f"Image for {self.listing.title}"


class ListingVideo(models.Model):
    """Videos for vehicle listings."""
    listing = models.ForeignKey(VehicleListing, on_delete=models.CASCADE, related_name='videos')
    video = models.FileField(
        upload_to=get_upload_path,
        validators=[
            validate_video_size,
            validate_video_type,
            FileExtensionValidator(allowed_extensions=['mp4', 'mov', 'avi', 'webm'])
        ],
        help_text='Supported formats: MP4, MOV, AVI, WebM. Max size: 100MB'
    )
    thumbnail = models.ImageField(upload_to='listings/video_thumbnails/', blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    duration = models.PositiveIntegerField(blank=True, null=True, help_text='Duration in seconds')
    file_size = models.PositiveIntegerField(blank=True, null=True, help_text='File size in bytes')
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['listing', 'order']),
        ]

    def save(self, *args, **kwargs):
        # Set file size
        if self.video:
            self.file_size = self.video.size
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Video for {self.listing.title}"


class SavedListing(models.Model):
    """User saved listings."""
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='saved_listings')
    listing = models.ForeignKey(VehicleListing, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'listing']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['listing']),
        ]

    def __str__(self):
        return f"{self.user.username} saved {self.listing.title}"


class ListingView(models.Model):
    """Track listing views."""
    listing = models.ForeignKey(VehicleListing, on_delete=models.CASCADE, related_name='listing_views')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    referrer = models.URLField(blank=True, null=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['listing', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
        ]

    def __str__(self):
        return f"View of {self.listing.title} at {self.created_at}"


class ListingStatusLog(models.Model):
    """Log status changes for audit trail."""
    listing = models.ForeignKey(VehicleListing, on_delete=models.CASCADE, related_name='status_logs')
    old_status = models.CharField(max_length=20, choices=ListingStatus.choices)
    new_status = models.CharField(max_length=20, choices=ListingStatus.choices)
    changed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['listing', 'timestamp']),
            models.Index(fields=['changed_by', 'timestamp']),
            models.Index(fields=['new_status', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.listing.title}: {self.old_status} → {self.new_status}"
