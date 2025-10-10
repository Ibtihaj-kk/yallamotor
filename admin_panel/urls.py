from django.urls import path
from . import views, auth_views

app_name = 'admin_panel'

urlpatterns = [
    # Authentication
    path('login/', auth_views.admin_login_view, name='login'),
    path('logout/', auth_views.admin_logout_view, name='logout'),
    path('setup-2fa/', auth_views.setup_2fa_view, name='setup_2fa'),
    path('disable-2fa/', auth_views.disable_2fa_view, name='disable_2fa'),
    
    # Main dashboard
    path('', views.dashboard_view, name='dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard_alt'),
    path('demo/', views.dashboard_demo_view, name='dashboard_demo'),
    
    # Listings management
    path('listings/', views.listings_management_view, name='listings_management'),
    path('listings/<int:listing_id>/', views.listing_detail_view, name='listing_detail'),
    path('listings/<int:listing_id>/update-status/', views.update_listing_status, name='update_listing_status'),
    path('listings/bulk-update/', views.bulk_update_listings, name='bulk_update_listings'),
    
    # Analytics
    path('analytics/', views.analytics_view, name='analytics'),
    
    # Activity logs
    path('activity-logs/', views.activity_logs_view, name='activity_logs'),
    
    # API endpoints for dashboard widgets
    path('api/stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
    path('api/recent-activity/', views.api_recent_activity, name='api_recent_activity'),
]