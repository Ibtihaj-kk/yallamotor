from django.db import models
from django.utils.text import slugify


class FuelType(models.Model):
    """Fuel type model (e.g., Petrol, Diesel, Electric)."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    icon = models.ImageField(upload_to='fuel_types/icons/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class TransmissionType(models.Model):
    """Transmission type model (e.g., Automatic, Manual, CVT)."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    icon = models.ImageField(upload_to='transmission_types/icons/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Brand(models.Model):
    """Vehicle brand/manufacturer model."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    logo = models.ImageField(upload_to='brands/logos/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    country_of_origin = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    founded_year = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class VehicleModel(models.Model):
    """Vehicle model belonging to a brand."""
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, blank=True)
    image = models.ImageField(upload_to='models/images/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['brand__name', 'name']
        unique_together = ['brand', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.brand.name}-{self.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.brand.name} {self.name}"


class VehicleCategory(models.Model):
    """Vehicle category (e.g., Sedan, SUV, Truck)."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    icon = models.ImageField(upload_to='categories/icons/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Vehicle Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class VehicleSpecification(models.Model):
    """Vehicle specification template for a model."""
    model = models.ForeignKey(VehicleModel, on_delete=models.CASCADE, related_name='specifications')
    year = models.PositiveIntegerField()
    category = models.ForeignKey(VehicleCategory, on_delete=models.SET_NULL, null=True, blank=True)
    engine_type = models.CharField(max_length=100, blank=True, null=True)
    engine_capacity = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True)  # in liters
    transmission = models.ForeignKey(TransmissionType, on_delete=models.SET_NULL, null=True, blank=True, related_name='specifications')
    fuel_type = models.ForeignKey(FuelType, on_delete=models.SET_NULL, null=True, blank=True, related_name='specifications')
    horsepower = models.PositiveIntegerField(blank=True, null=True)
    torque = models.PositiveIntegerField(blank=True, null=True)  # in Nm
    drive_type = models.CharField(max_length=50, blank=True, null=True)  # FWD, RWD, AWD
    acceleration = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)  # 0-100 km/h in seconds
    top_speed = models.PositiveIntegerField(blank=True, null=True)  # in km/h
    fuel_economy = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)  # in L/100km
    seating_capacity = models.PositiveSmallIntegerField(blank=True, null=True)
    body_style = models.CharField(max_length=50, blank=True, null=True)
    doors = models.PositiveSmallIntegerField(blank=True, null=True)
    weight = models.PositiveIntegerField(blank=True, null=True)  # in kg
    length = models.PositiveIntegerField(blank=True, null=True)  # in mm
    width = models.PositiveIntegerField(blank=True, null=True)  # in mm
    height = models.PositiveIntegerField(blank=True, null=True)  # in mm
    wheelbase = models.PositiveIntegerField(blank=True, null=True)  # in mm
    ground_clearance = models.PositiveIntegerField(blank=True, null=True)  # in mm
    trunk_capacity = models.PositiveIntegerField(blank=True, null=True)  # in liters
    fuel_tank_capacity = models.PositiveIntegerField(blank=True, null=True)  # in liters
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['model', 'year']
        ordering = ['-year']

    def __str__(self):
        return f"{self.model} {self.year}"


class VehicleFeature(models.Model):
    """Features that can be associated with vehicle specifications."""
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True, null=True)  # e.g., Safety, Comfort, Technology
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # FontAwesome or similar icon name
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class VehicleSpecificationFeature(models.Model):
    """Many-to-many relationship between vehicle specifications and features."""
    specification = models.ForeignKey(VehicleSpecification, on_delete=models.CASCADE, related_name='features')
    feature = models.ForeignKey(VehicleFeature, on_delete=models.CASCADE)
    is_standard = models.BooleanField(default=True)  # True if standard, False if optional
    additional_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Cost if optional
    notes = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ['specification', 'feature']

    def __str__(self):
        return f"{self.specification} - {self.feature}"
