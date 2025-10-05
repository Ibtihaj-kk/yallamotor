from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import ListingInquiryViewSet, InquiryResponseViewSet, TestDriveRequestViewSet

app_name = 'inquiries'

router = DefaultRouter()
router.register(r'inquiries', ListingInquiryViewSet, basename='inquiries')
router.register(r'responses', InquiryResponseViewSet, basename='responses')
router.register(r'test-drives', TestDriveRequestViewSet, basename='test-drives')

urlpatterns = [
    path('', include(router.urls)),
]