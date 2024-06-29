from django.urls import path
from .views import (
    DistrictListAPIView, DistrictDetailAPIView,
    HotelListAPIView, HotelDetailAPIView,
    ReviewListCreateAPIView, ReviewDetailAPIView,
 BookingDetailAPIView,AllReviewsListAPIView,
    # BookingHotelView,
    download_booking_pdf
)
from . import views

urlpatterns = [
    path('districts/', DistrictListAPIView.as_view(), name='district-list'),
    path('districts/<int:pk>/', DistrictDetailAPIView.as_view(), name='district-detail'),
    path('hotels/', HotelListAPIView.as_view(), name='hotel-list'),
    path('hotels/<int:pk>/', HotelDetailAPIView.as_view(), name='hotel-detail'),
    path('bookings/<int:pk>/', BookingDetailAPIView.as_view(), name='booking-detail'),
    # path('book/', BookingHotelView.as_view(), name='book'),
    path('download-booking-pdf/<int:booking_id>/', download_booking_pdf, name='download_booking_pdf'),
    path('hotels/<int:hotel_id>/reviews/', ReviewListCreateAPIView.as_view(), name='hotel-review-list-create'),
    path('reviews/<int:pk>/', ReviewDetailAPIView.as_view(), name='review-detail'),
    path('reviews/', AllReviewsListAPIView.as_view(), name='all-reviews-list'),
    path('book/', views.BookHotelView.as_view(), name='book_hotel'),
    
]
