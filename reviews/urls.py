from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'reviews'

router = DefaultRouter()
router.register(r'vehicle-reviews', views.VehicleReviewViewSet, basename='vehicle-review')
router.register(r'dealer-reviews', views.DealerReviewViewSet, basename='dealer-review')
router.register(r'comments', views.ReviewCommentViewSet, basename='review-comment')
router.register(r'votes', views.ReviewVoteViewSet, basename='review-vote')

urlpatterns = [
    path('', include(router.urls)),
]