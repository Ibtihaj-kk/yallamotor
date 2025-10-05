from django_filters import rest_framework as filters
from django.db import models
from .models import VehicleListing
from vehicles.models import Brand, VehicleModel, VehicleCategory, FuelType, TransmissionType


class VehicleListingFilter(filters.FilterSet):
    """Custom filter for vehicle listings."""
    # Price range filters
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte')
    
    # Mileage range filters
    min_mileage = filters.NumberFilter(field_name='mileage', lookup_expr='gte')
    max_mileage = filters.NumberFilter(field_name='mileage', lookup_expr='lte')
    
    # Year range filters
    min_year = filters.NumberFilter(field_name='vehicle_specification__year', lookup_expr='gte')
    max_year = filters.NumberFilter(field_name='vehicle_specification__year', lookup_expr='lte')
    
    # Vehicle specification filters
    brand = filters.ModelChoiceFilter(queryset=Brand.objects.all(), field_name='vehicle_specification__model__brand')
    model = filters.ModelChoiceFilter(queryset=VehicleModel.objects.all(), field_name='vehicle_specification__model')
    category = filters.ModelChoiceFilter(queryset=VehicleCategory.objects.all(), field_name='vehicle_specification__category')
    fuel_type = filters.ModelChoiceFilter(queryset=FuelType.objects.all(), field_name='vehicle_specification__fuel_type')
    transmission = filters.ModelChoiceFilter(queryset=TransmissionType.objects.all(), field_name='vehicle_specification__transmission')
    
    # Location filters
    city = filters.CharFilter(field_name='location_city', lookup_expr='icontains')
    country = filters.CharFilter(field_name='location_country', lookup_expr='icontains')
    
    # Color filters
    exterior_color = filters.CharFilter(field_name='color_exterior', lookup_expr='icontains')
    interior_color = filters.CharFilter(field_name='color_interior', lookup_expr='icontains')
    
    # Listing status filters
    is_featured = filters.BooleanFilter(field_name='is_featured')
    is_premium = filters.BooleanFilter(field_name='is_premium')
    
    # Search filter
    search = filters.CharFilter(method='filter_search')
    
    def filter_search(self, queryset, name, value):
        """Custom search filter that searches across multiple fields."""
        return queryset.filter(
            models.Q(title__icontains=value) |
            models.Q(description__icontains=value) |
            models.Q(vehicle_specification__model__name__icontains=value) |
            models.Q(vehicle_specification__model__brand__name__icontains=value) |
            models.Q(location_city__icontains=value) |
            models.Q(location_country__icontains=value)
        )
    
    class Meta:
        model = VehicleListing
        fields = [
            'condition', 'price_type', 'status', 'user',
            'min_price', 'max_price', 'min_mileage', 'max_mileage',
            'min_year', 'max_year', 'brand', 'model', 'category',
            'fuel_type', 'transmission', 'city', 'country',
            'exterior_color', 'interior_color', 'is_featured', 'is_premium'
        ]