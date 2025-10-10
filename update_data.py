import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yallamotor_project.settings')
django.setup()

from listings.models import VehicleListing

# Update active listings to published
updated_count = VehicleListing.objects.filter(status='active').update(status='published')
print(f"Updated {updated_count} listings to published status")

# Set first 5 published listings as featured
listings_to_feature = VehicleListing.objects.filter(status='published', is_featured=False)[:5]
featured_count = 0
for listing in listings_to_feature:
    listing.is_featured = True
    listing.save()
    featured_count += 1
print(f"Set {featured_count} listings as featured")

# Print current counts
published_count = VehicleListing.objects.filter(status='published').count()
featured_total = VehicleListing.objects.filter(is_featured=True).count()

print(f"Total published listings: {published_count}")
print(f"Total featured listings: {featured_total}")