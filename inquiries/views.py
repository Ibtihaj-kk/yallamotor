from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import ListingInquiry, InquiryResponse, TestDriveRequest
from .permissions import (
    IsInquiryOwnerOrListingOwner,
    IsListingOwner,
    IsResponseOwnerOrInquiryParticipant,
    CanCreateInquiry,
    CanManageTestDrive
)
from .serializers import (
    ListingInquiryListSerializer,
    ListingInquiryDetailSerializer,
    ListingInquiryCreateSerializer,
    InquiryResponseSerializer,
    InquiryResponseCreateSerializer,
    TestDriveRequestSerializer,
    TestDriveRequestUpdateSerializer
)
from listings.models import VehicleListing


class ListingInquiryViewSet(viewsets.ModelViewSet):
    """ViewSet for listing inquiries."""
    permission_classes = [IsAuthenticated, IsInquiryOwnerOrListingOwner]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['message']
    filterset_fields = ['status', 'inquiry_type', 'listing']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        # If user is staff or admin, they can see all inquiries
        if user.is_staff or user.is_superuser:
            return ListingInquiry.objects.all()
        
        # Regular users can see their own inquiries and inquiries for their listings
        return ListingInquiry.objects.filter(
            # User's own inquiries
            Q(user=user) |
            # Inquiries for user's listings
            Q(listing__user=user)
        )
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            permission_classes = [IsAuthenticated, CanCreateInquiry]
        elif self.action in ['mark_as_viewed', 'mark_as_closed']:
            permission_classes = [IsAuthenticated, IsListingOwner]
        else:
            permission_classes = [IsAuthenticated, IsInquiryOwnerOrListingOwner]
        
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Set the user when creating an inquiry."""
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Create an inquiry and return it with the list serializer."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Return the created inquiry using the list serializer to include the ID
        instance = serializer.instance
        response_serializer = ListingInquiryListSerializer(instance, context={'request': request})
        headers = self.get_success_headers(serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_class(self):
        if self.action == 'create':
            return ListingInquiryCreateSerializer
        elif self.action in ['list', 'my_inquiries', 'received_inquiries', 'seller_dashboard']:
            return ListingInquiryListSerializer
        return ListingInquiryDetailSerializer
    
    @action(detail=False, methods=['get'])
    def my_inquiries(self, request):
        """Get current user's inquiries."""
        inquiries = ListingInquiry.objects.filter(user=request.user)
        serializer = ListingInquiryListSerializer(inquiries, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def received_inquiries(self, request):
        """Get inquiries for current user's listings (Seller Portal)."""
        inquiries = ListingInquiry.objects.filter(listing__user=request.user)
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            inquiries = inquiries.filter(status=status_filter)
        
        serializer = ListingInquiryListSerializer(inquiries, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_viewed(self, request, pk=None):
        """Mark inquiry as viewed by seller."""
        inquiry = self.get_object()
        
        # Only the listing owner can mark as viewed
        if inquiry.listing.user != request.user:
            return Response(
                {'error': 'You do not have permission to update this inquiry.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        inquiry.mark_as_viewed()
        serializer = self.get_serializer(inquiry)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_closed(self, request, pk=None):
        """Mark inquiry as closed."""
        inquiry = self.get_object()
        
        # Only the listing owner can close the inquiry
        if inquiry.listing.user != request.user:
            return Response(
                {'error': 'You do not have permission to update this inquiry.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        inquiry.mark_as_closed()
        serializer = self.get_serializer(inquiry)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def seller_dashboard(self, request):
        """Get seller dashboard statistics."""
        user_inquiries = ListingInquiry.objects.filter(listing__user=request.user)
        
        stats = {
            'total_inquiries': user_inquiries.count(),
            'new_inquiries': user_inquiries.filter(status='new').count(),
            'viewed_inquiries': user_inquiries.filter(status='viewed').count(),
            'replied_inquiries': user_inquiries.filter(status='replied').count(),
            'closed_inquiries': user_inquiries.filter(status='closed').count(),
            'recent_inquiries': ListingInquiryListSerializer(
                user_inquiries[:5], many=True
            ).data
        }
        
        return Response(stats)


class InquiryResponseViewSet(viewsets.ModelViewSet):
    """ViewSet for inquiry responses."""
    serializer_class = InquiryResponseSerializer
    permission_classes = [IsAuthenticated, IsResponseOwnerOrInquiryParticipant]
    
    def get_queryset(self):
        user = self.request.user
        
        # If user is staff or admin, they can see all responses
        if user.is_staff or user.is_superuser:
            return InquiryResponse.objects.all()
        
        # Regular users can see responses to their inquiries and responses they've made
        return InquiryResponse.objects.filter(
            # Responses to user's inquiries
            Q(inquiry__user=user) |
            # Responses user has made
            Q(responder=user) |
            # Responses to inquiries about user's listings
            Q(inquiry__listing__user=user)
        )
    
    def get_serializer_class(self):
        if self.action == 'create':
            return InquiryResponseCreateSerializer
        return InquiryResponseSerializer
    
    def perform_create(self, serializer):
        """Create response and mark inquiry as replied."""
        response = serializer.save(responder=self.request.user)
        # The inquiry status is automatically updated in the model's save method
        return response


class TestDriveRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for test drive requests."""
    serializer_class = TestDriveRequestSerializer
    permission_classes = [IsAuthenticated, CanManageTestDrive]
    
    def get_queryset(self):
        user = self.request.user
        
        # If user is staff or admin, they can see all test drive requests
        if user.is_staff or user.is_superuser:
            return TestDriveRequest.objects.all()
        
        # Regular users can see their own test drive requests and requests for their listings
        return TestDriveRequest.objects.filter(
            # User's own test drive requests
            Q(inquiry__user=user) |
            # Test drive requests for user's listings
            Q(inquiry__listing__user=user)
        )
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return TestDriveRequestUpdateSerializer
        return TestDriveRequestSerializer
    
    @action(detail=True, methods=['post'])
    def confirm_test_drive(self, request, pk=None):
        """Confirm or unconfirm a test drive request."""
        test_drive = self.get_object()
        
        # Only the listing owner can confirm the test drive
        if test_drive.inquiry.listing.user != request.user:
            return Response(
                {'error': 'You do not have permission to update this test drive request.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        is_confirmed = request.data.get('is_confirmed', True)
        test_drive.is_confirmed = is_confirmed
        
        if is_confirmed:
            from django.utils import timezone
            test_drive.confirmation_date = timezone.now()
            test_drive.confirmed_by = request.user
        else:
            test_drive.confirmation_date = None
            test_drive.confirmed_by = None
            
        test_drive.save()
        
        serializer = self.get_serializer(test_drive)
        return Response(serializer.data)
