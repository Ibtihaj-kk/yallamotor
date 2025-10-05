from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import VehicleListing, ListingImage, SavedListing, ListingView
from vehicles.serializers import VehicleSpecificationDetailSerializer
from users.serializers import UserSerializer

User = get_user_model()


class ListingImageSerializer(serializers.ModelSerializer):
    """Serializer for listing images."""
    
    class Meta:
        model = ListingImage
        fields = ['id', 'image', 'thumbnail', 'is_primary', 'caption', 'order', 'created_at']


class VehicleListingListSerializer(serializers.ModelSerializer):
    """Serializer for listing vehicle listings."""
    user = UserSerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    
    class Meta:
        model = VehicleListing
        fields = [
            'id', 'title', 'slug', 'user', 'condition', 'year', 'mileage',
            'price', 'price_type', 'location', 'status', 'created_at',
            'primary_image'
        ]
    
    def get_year(self, obj):
        return obj.vehicle_specification.year if obj.vehicle_specification else None
    
    def get_location(self, obj):
        return f"{obj.location_city}, {obj.location_country}"
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if not primary_image:
            primary_image = obj.images.first()
        
        if primary_image:
            return ListingImageSerializer(primary_image).data
        return None


class VehicleListingDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for vehicle listings."""
    user = UserSerializer(read_only=True)
    vehicle_specification = VehicleSpecificationDetailSerializer(read_only=True)
    images = ListingImageSerializer(source='images', many=True, read_only=True)
    saved_count = serializers.SerializerMethodField()
    view_count = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    exterior_color = serializers.CharField(source='color_exterior', read_only=True)
    interior_color = serializers.CharField(source='color_interior', read_only=True)
    
    class Meta:
        model = VehicleListing
        fields = [
            'id', 'title', 'slug', 'user', 'vehicle_specification', 'condition',
            'year', 'mileage', 'price', 'price_type', 'location', 'description',
            'exterior_color', 'interior_color', 'vin', 'status', 'created_at',
            'updated_at', 'images', 'saved_count', 'view_count', 'is_saved'
        ]
    
    def get_year(self, obj):
        return obj.vehicle_specification.year if obj.vehicle_specification else None
    
    def get_location(self, obj):
        return f"{obj.location_city}, {obj.location_country}"
    
    def get_saved_count(self, obj):
        return obj.saved_by.count()
    
    def get_view_count(self, obj):
        return obj.listing_views.count()
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedListing.objects.filter(user=request.user, listing=obj).exists()
        return False


class VehicleListingCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating vehicle listings."""
    images = serializers.ListField(child=serializers.ImageField(), required=False, write_only=True)
    primary_image_index = serializers.IntegerField(required=False, write_only=True)
    location_city = serializers.CharField()
    location_country = serializers.CharField()
    exterior_color = serializers.CharField(source='color_exterior', required=False)
    interior_color = serializers.CharField(source='color_interior', required=False)
    
    class Meta:
        model = VehicleListing
        fields = [
            'title', 'vehicle_specification', 'condition', 'mileage',
            'price', 'price_type', 'location_city', 'location_country', 'description', 
            'exterior_color', 'interior_color', 'vin', 'status', 'images', 'primary_image_index'
        ]
    
    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        primary_image_index = validated_data.pop('primary_image_index', 0)
        
        # Set the user from the request
        validated_data['user'] = self.context['request'].user
        
        # Create the listing
        listing = VehicleListing.objects.create(**validated_data)
        
        # Create images
        self._process_images(listing, images_data, primary_image_index)
        
        return listing
    
    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', None)
        primary_image_index = validated_data.pop('primary_image_index', None)
        
        # Update listing fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update images if provided
        if images_data is not None:
            # Clear existing images
            instance.listingimage_set.all().delete()
            # Create new images
            self._process_images(instance, images_data, primary_image_index)
        
        return instance
    
    def _process_images(self, listing, images_data, primary_image_index):
        for i, image_data in enumerate(images_data):
            ListingImage.objects.create(
                listing=listing,
                image=image_data,
                is_primary=(i == primary_image_index),
                order=i
            )


class SavedListingSerializer(serializers.ModelSerializer):
    """Serializer for saved listings."""
    listing = VehicleListingListSerializer(read_only=True)
    
    class Meta:
        model = SavedListing
        fields = ['id', 'user', 'listing', 'created_at']
        read_only_fields = ['user']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ListingViewSerializer(serializers.ModelSerializer):
    """Serializer for listing views."""
    
    class Meta:
        model = ListingView
        fields = ['id', 'user', 'listing', 'ip_address', 'created_at']
        read_only_fields = ['user', 'ip_address']
    
    def create(self, validated_data):
        request = self.context.get('request')
        
        # Set user if authenticated
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        
        # Set IP address
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                validated_data['ip_address'] = x_forwarded_for.split(',')[0]
            else:
                validated_data['ip_address'] = request.META.get('REMOTE_ADDR')
        
        return super().create(validated_data)