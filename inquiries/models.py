from django.db import models
from django.conf import settings
from listings.models import VehicleListing


class InquiryStatus(models.TextChoices):
    NEW = 'new', 'New'
    IN_PROGRESS = 'in_progress', 'In Progress'
    RESPONDED = 'responded', 'Responded'
    CLOSED = 'closed', 'Closed'
    SPAM = 'spam', 'Spam'


class InquiryType(models.TextChoices):
    GENERAL = 'general', 'General Inquiry'
    PRICE = 'price', 'Price Inquiry'
    TEST_DRIVE = 'test_drive', 'Test Drive Request'
    FINANCING = 'financing', 'Financing Inquiry'
    AVAILABILITY = 'availability', 'Availability Check'


class ListingInquiry(models.Model):
    """Model for user inquiries about vehicle listings."""
    listing = models.ForeignKey(VehicleListing, on_delete=models.CASCADE, related_name='inquiries')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_inquiries', null=True, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    inquiry_type = models.CharField(max_length=20, choices=InquiryType.choices, default=InquiryType.GENERAL)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=InquiryStatus.choices, default=InquiryStatus.NEW)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Listing Inquiry'
        verbose_name_plural = 'Listing Inquiries'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['inquiry_type']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"Inquiry from {self.name} about {self.listing.title}"


class InquiryResponse(models.Model):
    """Model for responses to listing inquiries."""
    inquiry = models.ForeignKey(ListingInquiry, on_delete=models.CASCADE, related_name='responses')
    responder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_responses')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
    
    def save(self, *args, **kwargs):
        # Update the parent inquiry status when a response is added
        if self.inquiry.status == InquiryStatus.NEW or self.inquiry.status == InquiryStatus.IN_PROGRESS:
            self.inquiry.status = InquiryStatus.RESPONDED
            self.inquiry.save(update_fields=['status'])
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Response to {self.inquiry} by {self.responder.email}"


class TestDriveRequest(models.Model):
    """Model for test drive requests."""
    inquiry = models.OneToOneField(ListingInquiry, on_delete=models.CASCADE, related_name='test_drive_details')
    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    alternate_date = models.DateField(blank=True, null=True)
    alternate_time = models.TimeField(blank=True, null=True)
    location_preference = models.CharField(max_length=100, blank=True, null=True, 
                                         help_text='Preferred location for the test drive')
    additional_notes = models.TextField(blank=True, null=True)
    is_confirmed = models.BooleanField(default=False)
    confirmation_date = models.DateTimeField(blank=True, null=True)
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name='confirmed_test_drives')
    
    class Meta:
        ordering = ['preferred_date', 'preferred_time']
    
    def __str__(self):
        return f"Test drive request for {self.inquiry.listing.title} on {self.preferred_date}"
