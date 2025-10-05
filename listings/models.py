from django.db import models
from django.utils.text import slugify
from django.conf import settings
from vehicles.models import VehicleSpecification, VehicleModel, Brand


class ListingStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PENDING = 'pending', 'Pending Approval'
    ACTIVE = 'active', 'Active'
    SOLD = 'sold', 'Sold'
    EXPIRED = 'expired', 'Expired'
    REJECTED = 'rejected', 'Rejected'


class ConditionType(models.TextChoices):
    NEW = 'new', 'New'
    USED = 'used', 'Used'
    CERTIFIED_PRE_OWNED = 'certified_pre_owned', 'Certified Pre-Owned'


class PriceType(models.TextChoices):
    FIXED = 'fixed', 'Fixed Price'
    NEGOTIABLE = 'negotiable', 'Negotiable'
    CALL = 'call', 'Call for Price'


class VehicleListing(models.Model):
    """Vehicle listing model for selling vehicles."""
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listings')
    vehicle_specification = models.ForeignKey(VehicleSpecification, on_delete=models.CASCADE, related_name='listings')
    condition = models.CharField(max_length=20, choices=ConditionType.choices, default=ConditionType.USED)
    mileage = models.PositiveIntegerField(help_text='Vehicle mileage in kilometers')
    price = models.DecimalField(max_digits=12, decimal_places=2)
    price_type = models.CharField(max_length=20, choices=PriceType.choices, default=PriceType.FIXED)
    location_city = models.CharField(max_length=100)
    location_state = models.CharField(max_length=100, blank=True, null=True)
    location_country = models.CharField(max_length=100)
    description = models.TextField()
    color_exterior = models.CharField(max_length=50, blank=True, null=True)
    color_interior = models.CharField(max_length=50, blank=True, null=True)
    vin = models.CharField(max_length=17, blank=True, null=True, verbose_name='VIN')
    status = models.CharField(max_length=20, choices=ListingStatus.choices, default=ListingStatus.DRAFT)
    is_featured = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    warranty_information = models.TextField(blank=True, null=True)
    additional_features = models.TextField(blank=True, null=True)
    seller_notes = models.TextField(blank=True, null=True)
    views_count = models.PositiveIntegerField(default=0)
    inquiries_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
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
            models.Index(fields=['location_city', 'location_country']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.vehicle_specification.model.brand.name}-{self.vehicle_specification.model.name}-{self.vehicle_specification.year}")
            self.slug = f"{base_slug}-{self.id if self.id else ''}"  # Will be updated after save if new
        super().save(*args, **kwargs)
        
        # Update slug with ID for new listings
        if not self.slug.endswith(str(self.id)):
            self.slug = f"{slugify(f"{self.vehicle_specification.model.brand.name}-{self.vehicle_specification.model.name}-{self.vehicle_specification.year}")}-{self.id}"
            super().save(update_fields=['slug'])

    def __str__(self):
        return self.title


from io import BytesIO
from PIL import Image as PILImage
from django.core.files.base import ContentFile
import os


class ListingImage(models.Model):
    """Images for vehicle listings."""
    listing = models.ForeignKey(VehicleListing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listings/images/')
    thumbnail = models.ImageField(upload_to='listings/thumbnails/', blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    caption = models.CharField(max_length=255, blank=True, null=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Image for {self.listing.title}"
    
    def save(self, *args, **kwargs):
        # Only process if the image is being saved for the first time
        if not self.id:
            self.compress_image()
            self.create_thumbnail()
        super().save(*args, **kwargs)
    
    def compress_image(self, quality=85):
        # Open the image using PIL
        img = PILImage.open(self.image)
        
        # Convert to RGB if image is in RGBA mode
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # Set a maximum size (e.g., 1920x1080)
        max_width = 1920
        max_height = 1080
        
        # Resize if larger than maximum size while maintaining aspect ratio
        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), PILImage.LANCZOS)
        
        # Save the compressed image
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        # Get the file name and extension
        file_name, file_ext = os.path.splitext(os.path.basename(self.image.name))
        new_name = f"{file_name}_compressed.jpg"
        
        # Save the compressed image back to the model field
        self.image.save(new_name, ContentFile(output.read()), save=False)
    
    def create_thumbnail(self, size=(300, 200)):
        # Open the image using PIL
        img = PILImage.open(self.image)
        
        # Convert to RGB if image is in RGBA mode
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # Create thumbnail
        img.thumbnail(size, PILImage.LANCZOS)
        
        # Save the thumbnail
        output = BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        
        # Get the file name and extension
        file_name, file_ext = os.path.splitext(os.path.basename(self.image.name))
        thumb_name = f"{file_name}_thumb.jpg"
        
        # Save the thumbnail back to the model field
        self.thumbnail.save(thumb_name, ContentFile(output.read()), save=False)


class SavedListing(models.Model):
    """Saved/favorited listings by users."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_listings')
    listing = models.ForeignKey(VehicleListing, on_delete=models.CASCADE, related_name='saved_by')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'listing']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} saved {self.listing.title}"


class ListingView(models.Model):
    """Track listing views by users."""
    listing = models.ForeignKey(VehicleListing, on_delete=models.CASCADE, related_name='listing_views')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']

    def __str__(self):
        return f"View of {self.listing.title} at {self.viewed_at}"
