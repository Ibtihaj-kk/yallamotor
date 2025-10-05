#!/usr/bin/env python
"""
Dummy Data Creation Script for YallaMotor
This script creates comprehensive test data for all models.
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta
import random
from django.utils import timezone
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yallamotor_project.settings')
django.setup()

# Import models after Django setup
from users.models import User, UserProfile, UserRole
from vehicles.models import (
    FuelType, TransmissionType, Brand, VehicleModel, 
    VehicleCategory, VehicleSpecification, VehicleFeature, 
    VehicleSpecificationFeature
)
from listings.models import (
    VehicleListing, ListingImage, SavedListing, ListingView,
    ListingStatus, ConditionType, PriceType
)
from inquiries.models import ListingInquiry, InquiryResponse, TestDriveRequest
from reviews.models import DealerReview, VehicleReview
from subscriptions.models import SubscriptionPlan, UserSubscription
from notifications.models import Notification, NotificationPreference


def create_users():
    """Create test users with different roles."""
    print("Creating users...")
    
    users_data = [
        {
            'email': 'admin@yallamotor.com',
            'password': 'admin123',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': UserRole.ADMIN,
            'is_superuser': True,
            'is_staff': True,
            'is_verified': True
        },
        {
            'email': 'staff@yallamotor.com',
            'password': 'staff123',
            'first_name': 'Staff',
            'last_name': 'Member',
            'role': UserRole.STAFF,
            'is_staff': True,
            'is_verified': True
        },
        {
            'email': 'seller1@example.com',
            'password': 'seller123',
            'first_name': 'Ahmed',
            'last_name': 'Al-Rashid',
            'role': UserRole.SELLER,
            'phone_number': '+971501234567',
            'is_verified': True
        },
        {
            'email': 'seller2@example.com',
            'password': 'seller123',
            'first_name': 'Mohammed',
            'last_name': 'Hassan',
            'role': UserRole.SELLER,
            'phone_number': '+971507654321',
            'is_verified': True
        },
        {
            'email': 'dealer@example.com',
            'password': 'dealer123',
            'first_name': 'Premium',
            'last_name': 'Motors',
            'role': UserRole.SELLER,
            'phone_number': '+971509876543',
            'is_verified': True
        },
        {
            'email': 'client1@example.com',
            'password': 'client123',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'role': UserRole.CLIENT,
            'phone_number': '+971502345678',
            'is_verified': True
        },
        {
            'email': 'client2@example.com',
            'password': 'client123',
            'first_name': 'Omar',
            'last_name': 'Abdullah',
            'role': UserRole.CLIENT,
            'phone_number': '+971508765432',
            'is_verified': True
        },
        {
            'email': 'user1@example.com',
            'password': 'user123',
            'first_name': 'Fatima',
            'last_name': 'Al-Zahra',
            'role': UserRole.USER,
            'phone_number': '+971503456789',
            'is_verified': True
        },
        {
            'email': 'user2@example.com',
            'password': 'user123',
            'first_name': 'Ali',
            'last_name': 'Mohamed',
            'role': UserRole.USER,
            'phone_number': '+971506789012',
            'is_verified': False
        },
        {
            'email': 'buyer@example.com',
            'password': 'buyer123',
            'first_name': 'Khalid',
            'last_name': 'Al-Mansouri',
            'role': UserRole.CLIENT,
            'phone_number': '+971504567890',
            'is_verified': True
        }
    ]
    
    created_users = []
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            email=user_data['email'],
            defaults=user_data
        )
        if created:
            user.set_password(user_data['password'])
            user.save()
            print(f"Created user: {user.email}")
        else:
            print(f"User already exists: {user.email}")
        created_users.append(user)
    
    # Create user profiles
    profiles_data = [
        {
            'user': created_users[2],  # seller1
            'company_name': 'Al-Rashid Auto Trading',
            'address': 'Sheikh Zayed Road, Dubai',
            'city': 'Dubai',
            'country': 'UAE',
            'bio': 'Experienced car dealer specializing in luxury vehicles.'
        },
        {
            'user': created_users[3],  # seller2
            'company_name': 'Hassan Motors',
            'address': 'Al Wasl Road, Dubai',
            'city': 'Dubai',
            'country': 'UAE',
            'bio': 'Family-owned dealership serving customers for over 20 years.'
        },
        {
            'user': created_users[4],  # dealer
            'company_name': 'Premium Motors LLC',
            'address': 'Business Bay, Dubai',
            'city': 'Dubai',
            'country': 'UAE',
            'bio': 'Premium automotive dealership offering the finest selection of vehicles.',
            'website': 'https://premiummotors.ae'
        }
    ]
    
    for profile_data in profiles_data:
        profile, created = UserProfile.objects.get_or_create(
            user=profile_data['user'],
            defaults=profile_data
        )
        if created:
            print(f"Created profile for: {profile.user.email}")
    
    return created_users


def create_vehicle_master_data():
    """Create fuel types, transmission types, brands, models, and categories."""
    print("Creating vehicle master data...")
    
    # Fuel Types
    fuel_types_data = [
        {'name': 'Petrol', 'description': 'Gasoline engine'},
        {'name': 'Diesel', 'description': 'Diesel engine'},
        {'name': 'Electric', 'description': 'Electric motor'},
        {'name': 'Hybrid', 'description': 'Hybrid petrol-electric'},
        {'name': 'Plug-in Hybrid', 'description': 'Plug-in hybrid electric'},
        {'name': 'CNG', 'description': 'Compressed Natural Gas'}
    ]
    
    fuel_types = []
    for data in fuel_types_data:
        fuel_type, created = FuelType.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        fuel_types.append(fuel_type)
        if created:
            print(f"Created fuel type: {fuel_type.name}")
    
    # Transmission Types
    transmission_types_data = [
        {'name': 'Automatic', 'description': 'Automatic transmission'},
        {'name': 'Manual', 'description': 'Manual transmission'},
        {'name': 'CVT', 'description': 'Continuously Variable Transmission'},
        {'name': 'Semi-Automatic', 'description': 'Semi-automatic transmission'}
    ]
    
    transmission_types = []
    for data in transmission_types_data:
        transmission_type, created = TransmissionType.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        transmission_types.append(transmission_type)
        if created:
            print(f"Created transmission type: {transmission_type.name}")
    
    # Vehicle Categories
    categories_data = [
        {'name': 'Sedan', 'description': 'Four-door passenger car'},
        {'name': 'SUV', 'description': 'Sport Utility Vehicle'},
        {'name': 'Hatchback', 'description': 'Compact car with rear door'},
        {'name': 'Coupe', 'description': 'Two-door sports car'},
        {'name': 'Convertible', 'description': 'Car with retractable roof'},
        {'name': 'Pickup Truck', 'description': 'Light duty truck'},
        {'name': 'Van', 'description': 'Commercial or passenger van'},
        {'name': 'Wagon', 'description': 'Station wagon'}
    ]
    
    categories = []
    for data in categories_data:
        category, created = VehicleCategory.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        categories.append(category)
        if created:
            print(f"Created category: {category.name}")
    
    # Brands
    brands_data = [
        {'name': 'Toyota', 'country_of_origin': 'Japan', 'founded_year': 1937},
        {'name': 'BMW', 'country_of_origin': 'Germany', 'founded_year': 1916},
        {'name': 'Mercedes-Benz', 'country_of_origin': 'Germany', 'founded_year': 1926},
        {'name': 'Audi', 'country_of_origin': 'Germany', 'founded_year': 1909},
        {'name': 'Honda', 'country_of_origin': 'Japan', 'founded_year': 1948},
        {'name': 'Nissan', 'country_of_origin': 'Japan', 'founded_year': 1933},
        {'name': 'Ford', 'country_of_origin': 'USA', 'founded_year': 1903},
        {'name': 'Chevrolet', 'country_of_origin': 'USA', 'founded_year': 1911},
        {'name': 'Hyundai', 'country_of_origin': 'South Korea', 'founded_year': 1967},
        {'name': 'Kia', 'country_of_origin': 'South Korea', 'founded_year': 1944},
        {'name': 'Lexus', 'country_of_origin': 'Japan', 'founded_year': 1989},
        {'name': 'Porsche', 'country_of_origin': 'Germany', 'founded_year': 1931}
    ]
    
    brands = []
    for data in brands_data:
        brand, created = Brand.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        brands.append(brand)
        if created:
            print(f"Created brand: {brand.name}")
    
    # Vehicle Models
    models_data = [
        # Toyota
        {'brand': 'Toyota', 'name': 'Camry'},
        {'brand': 'Toyota', 'name': 'Corolla'},
        {'brand': 'Toyota', 'name': 'RAV4'},
        {'brand': 'Toyota', 'name': 'Prius'},
        {'brand': 'Toyota', 'name': 'Land Cruiser'},
        # BMW
        {'brand': 'BMW', 'name': '3 Series'},
        {'brand': 'BMW', 'name': '5 Series'},
        {'brand': 'BMW', 'name': 'X3'},
        {'brand': 'BMW', 'name': 'X5'},
        # Mercedes-Benz
        {'brand': 'Mercedes-Benz', 'name': 'C-Class'},
        {'brand': 'Mercedes-Benz', 'name': 'E-Class'},
        {'brand': 'Mercedes-Benz', 'name': 'GLC'},
        {'brand': 'Mercedes-Benz', 'name': 'S-Class'},
        # Audi
        {'brand': 'Audi', 'name': 'A4'},
        {'brand': 'Audi', 'name': 'A6'},
        {'brand': 'Audi', 'name': 'Q5'},
        {'brand': 'Audi', 'name': 'Q7'},
        # Honda
        {'brand': 'Honda', 'name': 'Civic'},
        {'brand': 'Honda', 'name': 'Accord'},
        {'brand': 'Honda', 'name': 'CR-V'},
        # Nissan
        {'brand': 'Nissan', 'name': 'Altima'},
        {'brand': 'Nissan', 'name': 'Sentra'},
        {'brand': 'Nissan', 'name': 'Rogue'},
        # Ford
        {'brand': 'Ford', 'name': 'F-150'},
        {'brand': 'Ford', 'name': 'Mustang'},
        {'brand': 'Ford', 'name': 'Explorer'},
        # Hyundai
        {'brand': 'Hyundai', 'name': 'Elantra'},
        {'brand': 'Hyundai', 'name': 'Sonata'},
        {'brand': 'Hyundai', 'name': 'Tucson'}
    ]
    
    models = []
    for data in models_data:
        brand = Brand.objects.get(name=data['brand'])
        model, created = VehicleModel.objects.get_or_create(
            brand=brand,
            name=data['name']
        )
        models.append(model)
        if created:
            print(f"Created model: {model.brand.name} {model.name}")
    
    return fuel_types, transmission_types, categories, brands, models


def create_vehicle_specifications(fuel_types, transmission_types, categories, models):
    """Create vehicle specifications."""
    print("Creating vehicle specifications...")
    
    specifications = []
    years = [2020, 2021, 2022, 2023, 2024]
    
    for model in models[:15]:  # Create specs for first 15 models
        for year in random.sample(years, random.randint(2, 4)):
            spec_data = {
                'model': model,
                'year': year,
                'category': random.choice(categories),
                'engine_capacity': Decimal(str(round(random.uniform(1.0, 6.0), 1))),
                'transmission': random.choice(transmission_types),
                'fuel_type': random.choice(fuel_types),
                'horsepower': random.randint(150, 500),
                'torque': random.randint(200, 600),
                'drive_type': random.choice(['FWD', 'RWD', 'AWD']),
                'acceleration': Decimal(str(round(random.uniform(4.0, 12.0), 1))),
                'top_speed': random.randint(180, 300),
                'fuel_economy': Decimal(str(round(random.uniform(6.0, 15.0), 1))),
                'seating_capacity': random.choice([2, 4, 5, 7, 8]),
                'doors': random.choice([2, 4, 5]),
                'weight': random.randint(1200, 2500)
            }
            
            spec, created = VehicleSpecification.objects.get_or_create(
                model=model,
                year=year,
                defaults=spec_data
            )
            specifications.append(spec)
            if created:
                print(f"Created specification: {spec}")
    
    return specifications


def create_vehicle_listings(users, specifications):
    """Create vehicle listings."""
    print("Creating vehicle listings...")
    
    # Get seller users
    sellers = [user for user in users if user.role in [UserRole.SELLER, UserRole.ADMIN]]
    
    cities = ['Dubai', 'Abu Dhabi', 'Sharjah', 'Ajman', 'Ras Al Khaimah', 'Fujairah', 'Umm Al Quwain']
    colors = ['White', 'Black', 'Silver', 'Gray', 'Blue', 'Red', 'Green', 'Brown', 'Gold']
    
    listings = []
    for i in range(50):  # Create 50 listings
        spec = random.choice(specifications)
        seller = random.choice(sellers)
        city = random.choice(cities)
        
        # Generate realistic mileage based on year
        current_year = datetime.now().year
        age = current_year - spec.year
        base_mileage = age * random.randint(10000, 25000)
        mileage = max(0, base_mileage + random.randint(-5000, 10000))
        
        # Generate realistic price
        base_price = random.randint(50000, 500000)
        depreciation = age * 0.15  # 15% per year
        price = max(base_price * (1 - depreciation), base_price * 0.3)
        
        listing_data = {
            'title': f"{spec.model.brand.name} {spec.model.name} {spec.year}",
            'user': seller,
            'vehicle_specification': spec,
            'condition': random.choice([ConditionType.NEW, ConditionType.USED, ConditionType.CERTIFIED_PRE_OWNED]),
            'mileage': int(mileage),
            'price': Decimal(str(int(price))),
            'price_type': random.choice([PriceType.FIXED, PriceType.NEGOTIABLE]),
            'location_city': city,
            'location_country': 'UAE',
            'description': f"Excellent condition {spec.model.brand.name} {spec.model.name} {spec.year}. Well maintained with full service history. Perfect for daily commuting or family use.",
            'color_exterior': random.choice(colors),
            'color_interior': random.choice(['Black', 'Beige', 'Gray', 'Brown']),
            'status': random.choice([ListingStatus.ACTIVE, ListingStatus.ACTIVE, ListingStatus.ACTIVE, ListingStatus.SOLD]),  # More active listings
            'is_featured': random.choice([True, False, False, False]),  # 25% featured
            'is_premium': random.choice([True, False, False]),  # 33% premium
            'views_count': random.randint(0, 500),
            'inquiries_count': random.randint(0, 20)
        }
        
        listing, created = VehicleListing.objects.get_or_create(
            title=listing_data['title'],
            user=seller,
            defaults=listing_data
        )
        listings.append(listing)
        if created:
            print(f"Created listing: {listing.title}")
    
    return listings


def create_inquiries_and_reviews(users, listings):
    """Create inquiries and reviews."""
    print("Creating inquiries and reviews...")
    
    # Get client users
    clients = [user for user in users if user.role in [UserRole.CLIENT, UserRole.USER]]
    
    # Create inquiries
    for i in range(30):
        listing = random.choice(listings)
        client = random.choice(clients)
        
        inquiry_data = {
            'listing': listing,
            'user': client,
            'inquiry_type': random.choice(['general', 'price', 'inspection', 'test_drive']),
            'message': random.choice([
                'I am interested in this vehicle. Is it still available?',
                'Can you provide more details about the service history?',
                'Is the price negotiable?',
                'Can I schedule a test drive?',
                'What is the reason for selling?'
            ]),
            'phone_number': client.phone_number,
            'preferred_contact_time': random.choice(['morning', 'afternoon', 'evening', 'anytime'])
        }
        
        inquiry, created = ListingInquiry.objects.get_or_create(
            listing=listing,
            user=client,
            defaults=inquiry_data
        )
        
        if created:
            print(f"Created inquiry for: {listing.title}")
            
            # Create response for some inquiries
            if random.choice([True, False]):
                response_data = {
                    'inquiry': inquiry,
                    'user': listing.user,
                    'message': random.choice([
                        'Yes, the vehicle is still available. Please contact me to arrange a viewing.',
                        'Thank you for your interest. The vehicle has full service history.',
                        'The price is slightly negotiable. Please call me to discuss.',
                        'I can arrange a test drive this weekend. Please let me know your availability.'
                    ])
                }
                
                InquiryResponse.objects.create(**response_data)
    
    # Create vehicle reviews
    for i in range(20):
        client = random.choice(clients)
        listing = random.choice(listings)
        
        review_data = {
            'user': client,
            'vehicle_specification': listing.vehicle_specification,
            'overall_rating': random.randint(3, 5),
            'performance_rating': random.randint(3, 5),
            'comfort_rating': random.randint(3, 5),
            'fuel_economy_rating': random.randint(3, 5),
            'reliability_rating': random.randint(3, 5),
            'value_rating': random.randint(3, 5),
            'title': f"Great experience with {listing.vehicle_specification.model.brand.name} {listing.vehicle_specification.model.name}",
            'review_text': random.choice([
                'Excellent vehicle with great performance and comfort.',
                'Very reliable car, perfect for daily use.',
                'Good fuel economy and smooth driving experience.',
                'Comfortable interior and advanced features.',
                'Great value for money, highly recommended.'
            ]),
            'ownership_duration': random.choice(['less_than_6_months', '6_months_to_1_year', '1_to_2_years', '2_to_5_years']),
            'is_verified_owner': random.choice([True, False])
        }
        
        review, created = VehicleReview.objects.get_or_create(
            user=client,
            vehicle_specification=listing.vehicle_specification,
            defaults=review_data
        )
        
        if created:
            print(f"Created review for: {listing.vehicle_specification}")


def create_saved_listings_and_views(users, listings):
    """Create saved listings and listing views."""
    print("Creating saved listings and views...")
    
    # Create saved listings
    clients = [user for user in users if user.role in [UserRole.CLIENT, UserRole.USER]]
    
    for client in clients:
        # Each client saves 3-8 random listings
        saved_count = random.randint(3, 8)
        saved_listings = random.sample(listings, min(saved_count, len(listings)))
        
        for listing in saved_listings:
            saved, created = SavedListing.objects.get_or_create(
                user=client,
                listing=listing,
                defaults={'notes': 'Interested in this vehicle'}
            )
            if created:
                print(f"Created saved listing: {client.email} -> {listing.title}")
    
    # Create listing views
    for listing in listings:
        # Each listing gets 10-100 views
        view_count = random.randint(10, 100)
        
        for _ in range(view_count):
            viewer = random.choice(users) if random.choice([True, False]) else None
            ip_address = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
            
            view_data = {
                'listing': listing,
                'user': viewer,
                'ip_address': ip_address,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'viewed_at': timezone.now() - timedelta(days=random.randint(0, 30))
            }
            
            ListingView.objects.create(**view_data)


def create_subscription_plans():
    """Create subscription plans."""
    print("Creating subscription plans...")
    
    plans_data = [
        {
            'name': 'Basic',
            'description': 'Basic listing features',
            'price': Decimal('99.00'),
            'duration_days': 30,
            'max_listings': 5,
            'featured_listings': 0,
            'premium_support': False,
            'analytics_access': False,
            'is_active': True
        },
        {
            'name': 'Professional',
            'description': 'Professional features for dealers',
            'price': Decimal('299.00'),
            'duration_days': 30,
            'max_listings': 25,
            'featured_listings': 5,
            'premium_support': True,
            'analytics_access': True,
            'is_active': True
        },
        {
            'name': 'Enterprise',
            'description': 'Enterprise solution for large dealers',
            'price': Decimal('599.00'),
            'duration_days': 30,
            'max_listings': 100,
            'featured_listings': 20,
            'premium_support': True,
            'analytics_access': True,
            'is_active': True
        }
    ]
    
    plans = []
    for data in plans_data:
        plan, created = SubscriptionPlan.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        plans.append(plan)
        if created:
            print(f"Created subscription plan: {plan.name}")
    
    return plans


def create_notifications(users):
    """Create sample notifications."""
    print("Creating notifications...")
    
    notification_types = [
        ('listing_approved', 'Your listing has been approved'),
        ('new_inquiry', 'You have a new inquiry'),
        ('price_alert', 'Price drop alert for saved listing'),
        ('system_update', 'System maintenance scheduled'),
        ('welcome', 'Welcome to YallaMotor!')
    ]
    
    for user in users[:5]:  # Create notifications for first 5 users
        for i in range(random.randint(2, 5)):
            notification_type, title = random.choice(notification_types)
            
            notification_data = {
                'user': user,
                'title': title,
                'message': f"This is a sample {notification_type} notification for {user.first_name}.",
                'notification_type': notification_type,
                'is_read': random.choice([True, False])
            }
            
            Notification.objects.create(**notification_data)
            print(f"Created notification for: {user.email}")


def main():
    """Main function to create all dummy data."""
    print("Starting dummy data creation...")
    print("=" * 50)
    
    try:
        # Create users
        users = create_users()
        print(f"Created {len(users)} users")
        
        # Create vehicle master data
        fuel_types, transmission_types, categories, brands, models = create_vehicle_master_data()
        print(f"Created {len(fuel_types)} fuel types, {len(transmission_types)} transmission types")
        print(f"Created {len(categories)} categories, {len(brands)} brands, {len(models)} models")
        
        # Create vehicle specifications
        specifications = create_vehicle_specifications(fuel_types, transmission_types, categories, models)
        print(f"Created {len(specifications)} vehicle specifications")
        
        # Create vehicle listings
        listings = create_vehicle_listings(users, specifications)
        print(f"Created {len(listings)} vehicle listings")
        
        # Create inquiries and reviews
        create_inquiries_and_reviews(users, listings)
        
        # Create saved listings and views
        create_saved_listings_and_views(users, listings)
        
        # Create subscription plans
        plans = create_subscription_plans()
        print(f"Created {len(plans)} subscription plans")
        
        # Create notifications
        create_notifications(users)
        
        print("=" * 50)
        print("Dummy data creation completed successfully!")
        print("\nTest Accounts Created:")
        print("-" * 30)
        print("Admin: admin@yallamotor.com / admin123")
        print("Staff: staff@yallamotor.com / staff123")
        print("Seller 1: seller1@example.com / seller123")
        print("Seller 2: seller2@example.com / seller123")
        print("Dealer: dealer@example.com / dealer123")
        print("Client 1: client1@example.com / client123")
        print("Client 2: client2@example.com / client123")
        print("User 1: user1@example.com / user123")
        print("User 2: user2@example.com / user123")
        print("Buyer: buyer@example.com / buyer123")
        
    except Exception as e:
        print(f"Error creating dummy data: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()