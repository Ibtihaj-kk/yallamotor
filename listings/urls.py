from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import VehicleListingViewSet, SavedListingViewSet

app_name = 'listings'

router = DefaultRouter()
router.register(r'listings', VehicleListingViewSet)
router.register(r'saved-listings', SavedListingViewSet, basename='saved-listings')

urlpatterns = [
    path('', include(router.urls)),
]