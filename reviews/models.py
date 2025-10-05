from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from vehicles.models import VehicleModel, Brand


class ReviewStatus(models.TextChoices):
    PENDING = 'pending', 'Pending Approval'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
    FLAGGED = 'flagged', 'Flagged for Review'


class VehicleReview(models.Model):
    """Model for user reviews of specific vehicle models."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vehicle_reviews')
    vehicle_model = models.ForeignKey(VehicleModel, on_delete=models.CASCADE, related_name='reviews')
    year = models.PositiveIntegerField(help_text='Year of the vehicle being reviewed')
    title = models.CharField(max_length=255)
    content = models.TextField()
    pros = models.TextField(blank=True, null=True, help_text='Positive aspects of the vehicle')
    cons = models.TextField(blank=True, null=True, help_text='Negative aspects of the vehicle')
    
    # Rating categories (1-5 scale)
    overall_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comfort_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True, null=True
    )
    performance_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True, null=True
    )
    reliability_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True, null=True
    )
    value_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True, null=True
    )
    fuel_economy_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True, null=True
    )
    
    # Review metadata
    status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING)
    is_verified_purchase = models.BooleanField(default=False)
    is_verified_owner = models.BooleanField(default=False)
    helpful_votes = models.PositiveIntegerField(default=0)
    unhelpful_votes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Vehicle Review'
        verbose_name_plural = 'Vehicle Reviews'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['overall_rating']),
            models.Index(fields=['is_verified_owner']),
        ]
        unique_together = ['user', 'vehicle_model', 'year']
    
    def __str__(self):
        return f"{self.title} - {self.vehicle_model.brand.name} {self.vehicle_model.name} {self.year}"


class DealerReview(models.Model):
    """Model for user reviews of car dealers."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dealer_reviews')
    dealer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_reviews',
                              limit_choices_to={'is_dealer': True})
    title = models.CharField(max_length=255)
    content = models.TextField()
    
    # Rating categories (1-5 scale)
    overall_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    customer_service_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True, null=True
    )
    buying_process_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True, null=True
    )
    price_fairness_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True, null=True
    )
    
    # Review metadata
    status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING)
    is_verified_transaction = models.BooleanField(default=False)
    helpful_votes = models.PositiveIntegerField(default=0)
    unhelpful_votes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Dealer Review'
        verbose_name_plural = 'Dealer Reviews'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['overall_rating']),
            models.Index(fields=['is_verified_transaction']),
        ]
        unique_together = ['user', 'dealer']
    
    def __str__(self):
        return f"{self.title} - Review for {self.dealer.email}"


class ReviewImage(models.Model):
    """Images attached to vehicle reviews."""
    vehicle_review = models.ForeignKey(VehicleReview, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    dealer_review = models.ForeignKey(DealerReview, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    image = models.ImageField(upload_to='reviews/images/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        if self.vehicle_review:
            return f"Image for {self.vehicle_review}"
        return f"Image for {self.dealer_review}"


class ReviewVote(models.Model):
    """Track helpful/unhelpful votes on reviews."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_votes')
    vehicle_review = models.ForeignKey(VehicleReview, on_delete=models.CASCADE, related_name='votes', null=True, blank=True)
    dealer_review = models.ForeignKey(DealerReview, on_delete=models.CASCADE, related_name='votes', null=True, blank=True)
    is_helpful = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [
            ('user', 'vehicle_review'),
            ('user', 'dealer_review'),
        ]
    
    def __str__(self):
        review = self.vehicle_review or self.dealer_review
        vote_type = "helpful" if self.is_helpful else "unhelpful"
        return f"{self.user.email} found review {review.id} {vote_type}"


class ReviewComment(models.Model):
    """Comments on vehicle or dealer reviews."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_comments')
    vehicle_review = models.ForeignKey(VehicleReview, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    dealer_review = models.ForeignKey(DealerReview, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        review = self.vehicle_review or self.dealer_review
        return f"Comment by {self.user.email} on review {review.id}"
