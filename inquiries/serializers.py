from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ListingInquiry, InquiryResponse, TestDriveRequest
from listings.serializers import VehicleListingListSerializer
from users.serializers import UserSerializer

User = get_user_model()


class TestDriveRequestSerializer(serializers.ModelSerializer):
    """Serializer for test drive requests."""
    
    class Meta:
        model = TestDriveRequest
        fields = ['id', 'inquiry', 'preferred_date', 'preferred_time', 'alternate_date', 
                 'alternate_time', 'location_preference', 'additional_notes', 
                 'is_confirmed', 'confirmation_date', 'confirmed_by']


class InquiryResponseSerializer(serializers.ModelSerializer):
    """Serializer for inquiry responses."""
    responder = UserSerializer(read_only=True)
    
    class Meta:
        model = InquiryResponse
        fields = ['id', 'inquiry', 'responder', 'message', 'created_at', 'is_read']
        read_only_fields = ['responder']
    
    def create(self, validated_data):
        validated_data['responder'] = self.context['request'].user
        return super().create(validated_data)


class ListingInquiryListSerializer(serializers.ModelSerializer):
    """Serializer for listing inquiries."""
    user = UserSerializer(read_only=True)
    listing = VehicleListingListSerializer(read_only=True)
    seller = UserSerializer(read_only=True)
    response_count = serializers.SerializerMethodField()
    has_test_drive = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_new = serializers.BooleanField(read_only=True)
    is_viewed = serializers.BooleanField(read_only=True)
    is_replied = serializers.BooleanField(read_only=True)
    is_closed = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ListingInquiry
        fields = ['id', 'user', 'listing', 'seller', 'name', 'email', 'phone',
                 'inquiry_type', 'message', 'status', 'status_display', 'is_read',
                 'is_new', 'is_viewed', 'is_replied', 'is_closed',
                 'created_at', 'updated_at', 'response_count', 'has_test_drive']
    
    def get_response_count(self, obj):
        return obj.responses.count()
    
    def get_has_test_drive(self, obj):
        return hasattr(obj, 'test_drive_details')


class ListingInquiryDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed listing inquiry view."""
    user = UserSerializer(read_only=True)
    listing = VehicleListingListSerializer(read_only=True)
    seller = UserSerializer(read_only=True)
    responses = InquiryResponseSerializer(source='responses', many=True, read_only=True)
    test_drive = TestDriveRequestSerializer(source='test_drive_details', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_new = serializers.BooleanField(read_only=True)
    is_viewed = serializers.BooleanField(read_only=True)
    is_replied = serializers.BooleanField(read_only=True)
    is_closed = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ListingInquiry
        fields = ['id', 'user', 'listing', 'seller', 'name', 'email', 'phone',
                 'inquiry_type', 'message', 'status', 'status_display', 'is_read',
                 'is_new', 'is_viewed', 'is_replied', 'is_closed',
                 'created_at', 'updated_at', 'responses', 'test_drive']


class ListingInquiryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating listing inquiries."""
    test_drive_data = TestDriveRequestSerializer(required=False, write_only=True)
    
    class Meta:
        model = ListingInquiry
        fields = ['listing', 'inquiry_type', 'message', 'test_drive_data']
    
    def create(self, validated_data):
        test_drive_data = validated_data.pop('test_drive_data', None)
        
        # Set the user from the request
        validated_data['user'] = self.context['request'].user
        
        # Create the inquiry
        inquiry = ListingInquiry.objects.create(**validated_data)
        
        # Create test drive request if provided
        if test_drive_data and inquiry.inquiry_type == ListingInquiry.InquiryType.TEST_DRIVE:
            TestDriveRequest.objects.create(inquiry=inquiry, **test_drive_data)
        
        return inquiry


class InquiryResponseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating inquiry responses."""
    
    class Meta:
        model = InquiryResponse
        fields = ['inquiry', 'message']
    
    def create(self, validated_data):
        validated_data['responder'] = self.context['request'].user
        return super().create(validated_data)


class TestDriveRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating test drive requests."""
    
    class Meta:
        model = TestDriveRequest
        fields = ['preferred_date', 'preferred_time', 'alternate_date', 
                 'alternate_time', 'location_preference', 'additional_notes', 'is_confirmed']