

from .models import Booking, Hotel
from rest_framework import status
from xhtml2pdf import pisa
from django.shortcuts import get_object_or_404, render
import os
from django.conf import settings
from django.http import HttpResponse
from datetime import datetime
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Hotel, District, Review, Booking
from .serializers import HotelSerializer, ReviewSerializer, DistrictSerializer, BookingSerializer
from account.models import UserAccount
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
import json


class DistrictListAPIView(generics.ListCreateAPIView):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class DistrictDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class HotelFilter(filters.FilterSet):
    district_name = filters.CharFilter(
        field_name='district__district_name', lookup_expr='icontains')
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Hotel
        fields = ['district_name', 'name']


class HotelListAPIView(generics.ListCreateAPIView):
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = HotelFilter


class HotelDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class BookingDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]


def download_booking_pdf(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    start_date = booking.start_date
    end_date = booking.end_date
    days = (end_date - start_date).days

    if days <= 0:
        return HttpResponse('Invalid booking dates', status=400)

    total_cost = booking.hotel.price_per_night * days * booking.number_of_rooms

    context = {
        'booking': booking,
        'total_cost': total_cost,
    }

    # Render the booking details HTML template to
    html_string = render_to_string('booking_details.html', context)

    # Create HTTP response with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=Booking_Confirmation_{booking.id}.pdf'

    # Generate PDF from HTML string using xhtml2pdf
    pisa_status = pisa.CreatePDF(
        html_string, dest=response,
        link_callback=lambda uri, _: os.path.join(
            settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ''))
    )

    # Check for errors during PDF generation
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html.escape(html_string) + '</pre>')

    return response


class ReviewListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['rating']

    def get_queryset(self):
        hotel_id = self.kwargs.get('hotel_id')
        return Review.objects.filter(hotel__id=hotel_id)

    def perform_create(self, serializer):
        hotel_id = self.kwargs.get('hotel_id')
        hotel = generics.get_object_or_404(Hotel, pk=hotel_id)
        serializer.save(user=self.request.user, hotel=hotel)


class ReviewDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        if self.request.user != self.get_object().user:
            raise permissions.PermissionDenied(
                "You can only edit your own reviews.")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.user:
            raise permissions.PermissionDenied(
                "You can only delete your own reviews.")
        instance.delete()


class AllReviewsListAPIView(generics.ListAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# class BookingHotelView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request):
#         try:
#             data = json.loads(request.body)
#             hotel_id = data.get('hotel_id')
#             start_date = data.get('start_date')
#             end_date = data.get('end_date')
#             number_of_rooms = int(data.get('number_of_rooms', 1))
#         except json.JSONDecodeError:
#             return Response({'error': 'Invalid JSON format.'}, status=status.HTTP_400_BAD_REQUEST)

#         # Validate and parse dates
#         try:
#             start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
#             end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
#             if start_date >= end_date:
#                 return Response({'error': 'End date must be after start date.'}, status=status.HTTP_400_BAD_REQUEST)
#         except ValueError:
#             return Response({'error': 'Invalid date format.'}, status=status.HTTP_400_BAD_REQUEST)

#         # Fetch the hotel object
#         hotel = get_object_or_404(Hotel, id=hotel_id)

#         # Fetch the user from the request
#         user = request.user

#         # Check for existing bookings by the user for the same hotel and dates
#         existing_booking = Booking.objects.filter(
#             user=user,
#             hotel=hotel,
#             start_date=start_date,
#             end_date=end_date,
#             number_of_rooms=number_of_rooms
#         ).exists()

#         if existing_booking:
#             return Response({'error': 'You have already booked this hotel for these dates and number of rooms.'}, status=status.HTTP_400_BAD_REQUEST)

#         # Calculate the total cost
#         days = (end_date - start_date).days
#         total_cost = hotel.price_per_night * days * number_of_rooms

#         # Check room availability
#         if hotel.available_room < number_of_rooms:
#             return Response({'error': 'Not enough rooms available.'}, status=status.HTTP_400_BAD_REQUEST)

#         # Check user account balance
#         try:
#             user_account = user.account
#         except UserAccount.DoesNotExist:
#             return Response({'error': 'User account not found.'}, status=status.HTTP_400_BAD_REQUEST)

#         if user_account.balance < total_cost:
#             return Response({'error': 'Insufficient funds in balance.'}, status=status.HTTP_400_BAD_REQUEST)

#         # Create the booking data dictionary
#         booking_data = {
#             'user': user.id,
#             'hotel': hotel.id,
#             'start_date': start_date,
#             'end_date': end_date,
#             'number_of_rooms': number_of_rooms,
#         }

#         # Serialize the booking data
#         serializer = BookingSerializer(data=booking_data)

#         if serializer.is_valid():
#             booking = serializer.save()
#             # Deduct the cost from the user's account balance
#             user_account.balance -= total_cost
#             user_account.save()

#             # Update the hotel's available rooms
#             hotel.available_room -= number_of_rooms
#             hotel.save()

#             # Send booking confirmation email
#             email_subject = "Booking Confirmation"
#             email_body = render_to_string('book_confirm_email.html', {
#                 'hotel_name': hotel.name,
#                 'start_date': start_date,
#                 'end_date': end_date,
#                 'total_cost': total_cost,
#                 'pdf_link': request.build_absolute_uri(reverse('download_booking_pdf', args=[booking.id]))
#             })
#             email = EmailMultiAlternatives(email_subject, '', to=[user.email])
#             email.attach_alternative(email_body, "text/html")
#             email.send()

#             return Response({'message': 'Booking confirmed. Check your email for details.'}, status=status.HTTP_201_CREATED)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# ----------------------------------------------------





# from rest_framework import status, permissions
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from django.shortcuts import get_object_or_404
# from django.core.mail import EmailMultiAlternatives
# from django.template.loader import render_to_string
# from django.urls import reverse
# from datetime import datetime
# from .models import Booking, Hotel
# from .serializers import BookingSerializer
# import json

# class BookingHotelView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
    

#     def post(self, request):
#         try:
#             data = request.data  # Use DRF's request.data to access parsed JSON data
#             hotel_id = data.get('hotel_id')
#             start_date = data.get('start_date')
#             end_date = data.get('end_date')
#             number_of_rooms = int(data.get('number_of_rooms', 1))
#         except ValueError:
#             return Response({'error': 'Invalid data format.'}, status=status.HTTP_400_BAD_REQUEST)

#         # Validate and parse dates
#         try:
#             start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
#             end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
#             if start_date >= end_date:
#                 return Response({'error': 'End date must be after start date.'}, status=status.HTTP_400_BAD_REQUEST)
#         except ValueError:
#             return Response({'error': 'Invalid date format.'}, status=status.HTTP_400_BAD_REQUEST)

#         # Fetch the hotel object
#         hotel = get_object_or_404(Hotel, id=hotel_id)

#         # Fetch the user from the request
#         user = request.user

#         # Check for existing bookings by the user for the same hotel and dates
#         existing_booking = Booking.objects.filter(
#             user=user,
#             hotel=hotel,
#             start_date=start_date,
#             end_date=end_date,
#             number_of_rooms=number_of_rooms
#         ).exists()

#         if existing_booking:
#             return Response({'error': 'You have already booked this hotel for these dates and number of rooms.'}, status=status.HTTP_400_BAD_REQUEST)

#         # Calculate the total cost
#         days = (end_date - start_date).days
#         total_cost = hotel.price_per_night * days * number_of_rooms

#         # Check room availability
#         if hotel.available_room < number_of_rooms:
#             return Response({'error': 'Not enough rooms available.'}, status=status.HTTP_400_BAD_REQUEST)

#         # Check user account balance
#         try:
#             user_account = user.account
#         except UserAccount.DoesNotExist:
#             return Response({'error': 'User account not found.'}, status=status.HTTP_400_BAD_REQUEST)

#         if user_account.balance < total_cost:
#             return Response({'error': 'Insufficient funds in balance.'}, status=status.HTTP_400_BAD_REQUEST)

#         # Create the booking data dictionary
#         booking_data = {
#             'user': user.id,
#             'hotel': hotel.id,
#             'start_date': start_date,
#             'end_date': end_date,
#             'number_of_rooms': number_of_rooms,
#         }

#         # Serialize the booking data
#         serializer = BookingSerializer(data=booking_data)

#         if serializer.is_valid():
#             booking = serializer.save()
#             # Deduct the cost from the user's account balance
#             user_account.balance -= total_cost
#             user_account.save()

#             # Update the hotel's available rooms
#             hotel.available_room -= number_of_rooms
#             hotel.save()

#             # Send booking confirmation email
#             email_subject = "Booking Confirmation"
#             email_body = render_to_string('book_confirm_email.html', {
#                 'hotel_name': hotel.name,
#                 'start_date': start_date,
#                 'end_date': end_date,
#                 'total_cost': total_cost,
#                 'pdf_link': request.build_absolute_uri(reverse('download_booking_pdf', args=[booking.id]))
#             })
#             email = EmailMultiAlternatives(email_subject, '', to=[user.email])
#             email.attach_alternative(email_body, "text/html")
#             email.send()

#             return Response({'message': 'Booking confirmed. Check your email for details.'}, status=status.HTTP_201_CREATED)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


















# -------------------------


# from rest_framework import status
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from .models import Booking
# from .serializers import BookingSerializer

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def book_hotel(request):
#     serializer = BookingSerializer(data=request.data)
#     if serializer.is_valid():
#         serializer.save(user=request.user)  # Automatically associate the logged-in user
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# from rest_framework import status
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# # from .models import Booking, Hotel, UserAccount
# from .serializers import BookingSerializer
# from django.db import transaction

# @api_view(['POST'])
# # @permission_classes([IsAuthenticated])
# def book_hotel(request):
#     user = request.user
#     try:
#         user_account = user.account
#     except UserAccount.DoesNotExist:
#         return Response({'error': 'User account not found'}, status=status.HTTP_400_BAD_REQUEST)

#     serializer = BookingSerializer(data=request.data)
#     if serializer.is_valid():
#         hotel_id = serializer.validated_data['hotel'].id
#         number_of_rooms = serializer.validated_data['number_of_rooms']
#         start_date = serializer.validated_data['start_date']
#         end_date = serializer.validated_data['end_date']

#         try:
#             hotel = Hotel.objects.get(id=hotel_id)
#         except Hotel.DoesNotExist:
#             return Response({'error': 'Hotel not found'}, status=status.HTTP_400_BAD_REQUEST)

#         total_days = (end_date - start_date).days
#         total_cost = hotel.price_per_night * number_of_rooms * total_days

#         if user_account.balance < total_cost:
#             return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)

#         if hotel.available_room < number_of_rooms:
#             return Response({'error': 'Not enough rooms available'}, status=status.HTTP_400_BAD_REQUEST)

#         # Use a transaction to ensure atomicity
#         with transaction.atomic():
#             # Deduct balance
#             user_account.balance -= total_cost
#             user_account.save()

#             # Decrease available rooms
#             hotel.available_room -= number_of_rooms
#             hotel.save()

#             # Save the booking
#             booking = serializer.save(user=user)
#              # Send booking confirmation email
#             email_subject = "Booking Confirmation"
#             email_body = render_to_string('book_confirm_email.html', {
#                 'hotel_name': hotel.name,
#                 'start_date': start_date,
#                 'end_date': end_date,
#                 'total_cost': total_cost,
#                 'pdf_link': request.build_absolute_uri(reverse('download_booking_pdf', args=[booking.id]))
#             })
#             email = EmailMultiAlternatives(email_subject, '', to=[user.email])
#             email.attach_alternative(email_body, "text/html")
#             email.send()

#             # return Response({'message': 'Booking confirmed. Check your email for details.'}, status=status.HTTP_201_CREATED)
#             return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)

#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -------------------------------


# views.py

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from django.shortcuts import get_object_or_404
# from django.db import transaction
# from rest_framework import status
# from .models import Booking, Hotel
# from .serializers import BookingSerializer
# from account.models import UserAccount  


# class BookHotelView(APIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = BookingSerializer

#     def post(self, request, *args, **kwargs):
#         serializer = self.serializer_class(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             try:
#                 booking = serializer.save(user=request.user)
#                 return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)
#             except serializers.ValidationError as e:
#                 return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
#             except Exception as e:
#                 return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)










import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import BookingSerializer

# Set up logging
logger = logging.getLogger(__name__)

class BookHotelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logger.info("Booking request received.")
        
        # Pass the request context to the serializer
        serializer = BookingSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            try:
                # Save the booking if data is valid
                booking = serializer.save()
                
                logger.info(f"Booking successful for user {request.user.username}.")
                return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                # Log any exceptions that occur during the booking process
                logger.error(f"Booking failed: {e}")
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Log validation errors
        logger.warning(f"Validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
