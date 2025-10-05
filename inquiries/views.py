from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import ListingInquiry, InquiryResponse, TestDriveRequest
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
    permission_classes = [IsAuthenticated]
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
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ListingInquiryCreateSerializer
        elif self.action == 'retrieve':
            return ListingInquiryDetailSerializer
        return ListingInquiryListSerializer
    
    @action(detail=False, methods=['get'])
    def my_inquiries(self, request):
        """Get current user's inquiries."""
        inquiries = ListingInquiry.objects.filter(user=request.user)
        serializer = ListingInquiryListSerializer(inquiries, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def received_inquiries(self, request):
        """Get inquiries for current user's listings."""
        inquiries = ListingInquiry.objects.filter(listing__user=request.user)
        serializer = ListingInquiryListSerializer(inquiries, many=True)
        return Response(serializer.data)


class InquiryResponseViewSet(viewsets.ModelViewSet):
    """ViewSet for inquiry responses."""
    serializer_class = InquiryResponseSerializer
    permission_classes = [IsAuthenticated]
    
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


class TestDriveRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for test drive requests."""
    serializer_class = TestDriveRequestSerializer
    permission_classes = [IsAuthenticated]
    
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
    def update_status(self, request, pk=None):
        """Update the status of a test drive request."""
        test_drive = self.get_object()
        
        # Only the listing owner can update the status
        if test_drive.inquiry.listing.user != request.user:
            return Response(
                {'error': 'You do not have permission to update this test drive request.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        status_value = request.data.get('status')
        if not status_value or status_value not in dict(TestDriveRequest.Status.choices).keys():
            return Response(
                {'error': 'Invalid status value.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        test_drive.status = status_value
        test_drive.save()
        
        serializer = self.get_serializer(test_drive)
        return Response(serializer.data)
