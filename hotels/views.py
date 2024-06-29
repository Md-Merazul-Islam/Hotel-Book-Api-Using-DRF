

from rest_framework import generics
from .models import Booking
from .serializers import BookingSerializer
from rest_framework.permissions import IsAuthenticated
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


class BookHotelView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = BookingSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                booking = serializer.save()
                return Response({'message': 'You have successfully booked the hotel.${booking}'}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': 'Failed to book hotel.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookingListAPIView(generics.ListAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)
