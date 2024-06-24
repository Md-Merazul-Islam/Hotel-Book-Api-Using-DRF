from django.urls import path
from .views import (
    DistrictListAPIView, DistrictDetailAPIView,
    HotelListAPIView, HotelDetailAPIView,
    ReviewListCreateAPIView, ReviewDetailAPIView,
 BookingDetailAPIView,
    BookingHotelView, download_booking_pdf
)
from . import views

urlpatterns = [
    path('districts/', DistrictListAPIView.as_view(), name='district-list'),
    path('districts/<int:pk>/', DistrictDetailAPIView.as_view(), name='district-detail'),
    path('hotels/', HotelListAPIView.as_view(), name='hotel-list'),
    path('hotels/<int:pk>/', HotelDetailAPIView.as_view(), name='hotel-detail'),
    path('reviews/', ReviewListCreateAPIView.as_view(), name='review-list-create'),
    path('reviews/<int:pk>/', ReviewDetailAPIView.as_view(), name='review-detail'),
    path('bookings/<int:pk>/', BookingDetailAPIView.as_view(), name='booking-detail'),
    path('book-hotel/', BookingHotelView.as_view(), name='book-hotel'),
    path('download-booking-pdf/<int:booking_id>/', download_booking_pdf, name='download_booking_pdf'),
    
]
