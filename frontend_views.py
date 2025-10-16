from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from listings.models import VehicleListing
from vehicles.models import VehicleCategory, VehicleModel, VehicleSpecification
from listings.filters import VehicleListingFilter
from listings.serializers import VehicleListingListSerializer
import json


def homepage_view(request):
    """
    Homepage view that renders the index.html template with dynamic data
    """
    # Get filter data for the homepage
    categories = VehicleCategory.objects.all()
    vehicle_models = VehicleModel.objects.all()
    
    # Get unique values for filters
    listings = VehicleListing.objects.filter(status='published')
    
    # Get unique cities
    cities = listings.values_list('location_city', flat=True).distinct().order_by('location_city')
    cities = [city for city in cities if city]  # Remove empty values
    
    # Get unique makes/brands
    makes = listings.values_list('make', flat=True).distinct().order_by('make')
    makes = [make for make in makes if make]  # Remove empty values
    
    # Get unique years
    years = listings.values_list('year', flat=True).distinct().order_by('-year')
    years = [year for year in years if year]  # Remove empty values
    
    # Get unique body types from VehicleCategory
    body_types = VehicleCategory.objects.filter(is_active=True)
    
    # Budget ranges (predefined)
    budget_ranges = [
        {'label': 'Under $5K', 'min': 0, 'max': 5000},
        {'label': '$5K - $10K', 'min': 5000, 'max': 10000},
        {'label': '$10K - $15K', 'min': 10000, 'max': 15000},
        {'label': '$15K - $20K', 'min': 15000, 'max': 20000},
        {'label': '$20K - $25K', 'min': 20000, 'max': 25000},
        {'label': '$25K - $30K', 'min': 25000, 'max': 30000},
        {'label': '$30K - $40K', 'min': 30000, 'max': 40000},
        {'label': '$40K - $50K', 'min': 40000, 'max': 50000},
        {'label': '$50K+', 'min': 50000, 'max': None},
    ]
    
    # Get featured listings for homepage display
    featured_listings = listings.filter(is_featured=True)[:8]
    
    context = {
        'categories': categories,
        'vehicle_models': vehicle_models,
        'cities': cities,
        'makes': makes,
        'years': years,
        'body_types': body_types,
        'budget_ranges': budget_ranges,
        'featured_listings': featured_listings,
    }
    
    return render(request, 'frontend/index.html', context)


@api_view(['GET'])
def filter_listings_api(request):
    """
    API endpoint to filter listings based on various criteria
    """
    # Apply filters using the existing VehicleListingFilter
    filterset = VehicleListingFilter(request.GET, queryset=VehicleListing.objects.filter(status='published'))
    
    if filterset.is_valid():
        queryset = filterset.qs
    else:
        queryset = VehicleListing.objects.filter(status='published')
    
    # Apply pagination
    paginator = Paginator(queryset, 12)  # 12 items per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Serialize the data
    serializer = VehicleListingListSerializer(page_obj, many=True)
    
    return Response({
        'results': serializer.data,
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'current_page': page_obj.number,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
    })


def search_listings_view(request):
    """
    View to handle search and filtering of listings
    """
    # Get search parameters
    search_query = request.GET.get('search', '')
    category = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    make = request.GET.get('make', '')
    model = request.GET.get('model', '')
    city = request.GET.get('city', '')
    year = request.GET.get('year', '')
    body_type = request.GET.get('body_type', '')
    
    # Start with active listings
    listings = VehicleListing.objects.filter(status='published')
    
    # Apply search filters
    if search_query:
        listings = listings.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(make__icontains=search_query) |
            Q(model__icontains=search_query)
        )
    
    if category:
        # Filter by body_type category
        listings = listings.filter(body_type__name__icontains=category)
    
    if min_price:
        listings = listings.filter(price__gte=min_price)
    
    if max_price:
        listings = listings.filter(price__lte=max_price)
    
    if make:
        listings = listings.filter(make__icontains=make)
    
    if model:
        listings = listings.filter(model__icontains=model)
    
    if city:
        listings = listings.filter(location_city__icontains=city)
    
    if year:
        listings = listings.filter(year=year)
    
    if body_type:
        # Filter by body_type using the new body_type field
        listings = listings.filter(body_type__name__icontains=body_type)
    
    # Apply pagination
    paginator = Paginator(listings, 12)  # 12 items per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get filter data for the template
    categories = VehicleCategory.objects.all()
    all_listings = VehicleListing.objects.filter(status='published')
    cities = all_listings.values_list('location_city', flat=True).distinct().order_by('location_city')
    makes = all_listings.values_list('make', flat=True).distinct().order_by('make')
    years = all_listings.values_list('year', flat=True).distinct().order_by('-year')
    body_types = VehicleCategory.objects.filter(is_active=True).values_list('name', flat=True)
    
    context = {
        'listings': page_obj,
        'search_query': search_query,
        'categories': categories,
        'cities': [city for city in cities if city],
        'makes': [make for make in makes if make],
        'years': [year for year in years if year],
        'body_types': [body_type for body_type in body_types if body_type],
        'current_filters': {
            'category': category,
            'min_price': min_price,
            'max_price': max_price,
            'make': make,
            'model': model,
            'city': city,
            'year': year,
            'body_type': body_type,
        }
    }
    
    return render(request, 'frontend/search_results.html', context)