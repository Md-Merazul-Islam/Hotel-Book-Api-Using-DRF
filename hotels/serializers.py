

from rest_framework import serializers
from .models import Hotel, Review, Booking, District

class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'

class HotelSerializer(serializers.ModelSerializer):

    district_name = serializers.SerializerMethodField()

    def get_district_name(self, obj):
        return obj.district.district_name if obj.district else None

    class Meta:
        model = Hotel
        fields = ['id','name','address','district_name','photo','address','description','price_per_night','available_room']


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    hotel = serializers.ReadOnlyField(source='hotel.name')

    class Meta:
        model = Review
        fields = ['id', 'hotel', 'user', 'body', 'created', 'rating']



# class BookingSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Booking
#         fields ='__all__'
        
        
        
# ----------------------------------
from rest_framework import serializers
from .models import Booking

# class BookingSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Booking
#         fields = ['user', 'hotel', 'start_date', 'end_date', 'number_of_rooms']


# serializers.py

# from rest_framework import serializers
# from django.db import transaction
# from django.shortcuts import get_object_or_404
# from rest_framework.response import Response
# from rest_framework import status
# from django.core.mail import EmailMultiAlternatives
# from django.template.loader import render_to_string
# from django.urls import reverse
# from .models import Booking, Hotel
# from account.models import UserAccount  # Assuming your user account model

# class BookingSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Booking
#         fields = ['hotel', 'start_date', 'end_date', 'number_of_rooms']

#     def create(self, validated_data):
#         try:
#             user = self.context['request'].user
#             user_account = user.account
#         except UserAccount.DoesNotExist:
#             raise serializers.ValidationError({'error': 'User account not found'})

#         hotel_id = validated_data['hotel'].id
#         number_of_rooms = validated_data['number_of_rooms']
#         start_date = validated_data['start_date']
#         end_date = validated_data['end_date']

#         hotel = get_object_or_404(Hotel, id=hotel_id)

#         total_days = (end_date - start_date).days
#         total_cost = hotel.price_per_night * number_of_rooms * total_days

#         if user_account.balance < total_cost:
#             raise serializers.ValidationError({'error': 'Insufficient balance'})

#         if hotel.available_room < number_of_rooms:
#             raise serializers.ValidationError({'error': 'Not enough rooms available'})

#         with transaction.atomic():
#             user_account.balance -= total_cost
#             user_account.save()

#             hotel.available_room -= number_of_rooms
#             hotel.save()

#             booking = Booking.objects.create(
#                 user=user,
#                 hotel=hotel,
#                 start_date=start_date,
#                 end_date=end_date,
#                 number_of_rooms=number_of_rooms
#             )

#             # Sending booking confirmation email
#             email_subject = "Booking Confirmation"
#             email_body = render_to_string('book_confirm_email.html', {
#                 'hotel_name': hotel.name,
#                 'start_date': start_date,
#                 'end_date': end_date,
#                 'total_cost': total_cost,
#                 'pdf_link': self.context['request'].build_absolute_uri(reverse('download_booking_pdf', args=[booking.id]))
#             })
#             email = EmailMultiAlternatives(email_subject, '', to=[user.email])
#             email.attach_alternative(email_body, "text/html")
#             email.send()

#             return booking








from rest_framework import serializers
from django.db import transaction
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from .models import Booking, Hotel
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)

class BookingSerializer(serializers.Serializer):
    hotel_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    number_of_rooms = serializers.IntegerField()

    def validate(self, data):
        hotel_id = data.get('hotel_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        number_of_rooms = data.get('number_of_rooms')

        try:
            hotel = Hotel.objects.get(id=hotel_id)
        except Hotel.DoesNotExist:
            raise serializers.ValidationError({'error': 'Hotel does not exist'})

        user_account = self.context['request'].user.account

        total_days = (end_date - start_date).days
        total_cost = hotel.price_per_night * number_of_rooms * total_days

        if user_account.balance < total_cost:
            raise serializers.ValidationError({'error': 'Insufficient balance'})

        if hotel.available_room < number_of_rooms:
            raise serializers.ValidationError({'error': 'Not enough rooms available'})

        data['hotel'] = hotel
        data['user_account'] = user_account
        data['total_cost'] = total_cost
        return data

    def create(self, validated_data):
        try:
            user = self.context['request'].user
            hotel = validated_data['hotel']
            user_account = validated_data['user_account']
            total_cost = validated_data['total_cost']
            number_of_rooms = validated_data['number_of_rooms']
            start_date = validated_data['start_date']
            end_date = validated_data['end_date']

            with transaction.atomic():
                user_account.balance -= total_cost
                user_account.save(update_fields=['balance'])

                hotel.available_room -= number_of_rooms
                hotel.save(update_fields=['available_room'])

                booking = Booking.objects.create(
                    user=user,
                    hotel=hotel,
                    start_date=start_date,
                    end_date=end_date,
                    number_of_rooms=number_of_rooms
                )

                email_subject = "Booking Confirmation"
                email_body = render_to_string('book_confirm_email.html', {
                    'hotel_name': hotel.name,
                    'start_date': start_date,
                    'end_date': end_date,
                    'total_cost': total_cost,
                    'pdf_link': self.context['request'].build_absolute_uri(reverse('download_booking_pdf', args=[booking.id]))
                })
                email = EmailMultiAlternatives(email_subject, '', to=[user.email])
                email.attach_alternative(email_body, "text/html")
                email.send()

            return booking
        except Exception as e:
            logger.error(f"Error creating booking: {str(e)}")
            raise serializers.ValidationError({'error': 'Failed to create booking.'})
