#!/usr/bin/env python
"""
Basic Test Data Creation Script for YallaMotor
This script creates essential test data for testing the application.
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta
import random
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yallamotor_project.settings')
django.setup()

# Import models after Django setup
from users.models import User, UserProfile, UserRole
from vehicles.models import (
    FuelType, TransmissionType, Brand, VehicleModel, 
    VehicleCategory, VehicleSpecification
)
from listings.models import (
    VehicleListing, ListingStatus, ConditionType, PriceType
)


def create_basic_users():
    """Create basic test users."""
    print("Creating basic users...")
    
    # Create superuser
    admin_user, created = User.objects.get_or_create(
        email='admin@yallamotor.com',
        defaults={
            'first_name': 'Admin',
            'last_name': 'User',
            'role': UserRole.ADMIN,
            'is_superuser': True,
            'is_staff': True,
            'is_verified': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print(f"Created admin user: {admin_user.email}")
    
    # Create seller
    seller_user, created = User.objects.get_or_create(
        email='seller@example.com',
        defaults={
            'first_name': 'Ahmed',
            'last_name': 'Al-Rashid',
            'role': UserRole.SELLER,
            'phone_number': '+971501234567',
            'is_verified': True
        }
    )
    if created:
        seller_user.set_password('seller123')
        seller_user.save()
        print(f"Created seller user: {seller_user.email}")
    
    # Create client
    client_user, created = User.objects.get_or_create(
        email='client@example.com',
        defaults={
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'role': UserRole.CLIENT,
            'phone_number': '+971502345678',
            'is_verified': True
        }
    )
    if created:
        client_user.set_password('client123')
        client_user.save()
        print(f"Created client user: {client_user.email}")
    
    return [admin_user, seller_user, client_user]


def create_basic_vehicle_data():
    """Create basic vehicle master data."""
    print("Creating basic vehicle data...")
    
    # Create fuel types
    petrol, _ = FuelType.objects.get_or_create(
        name='Petrol',
        defaults={'description': 'Gasoline engine'}
    )
    diesel, _ = FuelType.objects.get_or_create(
        name='Diesel',
        defaults={'description': 'Diesel engine'}
    )
    
    # Create transmission types
    automatic, _ = TransmissionType.objects.get_or_create(
        name='Automatic',
        defaults={'description': 'Automatic transmission'}
    )
    manual, _ = TransmissionType.objects.get_or_create(
        name='Manual',
        defaults={'description': 'Manual transmission'}
    )
    
    # Create categories
    sedan, _ = VehicleCategory.objects.get_or_create(
        name='Sedan',
        defaults={'description': 'Four-door passenger car'}
    )
    suv, _ = VehicleCategory.objects.get_or_create(
        name='SUV',
        defaults={'description': 'Sport Utility Vehicle'}
    )
    
    # Create brands
    toyota, _ = Brand.objects.get_or_create(
        name='Toyota',
        defaults={'country_of_origin': 'Japan', 'founded_year': 1937}
    )
    bmw, _ = Brand.objects.get_or_create(
        name='BMW',
        defaults={'country_of_origin': 'Germany', 'founded_year': 1916}
    )
    
    # Create models
    camry, _ = VehicleModel.objects.get_or_create(
        brand=toyota,
        name='Camry'
    )
    x5, _ = VehicleModel.objects.get_or_create(
        brand=bmw,
        name='X5'
    )
    
    print("Created basic vehicle master data")
    return {
        'fuel_types': [petrol, diesel],
        'transmissions': [automatic, manual],
        'categories': [sedan, suv],
        'brands': [toyota, bmw],
        'models': [camry, x5]
    }


def create_basic_specifications(vehicle_data):
    """Create basic vehicle specifications."""
    print("Creating basic vehicle specifications...")
    
    specifications = []
    
    # Toyota Camry 2023
    camry_spec, created = VehicleSpecification.objects.get_or_create(
        model=vehicle_data['models'][0],  # Camry
        year=2023,
        defaults={
            'category': vehicle_data['categories'][0],  # Sedan
            'engine_capacity': Decimal('2.5'),
            'transmission': vehicle_data['transmissions'][0],  # Automatic
            'fuel_type': vehicle_data['fuel_types'][0],  # Petrol
            'horsepower': 203,
            'seating_capacity': 5,
            'doors': 4
        }
    )
    specifications.append(camry_spec)
    
    # BMW X5 2022
    x5_spec, created = VehicleSpecification.objects.get_or_create(
        model=vehicle_data['models'][1],  # X5
        year=2022,
        defaults={
            'category': vehicle_data['categories'][1],  # SUV
            'engine_capacity': Decimal('3.0'),
            'transmission': vehicle_data['transmissions'][0],  # Automatic
            'fuel_type': vehicle_data['fuel_types'][0],  # Petrol
            'horsepower': 335,
            'seating_capacity': 7,
            'doors': 5
        }
    )
    specifications.append(x5_spec)
    
    print(f"Created {len(specifications)} vehicle specifications")
    return specifications


def create_basic_listings(users, specifications):
    """Create basic vehicle listings."""
    print("Creating basic vehicle listings...")
    
    seller = users[1]  # seller user
    listings = []
    
    # Toyota Camry listing
    camry_listing, created = VehicleListing.objects.get_or_create(
        title='Toyota Camry 2023 - Excellent Condition',
        user=seller,
        defaults={
            'vehicle_specification': specifications[0],
            'condition': ConditionType.USED,
            'mileage': 15000,
            'price': Decimal('85000'),
            'price_type': PriceType.NEGOTIABLE,
            'location_city': 'Dubai',
            'location_country': 'UAE',
            'description': 'Excellent condition Toyota Camry 2023. Well maintained with full service history.',
            'color_exterior': 'White',
            'color_interior': 'Black',
            'status': ListingStatus.ACTIVE,
            'is_featured': True,
            'views_count': 45
        }
    )
    listings.append(camry_listing)
    
    # BMW X5 listing
    x5_listing, created = VehicleListing.objects.get_or_create(
        title='BMW X5 2022 - Premium SUV',
        user=seller,
        defaults={
            'vehicle_specification': specifications[1],
            'condition': ConditionType.USED,
            'mileage': 25000,
            'price': Decimal('185000'),
            'price_type': PriceType.FIXED,
            'location_city': 'Abu Dhabi',
            'location_country': 'UAE',
            'description': 'Premium BMW X5 2022 in excellent condition. Perfect for family use.',
            'color_exterior': 'Black',
            'color_interior': 'Beige',
            'status': ListingStatus.ACTIVE,
            'is_premium': True,
            'views_count': 78
        }
    )
    listings.append(x5_listing)
    
    print(f"Created {len(listings)} vehicle listings")
    return listings


def main():
    """Main function to create basic test data."""
    print("Starting basic test data creation...")
    print("=" * 40)
    
    try:
        # Create users
        users = create_basic_users()
        
        # Create vehicle data
        vehicle_data = create_basic_vehicle_data()
        
        # Create specifications
        specifications = create_basic_specifications(vehicle_data)
        
        # Create listings
        listings = create_basic_listings(users, specifications)
        
        print("=" * 40)
        print("Basic test data creation completed successfully!")
        print("\nTest Accounts:")
        print("-" * 20)
        print("Admin: admin@yallamotor.com / admin123")
        print("Seller: seller@example.com / seller123")
        print("Client: client@example.com / client123")
        print(f"\nCreated {len(listings)} test listings")
        
    except Exception as e:
        print(f"Error creating test data: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()