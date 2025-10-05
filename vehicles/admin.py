from django.contrib import admin
from .models import Brand, VehicleModel, VehicleCategory, VehicleSpecification, VehicleFeature, VehicleSpecificationFeature


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'country_of_origin', 'founded_year', 'is_active')
    list_filter = ('is_active', 'country_of_origin')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(VehicleModel)
class VehicleModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'is_active')
    list_filter = ('brand', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(VehicleCategory)
class VehicleCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(VehicleSpecification)
class VehicleSpecificationAdmin(admin.ModelAdmin):
    list_display = ('model', 'year', 'engine_type', 'transmission', 'fuel_type')
    list_filter = ('year', 'engine_type', 'transmission', 'fuel_type')
    search_fields = ('model__name', 'engine_type')


@admin.register(VehicleFeature)
class VehicleFeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name', 'description')


@admin.register(VehicleSpecificationFeature)
class VehicleSpecificationFeatureAdmin(admin.ModelAdmin):
    list_display = ('specification', 'feature', 'is_standard')
    list_filter = ('is_standard', 'feature__category')
    search_fields = ('specification__model__name', 'feature__name')
