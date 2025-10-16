from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Q, Count, Avg
from django.db import models
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
import json

from listings.models import VehicleListing, ListingStatusLog
from users.models import User
from vehicles.models import Brand, VehicleModel
from .models import ActivityLog, ActivityLogType, DashboardWidget
from .utils import (
    log_activity, log_listing_activity, log_bulk_listing_activity,
    log_status_change_activity, log_feature_toggle_activity
)
from .decorators import (
    admin_required, staff_required, can_manage_listings, 
    can_view_analytics, can_view_audit_logs, ajax_admin_required
)
from .session_manager import require_valid_admin_session
from .audit_logger import AdminAuditLogger, audit_admin_action


def is_admin_user(user):
    """Check if user is admin or staff."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def dashboard_demo_view(request):
    """Public demo version of the dashboard for testing."""
    # Get basic statistics
    total_listings = VehicleListing.objects.count()
    published_listings = VehicleListing.objects.filter(status='published').count()
    pending_listings = VehicleListing.objects.filter(status='pending_review').count()
    featured_listings = VehicleListing.objects.filter(is_featured=True).count()
    
    # Get recent listings
    recent_listings = VehicleListing.objects.select_related('user').order_by('-created_at')[:10]
    
    # Get popular makes
    popular_makes = VehicleListing.objects.filter(status='published').values('make').annotate(
        count=models.Count('make')
    ).order_by('-count')[:10]
    
    context = {
        'total_listings': total_listings,
        'published_listings': published_listings,
        'pending_listings': pending_listings,
        'featured_listings': featured_listings,
        'recent_listings': recent_listings,
        'popular_makes': popular_makes,
        'demo_mode': True,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)

@admin_required(min_role='staff')
@require_valid_admin_session
@audit_admin_action(ActivityLogType.VIEW, "Accessed admin dashboard")
def dashboard_view(request):
    """Main admin dashboard view."""
    # Get dashboard statistics
    total_listings = VehicleListing.objects.count()
    published_listings = VehicleListing.objects.filter(status='published').count()
    pending_listings = VehicleListing.objects.filter(status='pending').count()
    featured_listings = VehicleListing.objects.filter(is_featured=True).count()
    
    # Recent activity
    recent_listings = VehicleListing.objects.select_related('user', 'make', 'model').order_by('-created_at')[:10]
    recent_activities = ActivityLog.objects.select_related('user').order_by('-action_time')[:10]
    
    # Popular makes
    popular_makes = VehicleListing.objects.filter(status='published').values('make__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Status distribution
    status_distribution = VehicleListing.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Monthly listings trend (last 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_data = []
    for i in range(6):
        month_start = six_months_ago + timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        count = VehicleListing.objects.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'count': count
        })
    
    context = {
        'total_listings': total_listings,
        'published_listings': published_listings,
        'pending_listings': pending_listings,
        'featured_listings': featured_listings,
        'recent_listings': recent_listings,
        'recent_activities': recent_activities,
        'popular_makes': popular_makes,
        'status_distribution': status_distribution,
        'monthly_data': monthly_data,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)


@can_manage_listings
@require_valid_admin_session
@audit_admin_action(ActivityLogType.VIEW, "Accessed listings management")
def listings_management_view(request):
    """Vehicle listings management view with filtering and bulk operations."""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    make_filter = request.GET.get('make', '')
    featured_filter = request.GET.get('featured', '')
    search_query = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Build queryset
    listings = VehicleListing.objects.select_related('user', 'make', 'model').all()
    
    if status_filter:
        listings = listings.filter(status=status_filter)
    
    if make_filter:
        listings = listings.filter(make_id=make_filter)
    
    if featured_filter == 'true':
        listings = listings.filter(is_featured=True)
    elif featured_filter == 'false':
        listings = listings.filter(is_featured=False)
    
    if search_query:
        listings = listings.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            listings = listings.filter(created_at__date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            listings = listings.filter(created_at__date__lte=date_to_obj)
        except ValueError:
            pass
    
    # Order by creation date (newest first)
    listings = listings.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(listings, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    makes = Brand.objects.all().order_by('name')
    status_choices = VehicleListing.STATUS_CHOICES
    
    context = {
        'page_obj': page_obj,
        'makes': makes,
        'status_choices': status_choices,
        'current_filters': {
            'status': status_filter,
            'make': make_filter,
            'featured': featured_filter,
            'search': search_query,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'admin_panel/listings_management.html', context)


@can_manage_listings
@require_valid_admin_session
@require_http_methods(["POST"])
@csrf_exempt
def bulk_update_listings(request):
    """Handle bulk operations on listings."""
    try:
        data = json.loads(request.body)
        action = data.get('action')
        listing_ids = data.get('listing_ids', [])
        
        if not action or not listing_ids:
            return JsonResponse({'success': False, 'error': 'Missing action or listing IDs'})
        
        listings = VehicleListing.objects.filter(id__in=listing_ids)
        updated_count = 0
        
        if action == 'publish':
            updated_count = listings.update(status='published')
            # Log status changes
            for listing in listings:
                ListingStatusLog.objects.create(
                    listing=listing,
                    old_status=listing.status,
                    new_status='published',
                    changed_by=request.user,
                    reason='Bulk publish operation'
                )
        
        elif action == 'unpublish':
            updated_count = listings.update(status='draft')
            for listing in listings:
                ListingStatusLog.objects.create(
                    listing=listing,
                    old_status=listing.status,
                    new_status='draft',
                    changed_by=request.user,
                    reason='Bulk unpublish operation'
                )
        
        elif action == 'feature':
            updated_count = listings.update(is_featured=True)
        
        elif action == 'unfeature':
            updated_count = listings.update(is_featured=False)
        
        elif action == 'delete':
            updated_count = listings.count()
            listings.delete()
        
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'})
        
        # Log the bulk operation with comprehensive details
        log_bulk_listing_activity(
            user=request.user,
            action_type=ActivityLogType.UPDATE,
            listings=listings,
            action_name=action,
            request=request
        )
        
        return JsonResponse({
            'success': True, 
            'message': f'Successfully {action}ed {updated_count} listings'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@can_manage_listings
@require_valid_admin_session
@audit_admin_action(ActivityLogType.VIEW, "Viewed listing details for listing {listing_id}")
def listing_detail_view(request, listing_id):
    """Detailed view of a single listing for admin management."""
    listing = get_object_or_404(VehicleListing, id=listing_id)
    
    # Get status history
    status_logs = ListingStatusLog.objects.filter(listing=listing).order_by('-changed_at')
    
    # Get related data
    images = listing.images.all()
    videos = listing.videos.all()
    
    context = {
        'listing': listing,
        'status_logs': status_logs,
        'images': images,
        'videos': videos,
        'status_choices': VehicleListing.STATUS_CHOICES,
    }
    
    return render(request, 'admin_panel/listing_detail.html', context)


@can_manage_listings
@require_valid_admin_session
@require_http_methods(["POST"])
def update_listing_status(request, listing_id):
    """Update listing status with logging."""
    listing = get_object_or_404(VehicleListing, id=listing_id)
    new_status = request.POST.get('status')
    reason = request.POST.get('reason', '')
    
    if new_status not in dict(VehicleListing.STATUS_CHOICES):
        messages.error(request, 'Invalid status')
        return redirect('admin_panel:listing_detail', listing_id=listing_id)
    
    old_status = listing.status
    listing.status = new_status
    listing.save()
    
    # Log the status change
    ListingStatusLog.objects.create(
        listing=listing,
        old_status=old_status,
        new_status=new_status,
        changed_by=request.user,
        reason=reason
    )
    
    # Log the status change with comprehensive details
    log_status_change_activity(
        user=request.user,
        listing=listing,
        old_status=old_status,
        new_status=new_status,
        reason=reason,
        request=request
    )
    
    messages.success(request, f'Listing status updated to {new_status}')
    return redirect('admin_panel:listing_detail', listing_id=listing_id)


@can_view_analytics
@require_valid_admin_session
@audit_admin_action(ActivityLogType.VIEW, "Accessed analytics dashboard")
def analytics_view(request):
    """Analytics dashboard for listings."""
    # Time period filter
    period = request.GET.get('period', '30')  # days
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    start_date = timezone.now() - timedelta(days=days)
    
    # Listings created in period
    listings_in_period = VehicleListing.objects.filter(created_at__gte=start_date)
    
    # Daily creation trend
    daily_data = []
    for i in range(days):
        day = start_date + timedelta(days=i)
        count = listings_in_period.filter(
            created_at__date=day.date()
        ).count()
        daily_data.append({
            'date': day.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Status distribution
    status_stats = listings_in_period.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Make distribution
    make_stats = listings_in_period.values('make__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # User activity
    user_stats = listings_in_period.values('user__email').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Average price by make
    price_stats = listings_in_period.filter(
        price__isnull=False
    ).values('make__name').annotate(
        avg_price=Avg('price'),
        count=Count('id')
    ).order_by('-avg_price')[:10]
    
    context = {
        'period': days,
        'daily_data': daily_data,
        'status_stats': status_stats,
        'make_stats': make_stats,
        'user_stats': user_stats,
        'price_stats': price_stats,
        'total_in_period': listings_in_period.count(),
    }
    
    return render(request, 'admin_panel/analytics.html', context)


@can_view_audit_logs
@require_valid_admin_session
@audit_admin_action(ActivityLogType.VIEW, "Accessed activity logs")
def activity_logs_view(request):
    """View activity logs."""
    # Filter parameters
    user_filter = request.GET.get('user', '')
    action_filter = request.GET.get('action', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Build queryset
    logs = ActivityLog.objects.select_related('user').all()
    
    if user_filter:
        logs = logs.filter(user__email__icontains=user_filter)
    
    if action_filter:
        logs = logs.filter(action_type=action_filter)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            logs = logs.filter(action_time__date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            logs = logs.filter(action_time__date__lte=date_to_obj)
        except ValueError:
            pass
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'action_choices': ActivityLogType.choices,
        'current_filters': {
            'user': user_filter,
            'action': action_filter,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'admin_panel/activity_logs.html', context)


# API endpoints for dashboard widgets
@ajax_admin_required
def api_dashboard_stats(request):
    """API endpoint for dashboard statistics."""
    stats = {
        'total_listings': VehicleListing.objects.count(),
        'published_listings': VehicleListing.objects.filter(status='published').count(),
        'pending_listings': VehicleListing.objects.filter(status='pending').count(),
        'featured_listings': VehicleListing.objects.filter(is_featured=True).count(),
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
    }
    return JsonResponse(stats)


@ajax_admin_required
def api_recent_activity(request):
    """API endpoint for recent activity."""
    activities = ActivityLog.objects.select_related('user').order_by('-action_time')[:10]
    data = []
    for activity in activities:
        data.append({
            'user': activity.user.email,
            'action': activity.get_action_type_display(),
            'description': activity.description,
            'time': activity.action_time.isoformat(),
        })
    return JsonResponse({'activities': data})
