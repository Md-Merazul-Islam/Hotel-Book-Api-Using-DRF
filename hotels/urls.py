from django.urls import path
from .views import (
    DistrictListAPIView, DistrictDetailAPIView,
    HotelListAPIView, HotelDetailAPIView,
    ReviewListCreateAPIView, ReviewDetailAPIView,
    BookingDetailAPIView,AllReviewsListAPIView,
    download_booking_pdf,BookingListAPIView,BookHotelView
)

urlpatterns = [
    path('districts/', DistrictListAPIView.as_view(), name='district-list'),
    path('districts/<int:pk>/', DistrictDetailAPIView.as_view(), name='district-detail'),
    path('hotels/', HotelListAPIView.as_view(), name='hotel-list'),
    path('hotels/<int:pk>/', HotelDetailAPIView.as_view(), name='hotel-detail'),
    path('download-booking-pdf/<int:booking_id>/', download_booking_pdf, name='download_booking_pdf'),
    path('<int:hotel_id>/review/', ReviewListCreateAPIView.as_view(), name='hotel-review-list-create'),
    path('review/<int:pk>/', ReviewDetailAPIView.as_view(), name='review-detail'),
    path('reviews/', AllReviewsListAPIView.as_view(), name='all-reviews-list'),
    path('book/', BookHotelView.as_view(), name='book_hotel'),
    path('bookings/', BookingListAPIView.as_view(), name='booking-list'),
    
]



# {
#   "hotel_id": 1,
#   "start_date": "2024-07-05",
#   "end_date": "2024-07-07",
#   "number_of_rooms": 2,
#   "user_id": 13
# }
