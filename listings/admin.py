from django.contrib import admin
from django.utils.html import format_html
from .models import VehicleListing, ListingImage, SavedListing, ListingView


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1
    readonly_fields = ('thumbnail_preview',)
    fields = ('image', 'thumbnail_preview', 'is_primary', 'caption', 'order')
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="150" height="100" />', obj.thumbnail.url)
        return "-"
    thumbnail_preview.short_description = 'Thumbnail Preview'


class ListingViewInline(admin.TabularInline):
    model = ListingView
    extra = 0
    readonly_fields = ('user', 'ip_address', 'user_agent', 'viewed_at')
    fields = ('user', 'ip_address', 'viewed_at')
    can_delete = False
    max_num = 10
    verbose_name_plural = 'Recent Views'
    ordering = ('-viewed_at',)


@admin.register(VehicleListing)
class VehicleListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'vehicle_info', 'price_display', 'status', 'views_display', 'is_featured', 'created_at')
    list_filter = ('status', 'condition', 'is_featured', 'is_premium', 'vehicle_specification__model__brand')
    search_fields = ('title', 'description', 'user__email', 'vin', 'vehicle_specification__model__name', 'vehicle_specification__model__brand__name')
    readonly_fields = ('views_count', 'inquiries_count', 'created_at', 'updated_at')
    inlines = [ListingImageInline, ListingViewInline]
    prepopulated_fields = {'slug': ('title',)}
    list_per_page = 25
    date_hierarchy = 'created_at'
    actions = ['mark_as_featured', 'mark_as_premium', 'mark_as_active', 'mark_as_sold']
    
    def vehicle_info(self, obj):
        return f"{obj.vehicle_specification.model.brand.name} {obj.vehicle_specification.model.name} {obj.vehicle_specification.year}"
    vehicle_info.short_description = 'Vehicle'
    
    def price_display(self, obj):
        return f"${obj.price:,.2f}"
    price_display.short_description = 'Price'
    price_display.admin_order_field = 'price'
    
    def views_display(self, obj):
        return obj.views_count
    views_display.short_description = 'Views'
    views_display.admin_order_field = 'views_count'
    
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
    mark_as_featured.short_description = "Mark selected listings as featured"
    
    def mark_as_premium(self, request, queryset):
        queryset.update(is_premium=True)
    mark_as_premium.short_description = "Mark selected listings as premium"
    
    def mark_as_active(self, request, queryset):
        queryset.update(status='active')
    mark_as_active.short_description = "Mark selected listings as active"
    
    def mark_as_sold(self, request, queryset):
        queryset.update(status='sold')
    mark_as_sold.short_description = "Mark selected listings as sold"
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'user', 'vehicle_specification', 'condition', 'status')
        }),
        ('Pricing and Details', {
            'fields': ('price', 'price_type', 'mileage', 'color_exterior', 'color_interior', 'vin')
        }),
        ('Location', {
            'fields': ('location_city', 'location_state', 'location_country')
        }),
        ('Description and Features', {
            'fields': ('description', 'warranty_information', 'additional_features', 'seller_notes')
        }),
        ('Listing Options', {
            'fields': ('is_featured', 'is_premium', 'expires_at')
        }),
        ('SEO Options', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',),
        }),
        ('Statistics', {
            'fields': ('views_count', 'inquiries_count', 'created_at', 'updated_at')
        }),
    )


@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ('listing', 'image_preview', 'is_primary', 'order', 'created_at')
    list_filter = ('is_primary', 'listing__vehicle_specification__model__brand')
    search_fields = ('listing__title', 'caption')
    readonly_fields = ('image_preview', 'thumbnail_preview')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="75" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Image Preview'
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="100" height="75" />', obj.thumbnail.url)
        return "-"
    thumbnail_preview.short_description = 'Thumbnail Preview'


@admin.register(SavedListing)
class SavedListingAdmin(admin.ModelAdmin):
    list_display = ('user', 'listing', 'created_at')
    search_fields = ('user__email', 'listing__title')
    list_filter = ('created_at',)


@admin.register(ListingView)
class ListingViewAdmin(admin.ModelAdmin):
    list_display = ('listing', 'user', 'ip_address', 'viewed_at')
    list_filter = ('viewed_at', 'listing__vehicle_specification__model__brand')
    search_fields = ('listing__title', 'user__email', 'ip_address')
    readonly_fields = ('listing', 'user', 'ip_address', 'user_agent', 'viewed_at')
    date_hierarchy = 'viewed_at'
