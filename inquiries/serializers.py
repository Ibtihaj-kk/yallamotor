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
        fields = ['id', 'preferred_date', 'preferred_time', 'alternate_date', 
                 'alternate_time', 'notes', 'status', 'created_at', 'updated_at']


class InquiryResponseSerializer(serializers.ModelSerializer):
    """Serializer for inquiry responses."""
    responder = UserSerializer(read_only=True)
    
    class Meta:
        model = InquiryResponse
        fields = ['id', 'inquiry', 'responder', 'message', 'created_at']
        read_only_fields = ['responder']
    
    def create(self, validated_data):
        validated_data['responder'] = self.context['request'].user
        return super().create(validated_data)


class ListingInquiryListSerializer(serializers.ModelSerializer):
    """Serializer for listing inquiries."""
    user = UserSerializer(read_only=True)
    listing = VehicleListingListSerializer(read_only=True)
    response_count = serializers.SerializerMethodField()
    has_test_drive = serializers.SerializerMethodField()
    
    class Meta:
        model = ListingInquiry
        fields = ['id', 'user', 'listing', 'inquiry_type', 'message', 'status', 
                 'created_at', 'response_count', 'has_test_drive']
    
    def get_response_count(self, obj):
        return obj.inquiryresponse_set.count()
    
    def get_has_test_drive(self, obj):
        return hasattr(obj, 'testdriverequest')


class ListingInquiryDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for listing inquiries."""
    user = UserSerializer(read_only=True)
    listing = VehicleListingListSerializer(read_only=True)
    responses = InquiryResponseSerializer(source='inquiryresponse_set', many=True, read_only=True)
    test_drive = TestDriveRequestSerializer(source='testdriverequest', read_only=True)
    
    class Meta:
        model = ListingInquiry
        fields = ['id', 'user', 'listing', 'inquiry_type', 'message', 'status', 
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
                 'alternate_time', 'notes', 'status']