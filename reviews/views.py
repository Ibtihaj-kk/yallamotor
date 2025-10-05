from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Avg
from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .models import VehicleReview, DealerReview, ReviewImage, ReviewVote, ReviewComment
from .serializers import (
    VehicleReviewListSerializer,
    VehicleReviewDetailSerializer,
    VehicleReviewCreateUpdateSerializer,
    DealerReviewListSerializer,
    DealerReviewDetailSerializer,
    DealerReviewCreateUpdateSerializer,
    ReviewCommentSerializer,
    ReviewVoteCreateSerializer
)
from vehicles.models import VehicleModel


class VehicleReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for vehicle reviews."""
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['title', 'content', 'pros', 'cons']
    filterset_fields = ['vehicle_model', 'status', 'user']
    ordering_fields = ['created_at', 'overall_rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # By default, only show approved reviews to the public
        queryset = VehicleReview.objects.all()
        
        # If user is staff or admin, they can see all reviews
        user = self.request.user
        if not (user.is_authenticated and (user.is_staff or user.is_superuser)):
            queryset = queryset.filter(status=VehicleReview.ReviewStatus.APPROVED)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VehicleReviewDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return VehicleReviewCreateUpdateSerializer
        return VehicleReviewListSerializer
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Get current user's vehicle reviews."""
        reviews = VehicleReview.objects.filter(user=request.user)
        serializer = VehicleReviewListSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get statistics for vehicle reviews."""
        vehicle_model_id = request.query_params.get('vehicle_model')
        if not vehicle_model_id:
            return Response({'error': 'vehicle_model parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            vehicle_model = VehicleModel.objects.get(id=vehicle_model_id)
        except VehicleModel.DoesNotExist:
            return Response({'error': 'Vehicle model not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get approved reviews for this vehicle model
        reviews = VehicleReview.objects.filter(
            vehicle_model=vehicle_model,
            status=VehicleReview.ReviewStatus.APPROVED
        )
        
        # Calculate average ratings
        avg_ratings = reviews.aggregate(
            avg_overall=Avg('overall_rating'),
            avg_performance=Avg('performance_rating'),
            avg_comfort=Avg('comfort_rating'),
            avg_interior=Avg('interior_rating'),
            avg_reliability=Avg('reliability_rating'),
            avg_value=Avg('value_rating'),
            avg_running_cost=Avg('running_cost_rating')
        )
        
        # Count reviews by rating
        rating_counts = {
            '5': reviews.filter(overall_rating=5).count(),
            '4': reviews.filter(overall_rating=4).count(),
            '3': reviews.filter(overall_rating=3).count(),
            '2': reviews.filter(overall_rating=2).count(),
            '1': reviews.filter(overall_rating=1).count()
        }
        
        return Response({
            'vehicle_model': vehicle_model.name,
            'total_reviews': reviews.count(),
            'average_ratings': avg_ratings,
            'rating_counts': rating_counts
        })


class DealerReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for dealer reviews."""
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['title', 'content', 'pros', 'cons']
    filterset_fields = ['dealer', 'status', 'user']
    ordering_fields = ['created_at', 'overall_rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # By default, only show approved reviews to the public
        queryset = DealerReview.objects.all()
        
        # If user is staff or admin, they can see all reviews
        user = self.request.user
        if not (user.is_authenticated and (user.is_staff or user.is_superuser)):
            queryset = queryset.filter(status=DealerReview.ReviewStatus.APPROVED)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DealerReviewDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return DealerReviewCreateUpdateSerializer
        return DealerReviewListSerializer
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Get current user's dealer reviews."""
        reviews = DealerReview.objects.filter(user=request.user)
        serializer = DealerReviewListSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get statistics for dealer reviews."""
        dealer_id = request.query_params.get('dealer')
        if not dealer_id:
            return Response({'error': 'dealer parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get approved reviews for this dealer
        reviews = DealerReview.objects.filter(
            dealer_id=dealer_id,
            status=DealerReview.ReviewStatus.APPROVED
        )
        
        # Calculate average ratings
        avg_ratings = reviews.aggregate(
            avg_overall=Avg('overall_rating'),
            avg_customer_service=Avg('customer_service_rating'),
            avg_buying_process=Avg('buying_process_rating'),
            avg_price_fairness=Avg('price_fairness_rating'),
            avg_facility=Avg('facility_rating')
        )
        
        # Count reviews by rating
        rating_counts = {
            '5': reviews.filter(overall_rating=5).count(),
            '4': reviews.filter(overall_rating=4).count(),
            '3': reviews.filter(overall_rating=3).count(),
            '2': reviews.filter(overall_rating=2).count(),
            '1': reviews.filter(overall_rating=1).count()
        }
        
        return Response({
            'dealer_id': dealer_id,
            'total_reviews': reviews.count(),
            'average_ratings': avg_ratings,
            'rating_counts': rating_counts
        })


class ReviewCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for review comments."""
    serializer_class = ReviewCommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        # Filter comments by review type and ID
        review_type = self.request.query_params.get('review_type')
        review_id = self.request.query_params.get('review_id')
        
        queryset = ReviewComment.objects.all()
        
        if review_type and review_id:
            if review_type == 'vehicle':
                queryset = queryset.filter(vehicle_review_id=review_id)
            elif review_type == 'dealer':
                queryset = queryset.filter(dealer_review_id=review_id)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        # Extract review type and ID from request data
        review_type = request.data.get('review_type')
        review_id = request.data.get('review_id')
        content = request.data.get('content')
        
        if not all([review_type, review_id, content]):
            return Response(
                {'error': 'review_type, review_id, and content are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create comment based on review type
        try:
            if review_type == 'vehicle':
                review = VehicleReview.objects.get(id=review_id)
                comment = ReviewComment.objects.create(
                    user=request.user,
                    vehicle_review=review,
                    content=content
                )
            elif review_type == 'dealer':
                review = DealerReview.objects.get(id=review_id)
                comment = ReviewComment.objects.create(
                    user=request.user,
                    dealer_review=review,
                    content=content
                )
            else:
                return Response(
                    {'error': 'Invalid review_type. Must be "vehicle" or "dealer".'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (VehicleReview.DoesNotExist, DealerReview.DoesNotExist):
            return Response(
                {'error': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReviewVoteViewSet(viewsets.GenericViewSet):
    """ViewSet for review votes."""
    serializer_class = ReviewVoteCreateSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def vote(self, request):
        """Vote on a review."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vote = serializer.save()
        
        return Response({'status': 'vote recorded'}, status=status.HTTP_201_CREATED)
