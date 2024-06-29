

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
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Booking, Hotel

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['hotel', 'start_date', 'end_date', 'number_of_rooms']

    def validate(self, data):
        """
        Custom validation for the serializer.
        """
        hotel = data['hotel']
        start_date = data['start_date']
        end_date = data['end_date']
        number_of_rooms = data['number_of_rooms']

        # Validate start_date and end_date
        if start_date >= end_date:
            raise serializers.ValidationError("End date must be after start date.")

        # Check if hotel has enough available rooms
        if hotel.available_room < number_of_rooms:
            raise serializers.ValidationError("Not enough rooms available for booking.")

        # Additional validation logic can be added here

        return data

    def create(self, validated_data):
        """
        Create and return a new Booking instance.
        """
        user = self.context['request'].user
        hotel = validated_data['hotel']
        start_date = validated_data['start_date']
        end_date = validated_data['end_date']
        number_of_rooms = validated_data['number_of_rooms']

        # Perform transaction for booking creation
        with transaction.atomic():
            try:
                # Calculate total cost based on hotel price per night
                total_days = (end_date - start_date).days
                total_cost = hotel.price_per_night * number_of_rooms * total_days

                # Check user account balance
                if user.account.balance < total_cost:
                    raise ValidationError("Insufficient balance for booking.")

                # Update hotel availability
                hotel.available_room -= number_of_rooms
                hotel.save()

                # Create the booking instance
                booking = Booking.objects.create(
                    user=user,
                    hotel=hotel,
                    start_date=start_date,
                    end_date=end_date,
                    number_of_rooms=number_of_rooms
                )

                # Deduct amount from user account balance
                user.account.balance -= total_cost
                user.account.save()

                # Send booking confirmation email
                self.send_booking_confirmation_email(user, hotel, start_date, end_date, total_cost, booking)

                return booking

            except Exception as e:
                raise serializers.ValidationError(str(e))

    def send_booking_confirmation_email(self, user, hotel, start_date, end_date, total_cost, booking):
        """
        Send booking confirmation email to the user.
        """
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
