"""
Comprehensive API views for vehicle listings.
"""
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg, Max
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import generics, status, filters, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters

# Import activity logging utilities
from admin_panel.utils import log_listing_activity, log_status_change_activity
from admin_panel.models import ActivityLogType

from .models import VehicleListing, ListingImage, ListingVideo, SavedListing, ListingView, ListingStatusLog
from .serializers import (
    VehicleListingListSerializer, VehicleListingDetailSerializer,
    VehicleListingCreateUpdateSerializer, SavedListingSerializer,
    ListingViewSerializer, VehicleListingStatusSerializer,
    VehicleListingStatsSerializer, ListingImageSerializer,
    ListingVideoSerializer
)
from .status_manager import ListingStatusManager
from .security import (
    RateLimitMixin, APISecurityMixin, CacheControlMixin,
    rate_limit, admin_required, get_rate_limit
)

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for listings."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class VehicleListingFilter(django_filters.FilterSet):
    """Advanced filtering for vehicle listings."""
    
    # Price filters
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    
    # Year filters
    year_min = django_filters.NumberFilter(field_name='year', lookup_expr='gte')
    year_max = django_filters.NumberFilter(field_name='year', lookup_expr='lte')
    
    # Kilometers filters
    kilometers_min = django_filters.NumberFilter(field_name='kilometers', lookup_expr='gte')
    kilometers_max = django_filters.NumberFilter(field_name='kilometers', lookup_expr='lte')
    
    # Location filters
    city = django_filters.CharFilter(field_name='location_city', lookup_expr='icontains')
    state = django_filters.CharFilter(field_name='location_state', lookup_expr='icontains')
    country = django_filters.CharFilter(field_name='location_country', lookup_expr='icontains')
    
    # Multiple choice filters
    make = django_filters.CharFilter(field_name='make', lookup_expr='iexact')
    model = django_filters.CharFilter(field_name='model', lookup_expr='icontains')
    fuel_type = django_filters.MultipleChoiceFilter(choices=[
        ('gasoline', 'Gasoline'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
        ('plug_in_hybrid', 'Plug-in Hybrid'),
        ('lpg', 'LPG'),
        ('cng', 'CNG'),
    ])
    transmission = django_filters.MultipleChoiceFilter(choices=[
        ('automatic', 'Automatic'),
        ('manual', 'Manual'),
        ('cvt', 'CVT'),
        ('semi_automatic', 'Semi-Automatic'),
    ])
    condition = django_filters.MultipleChoiceFilter(choices=[
        ('new', 'New'),
        ('used', 'Used'),
        ('certified_pre_owned', 'Certified Pre-Owned'),
    ])
    color = django_filters.CharFilter(field_name='color', lookup_expr='icontains')
    
    # Boolean filters
    is_featured = django_filters.BooleanFilter()
    is_premium = django_filters.BooleanFilter()
    
    # Date filters
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Search filter
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = VehicleListing
        fields = []
    
    def filter_search(self, queryset, name, value):
        """Full-text search across multiple fields."""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(make__icontains=value) |
            Q(model__icontains=value) |
            Q(features__icontains=value) |
            Q(city__icontains=value) |
            Q(state__icontains=value)
        )


class VehicleListingListView(RateLimitMixin, APISecurityMixin, CacheControlMixin, generics.ListAPIView):
    """List all published vehicle listings with filtering and search."""
    serializer_class = VehicleListingListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = VehicleListingFilter
    ordering_fields = ['price', 'year', 'kilometers', 'created_at', 'views_count']
    ordering = ['-created_at']
    cache_timeout = 300  # 5 minutes for list views
    
    def get_queryset(self):
        """Get published listings with optimized queries."""
        return VehicleListing.objects.filter(
            status='published'
        ).select_related('user').prefetch_related('images')


class VehicleListingDetailView(generics.RetrieveAPIView):
    """Retrieve detailed information about a specific listing."""
    serializer_class = VehicleListingDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Get published listings with all related data."""
        return VehicleListing.objects.filter(
            status='published'
        ).select_related('user').prefetch_related(
            'images', 'videos', 'status_logs__changed_by'
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve listing and record view."""
        instance = self.get_object()
        
        # Record view if not the owner
        if not request.user.is_authenticated or request.user != instance.user:
            self._record_view(request, instance)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def _record_view(self, request, listing):
        """Record a view for analytics."""
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create view record
        ListingView.objects.create(
            listing=listing,
            user=request.user if request.user.is_authenticated else None,
            ip_address=ip_address,
            user_agent=user_agent
        )


class VehicleListingCreateView(generics.CreateAPIView):
    """Create a new vehicle listing."""
    serializer_class = VehicleListingCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @rate_limit(rate='10/h', methods=['POST'])
    def perform_create(self, serializer):
        """Set user and initial status."""
        listing = serializer.save(user=self.request.user, status='draft')
        
        # Log the listing creation
        log_listing_activity(
            user=self.request.user,
            action_type=ActivityLogType.CREATE,
            listing=listing,
            description=f'Created new listing: {listing.title}',
            request=self.request
        )


class VehicleListingUpdateView(generics.UpdateAPIView):
    """Update an existing vehicle listing."""
    serializer_class = VehicleListingCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Only allow users to update their own listings."""
        return VehicleListing.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        """Update listing with logging."""
        listing = serializer.save()
        
        # Log the listing update
        log_listing_activity(
            user=self.request.user,
            action_type=ActivityLogType.UPDATE,
            listing=listing,
            description=f'Updated listing: {listing.title}',
            request=self.request
        )


class VehicleListingDeleteView(generics.DestroyAPIView):
    """Delete a vehicle listing."""
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Only allow users to delete their own listings."""
        return VehicleListing.objects.filter(user=self.request.user)
    
    def perform_destroy(self, instance):
        """Delete listing with logging."""
        # Log the listing deletion before deleting
        log_listing_activity(
            user=self.request.user,
            action_type=ActivityLogType.DELETE,
            listing=instance,
            description=f'Deleted listing: {instance.title}',
            request=self.request
        )
        
        # Perform the actual deletion
        instance.delete()


class MyListingsView(generics.ListAPIView):
    """List current user's listings."""
    serializer_class = VehicleListingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['created_at', 'updated_at', 'status', 'price']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get user's listings with view counts."""
        return VehicleListing.objects.filter(
            user=self.request.user
        ).prefetch_related('images')


class VehicleListingStatusView(RateLimitMixin, APISecurityMixin, generics.UpdateAPIView):
    """Change listing status."""
    serializer_class = VehicleListingStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Allow owners and staff to change status."""
        if self.request.user.is_staff:
            return VehicleListing.objects.all()
        return VehicleListing.objects.filter(user=self.request.user)
    
    @rate_limit(rate='20/h', methods=['POST', 'PUT', 'PATCH'])
    def update(self, request, *args, **kwargs):
        """Update listing status using workflow methods."""
        listing = self.get_object()
        serializer = self.get_serializer(data=request.data, context={'listing': listing})
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data['status']
        reason = serializer.validated_data.get('reason', '')
        
        try:
            # Store old status for logging
            old_status = listing.status
            
            # Use status manager for workflow validation
            status_manager = ListingStatusManager(listing)
            if status_manager.can_transition_to(new_status):
                # Use appropriate workflow method
                if new_status == 'published':
                    listing.publish(user=request.user, reason=reason)
                elif new_status == 'rejected':
                    listing.reject(user=request.user, reason=reason)
                elif new_status == 'sold':
                    listing.mark_as_sold(user=request.user)
                elif new_status == 'suspended':
                    listing.suspend(user=request.user, reason=reason)
                elif new_status == 'draft':
                    listing.make_draft(user=request.user, reason=reason)
                else:
                    listing.change_status(new_status, user=request.user, reason=reason)
                
                # Log comprehensive status change
                log_status_change_activity(
                    user=request.user,
                    listing=listing,
                    old_status=old_status,
                    new_status=new_status,
                    reason=reason,
                    request=request
                )
                
                # Log security event
                self.log_security_event(request, 'status_changed', {
                    'listing_id': listing.id,
                    'old_status': old_status,
                    'new_status': new_status,
                    'reason': reason
                })
                
                return Response({
                    'status': 'success',
                    'message': f'Listing status changed to {new_status}',
                    'new_status': listing.status
                })
            else:
                return Response({
                    'status': 'error',
                    'message': f'Cannot change status from {listing.status} to {new_status}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except ValueError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class SavedListingListView(generics.ListCreateAPIView):
    """List and create saved listings."""
    serializer_class = SavedListingSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Get user's saved listings."""
        return SavedListing.objects.filter(
            user=self.request.user
        ).select_related('listing__user').prefetch_related('listing__images')
    
    def perform_create(self, serializer):
        """Save listing for current user."""
        serializer.save(user=self.request.user)


class SavedListingDeleteView(generics.DestroyAPIView):
    """Remove a saved listing."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get user's saved listings."""
        return SavedListing.objects.filter(user=self.request.user)


class ListingImageListView(generics.ListCreateAPIView):
    """List and upload images for a listing."""
    serializer_class = ListingImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get images for user's listing."""
        listing_slug = self.kwargs['listing_slug']
        listing = get_object_or_404(
            VehicleListing, 
            slug=listing_slug, 
            user=self.request.user
        )
        return ListingImage.objects.filter(listing=listing).order_by('order')
    
    def perform_create(self, serializer):
        """Create image for user's listing."""
        listing_slug = self.kwargs['listing_slug']
        listing = get_object_or_404(
            VehicleListing, 
            slug=listing_slug, 
            user=self.request.user
        )
        
        # Set order based on existing images
        max_order = ListingImage.objects.filter(listing=listing).aggregate(
            max_order=Max('order')
        )['max_order'] or -1
        
        serializer.save(listing=listing, order=max_order + 1)


class ListingImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a listing image."""
    serializer_class = ListingImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get images for user's listing."""
        listing_slug = self.kwargs['listing_slug']
        listing = get_object_or_404(
            VehicleListing, 
            slug=listing_slug, 
            user=self.request.user
        )
        return ListingImage.objects.filter(listing=listing)


class ListingVideoListView(generics.ListCreateAPIView):
    """List and upload videos for a listing."""
    serializer_class = ListingVideoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get videos for user's listing."""
        listing_slug = self.kwargs['listing_slug']
        listing = get_object_or_404(
            VehicleListing, 
            slug=listing_slug, 
            user=self.request.user
        )
        return ListingVideo.objects.filter(listing=listing).order_by('order')
    
    def perform_create(self, serializer):
        """Create video for user's listing."""
        listing_slug = self.kwargs['listing_slug']
        listing = get_object_or_404(
            VehicleListing, 
            slug=listing_slug, 
            user=self.request.user
        )
        
        # Set order based on existing videos
        max_order = ListingVideo.objects.filter(listing=listing).aggregate(
            max_order=Max('order')
        )['max_order'] or -1
        
        serializer.save(listing=listing, order=max_order + 1)


class ListingVideoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a listing video."""
    serializer_class = ListingVideoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get videos for user's listing."""
        listing_slug = self.kwargs['listing_slug']
        listing = get_object_or_404(
            VehicleListing, 
            slug=listing_slug, 
            user=self.request.user
        )
        return ListingVideo.objects.filter(listing=listing)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def listing_stats_view(request):
    """Get listing statistics for current user."""
    user_listings = VehicleListing.objects.filter(user=request.user)
    
    stats = {
        'total_listings': user_listings.count(),
        'published_listings': user_listings.filter(status='published').count(),
        'draft_listings': user_listings.filter(status='draft').count(),
        'sold_listings': user_listings.filter(status='sold').count(),
        'total_views': ListingView.objects.filter(listing__user=request.user).count(),
        'total_inquiries': 0,  # Will be implemented with inquiries app
        'avg_price': user_listings.aggregate(avg_price=Avg('price'))['avg_price'] or 0,
        'popular_makes': list(
            user_listings.values('make').annotate(
                count=Count('make')
            ).order_by('-count')[:5]
        ),
        'recent_activity': list(
            user_listings.order_by('-updated_at')[:10].values(
                'title', 'status', 'updated_at'
            )
        )
    }
    
    serializer = VehicleListingStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def popular_makes_view(request):
    """Get popular vehicle makes."""
    popular_makes = VehicleListing.objects.filter(
        status='published'
    ).values('make').annotate(
        count=Count('make')
    ).order_by('-count')[:20]
    
    return Response(popular_makes)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def featured_listings_view(request):
    """Get featured listings."""
    featured_listings = VehicleListing.objects.filter(
        status='published',
        is_featured=True
    ).select_related('user').prefetch_related('images').order_by('-created_at')[:10]
    
    if not featured_listings.exists():
        return Response([], status=status.HTTP_200_OK)
    
    serializer = VehicleListingListSerializer(
        featured_listings, 
        many=True, 
        context={'request': request}
    )
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def recent_listings_view(request):
    """Get recently added listings."""
    recent_listings = VehicleListing.objects.filter(
        status='published'
    ).select_related('user').prefetch_related('images').order_by('-created_at')[:20]
    
    serializer = VehicleListingListSerializer(
        recent_listings, 
        many=True, 
        context={'request': request}
    )
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def bulk_status_change_view(request):
    """Bulk change status for multiple listings."""
    listing_ids = request.data.get('listing_ids', [])
    new_status = request.data.get('status')
    reason = request.data.get('reason', '')
    
    if not listing_ids or not new_status:
        return Response({
            'error': 'listing_ids and status are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get user's listings or all if staff
    if request.user.is_staff:
        listings = VehicleListing.objects.filter(id__in=listing_ids)
    else:
        listings = VehicleListing.objects.filter(
            id__in=listing_ids, 
            user=request.user
        )
    
    results = []
    for listing in listings:
        try:
            if new_status == 'published':
                listing.publish(user=request.user)
            elif new_status == 'rejected':
                listing.reject(user=request.user, reason=reason)
            elif new_status == 'sold':
                listing.mark_as_sold(user=request.user)
            elif new_status == 'suspended':
                listing.suspend(user=request.user, reason=reason)
            else:
                listing.change_status(new_status, user=request.user, reason=reason)
            
            results.append({
                'id': listing.id,
                'title': listing.title,
                'status': 'success',
                'new_status': listing.status
            })
        except ValueError as e:
            results.append({
                'id': listing.id,
                'title': listing.title,
                'status': 'error',
                'error': str(e)
            })
    
    return Response({
        'message': f'Processed {len(results)} listings',
        'results': results
    })
