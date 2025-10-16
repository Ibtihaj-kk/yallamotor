from django_filters import rest_framework as filters
from django.db import models
from .models import VehicleListing, ListingStatus, ConditionType


class VehicleListingFilter(filters.FilterSet):
    """Custom filter for vehicle listings."""
    # Price range filters
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte')
    
    # Kilometers range filters
    min_kilometers = filters.NumberFilter(field_name='kilometers', lookup_expr='gte')
    max_kilometers = filters.NumberFilter(field_name='kilometers', lookup_expr='lte')
    
    # Year range filters
    min_year = filters.NumberFilter(field_name='year', lookup_expr='gte')
    max_year = filters.NumberFilter(field_name='year', lookup_expr='lte')
    
    # Vehicle filters
    make = filters.CharFilter(field_name='make', lookup_expr='icontains')
    model = filters.CharFilter(field_name='model', lookup_expr='icontains')
    fuel_type = filters.ChoiceFilter(choices=[
        ('gasoline', 'Gasoline'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
        ('plug_in_hybrid', 'Plug-in Hybrid'),
        ('lpg', 'LPG'),
        ('cng', 'CNG'),
    ])
    transmission = filters.ChoiceFilter(choices=[
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
        ('cvt', 'CVT'),
        ('semi_automatic', 'Semi-Automatic'),
    ])
    
    # Engine size range filters
    min_engine_size = filters.NumberFilter(field_name='engine_size', lookup_expr='gte')
    max_engine_size = filters.NumberFilter(field_name='engine_size', lookup_expr='lte')
    
    # Doors and seats filters
    doors = filters.NumberFilter(field_name='doors')
    seats = filters.NumberFilter(field_name='seats')
    
    # Location filters
    city = filters.CharFilter(field_name='location_city', lookup_expr='icontains')
    country = filters.CharFilter(field_name='location_country', lookup_expr='icontains')
    
    # Color filter
    color = filters.CharFilter(field_name='color', lookup_expr='icontains')
    
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
            models.Q(make__icontains=value) |
            models.Q(model__icontains=value) |
            models.Q(location_city__icontains=value) |
            models.Q(location_country__icontains=value) |
            models.Q(color__icontains=value)
        )
    
    class Meta:
        model = VehicleListing
        fields = [
            'condition', 'status', 'user', 'year', 'make', 'model',
            'fuel_type', 'transmission', 'color', 'doors', 'seats',
            'city', 'country', 'is_featured', 'is_premium'
        ]