
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

class DistrictListAPIView(generics.ListCreateAPIView):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class DistrictDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class HotelFilter(filters.FilterSet):
    district_name = filters.CharFilter(field_name='district__district_name', lookup_expr='icontains')
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

class BookingHotelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        hotel_name = request.data.get('name')
        district_name = request.data.get('district_name')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        number_of_rooms = int(request.data.get('number_of_rooms', 1))

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            if start_date >= end_date:
                return Response({'error': 'End date must be after start date.'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'error': 'Invalid date format.'}, status=status.HTTP_400_BAD_REQUEST)

        hotel = Hotel.objects.filter(
            name=hotel_name, district__district_name=district_name).first()

        if not hotel:
            return Response({'error': 'Hotel not found.'}, status=status.HTTP_404_NOT_FOUND)

        existing_booking = Booking.objects.filter(
            user=user,
            hotel=hotel,
            start_date=start_date,
            end_date=end_date,
            number_of_rooms=number_of_rooms
        ).exists()

        if existing_booking:
            return Response({'error': 'You have already booked this hotel for these dates and number of rooms.'}, status=status.HTTP_400_BAD_REQUEST)

        days = (end_date - start_date).days
        total_cost = hotel.price_per_night * days * number_of_rooms

        if hotel.available_room < number_of_rooms:
            return Response({'error': 'Not enough rooms available.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_account = user.account
        except UserAccount.DoesNotExist:
            return Response({'error': 'User account not found.'}, status=status.HTTP_400_BAD_REQUEST)

        if user_account.balance < total_cost:
            return Response({'error': 'Insufficient funds in balance.'}, status=status.HTTP_400_BAD_REQUEST)

        booking_data = {
            'user': user.id,
            'hotel': hotel.id,
            'start_date': start_date,
            'end_date': end_date,
            'number_of_rooms': number_of_rooms,
        }

        serializer = BookingSerializer(data=booking_data)

        if serializer.is_valid():
            booking = serializer.save()
            user_account.balance -= total_cost
            user_account.save()

            # Deduct the booked rooms from available rooms
            hotel.available_room -= number_of_rooms * days
            hotel.save()

            # Send booking confirmation email
            email_subject = "Booking Confirmation"
            email_body = render_to_string('book_confirm_email.html', {
                'hotel_name': hotel.name,
                'start_date': start_date,
                'end_date': end_date,
                'total_cost': total_cost,
                'pdf_link': request.build_absolute_uri(reverse('download_booking_pdf', args=[booking.id]))
            })
            email = EmailMultiAlternatives(email_subject, '', to=[user.email])
            email.attach_alternative(email_body, "text/html")
            email.send()

            return Response({'message': 'Booking confirmed. Check your email for details.'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa

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
        link_callback=lambda uri, _: os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ''))
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
            raise permissions.PermissionDenied("You can only edit your own reviews.")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.user:
            raise permissions.PermissionDenied("You can only delete your own reviews.")
        instance.delete()



class AllReviewsListAPIView(generics.ListAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]







#     "id": 1,

# {
#     "user":"saim",
#     "name": "Amari Dhaka",
#     "start_date": "2024-06-20",
#     "end_date": "2024-06-25",
#     "number_of_rooms": 2
# }

