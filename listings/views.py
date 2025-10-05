from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models

from .models import VehicleListing, SavedListing, ListingView, ListingStatus
from .serializers import (
    VehicleListingListSerializer,
    VehicleListingDetailSerializer,
    VehicleListingCreateUpdateSerializer,
    SavedListingSerializer,
    ListingViewSerializer
)
from .filters import VehicleListingFilter
from .pagination import ListingPagination


class VehicleListingViewSet(viewsets.ModelViewSet):
    """ViewSet for vehicle listings."""
    queryset = VehicleListing.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['title', 'description', 'location_city', 'location_country', 'vin']
    filterset_class = VehicleListingFilter
    ordering_fields = ['created_at', 'price', 'mileage', 'views_count']
    ordering = ['-created_at']
    lookup_field = 'slug'
    pagination_class = ListingPagination
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def filter_options(self, request):
        """Get filter options for dropdowns."""
        from vehicles.models import Brand, VehicleModel, VehicleCategory, FuelType, TransmissionType
        from vehicles.serializers import (
            BrandSerializer, VehicleModelListSerializer, VehicleCategorySerializer,
            FuelTypeSerializer, TransmissionTypeSerializer
        )
        
        # Get unique values for location filters
        cities = VehicleListing.objects.filter(status=ListingStatus.ACTIVE)\
            .values_list('location_city', flat=True).distinct().order_by('location_city')
        countries = VehicleListing.objects.filter(status=ListingStatus.ACTIVE)\
            .values_list('location_country', flat=True).distinct().order_by('location_country')
        
        # Get years range
        from django.db.models import Min, Max
        year_range = VehicleListing.objects.filter(status=ListingStatus.ACTIVE)\
            .aggregate(min_year=Min('vehicle_specification__year'), max_year=Max('vehicle_specification__year'))
        
        # Get price range
        price_range = VehicleListing.objects.filter(status=ListingStatus.ACTIVE)\
            .aggregate(min_price=Min('price'), max_price=Max('price'))
        
        # Get mileage range
        mileage_range = VehicleListing.objects.filter(status=ListingStatus.ACTIVE)\
            .aggregate(min_mileage=Min('mileage'), max_mileage=Max('mileage'))
        
        # Get vehicle master data
        brands = Brand.objects.all().order_by('name')
        categories = VehicleCategory.objects.all().order_by('name')
        fuel_types = FuelType.objects.all().order_by('name')
        transmissions = TransmissionType.objects.all().order_by('name')
        
        # Get condition and price type choices
        from .models import ConditionType, PriceType
        condition_choices = [{'value': choice[0], 'label': choice[1]} for choice in ConditionType.choices]
        price_type_choices = [{'value': choice[0], 'label': choice[1]} for choice in PriceType.choices]
        
        # Serialize the data
        data = {
            'brands': BrandSerializer(brands, many=True).data,
            'categories': VehicleCategorySerializer(categories, many=True).data,
            'fuel_types': FuelTypeSerializer(fuel_types, many=True).data,
            'transmissions': TransmissionTypeSerializer(transmissions, many=True).data,
            'condition_types': condition_choices,
            'price_types': price_type_choices,
            'cities': cities,
            'countries': countries,
            'year_range': year_range,
            'price_range': price_range,
            'mileage_range': mileage_range
        }
        
        return Response(data)
        
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_listings(self, request):
        """Get listings for the authenticated user."""
        queryset = self.filter_queryset(self.get_queryset().filter(user=request.user))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VehicleListingDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return VehicleListingCreateUpdateSerializer
        return VehicleListingListSerializer
    
    def get_queryset(self):
        queryset = VehicleListing.objects.all()
        
        # For public listings, only show active listings
        if self.action in ['list', 'retrieve'] and not self.request.user.is_staff:
            queryset = queryset.filter(status=ListingStatus.ACTIVE)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Filter by mileage range
        min_mileage = self.request.query_params.get('min_mileage')
        max_mileage = self.request.query_params.get('max_mileage')
        if min_mileage:
            queryset = queryset.filter(mileage__gte=min_mileage)
        if max_mileage:
            queryset = queryset.filter(mileage__lte=max_mileage)
        
        # Filter by vehicle specification
        model_id = self.request.query_params.get('model')
        brand_id = self.request.query_params.get('brand')
        year = self.request.query_params.get('year')
        fuel_type = self.request.query_params.get('fuel_type')
        transmission = self.request.query_params.get('transmission')
        category = self.request.query_params.get('category')
        
        if model_id:
            queryset = queryset.filter(vehicle_specification__model_id=model_id)
        if brand_id:
            queryset = queryset.filter(vehicle_specification__model__brand_id=brand_id)
        if year:
            queryset = queryset.filter(vehicle_specification__year=year)
        if fuel_type:
            queryset = queryset.filter(vehicle_specification__fuel_type_id=fuel_type)
        if transmission:
            queryset = queryset.filter(vehicle_specification__transmission_id=transmission)
        if category:
            queryset = queryset.filter(vehicle_specification__category_id=category)
        
        # Filter by location
        city = self.request.query_params.get('city')
        country = self.request.query_params.get('country')
        if city:
            queryset = queryset.filter(location_city__icontains=city)
        if country:
            queryset = queryset.filter(location_country__icontains=country)
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Record view if not from the owner
        if not request.user.is_authenticated or request.user != instance.user:
            # Get client IP and user agent
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Check if this IP has viewed this listing in the last 24 hours
            from django.utils import timezone
            import datetime
            recent_view = ListingView.objects.filter(
                listing=instance,
                ip_address=ip_address,
                viewed_at__gte=timezone.now() - datetime.timedelta(hours=24)
            ).exists()
            
            # Only record view if not viewed recently from same IP
            if not recent_view:
                ListingView.objects.create(
                    listing=instance,
                    user=request.user if request.user.is_authenticated else None,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                # Increment the views_count field
                instance.views_count += 1
                instance.save(update_fields=['views_count'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    



class SavedListingViewSet(viewsets.ModelViewSet):
    """ViewSet for saved listings."""
    serializer_class = SavedListingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return SavedListing.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """Toggle saved status for a listing."""
        listing_id = request.data.get('listing_id')
        if not listing_id:
            return Response({'error': 'listing_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        listing = get_object_or_404(VehicleListing, id=listing_id)
        saved_listing = SavedListing.objects.filter(user=request.user, listing=listing)
        
        if saved_listing.exists():
            saved_listing.delete()
            return Response({'status': 'unsaved'}, status=status.HTTP_200_OK)
        else:
            SavedListing.objects.create(user=request.user, listing=listing)
            return Response({'status': 'saved'}, status=status.HTTP_201_CREATED)
