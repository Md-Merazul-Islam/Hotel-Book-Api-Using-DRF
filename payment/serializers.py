from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import transaction
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from hotels.models import Booking, Hotel
from account.models import UserAccount
from sslcommerz_lib import SSLCOMMERZ 
import uuid
from datetime import datetime


def generate_transaction_id():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_id = uuid.uuid4().hex[:6].upper()
    return f'TXN-{timestamp}-{unique_id}'


class PaymentSerializer(serializers.Serializer):
    hotel_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    number_of_rooms = serializers.IntegerField()
    user_id = serializers.IntegerField()

    def validate(self, data):
        hotel_id = data.get('hotel_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        number_of_rooms = data.get('number_of_rooms')
        user_id = data.get('user_id')

        try:
            hotel = Hotel.objects.get(id=hotel_id)
        except Hotel.DoesNotExist:
            raise serializers.ValidationError(
                {'error': _('Hotel does not exist')})

        try:
            user_account = UserAccount.objects.get(user_id=user_id)
        except UserAccount.DoesNotExist:
            raise serializers.ValidationError(
                {'error': _('User account does not exist')})

        total_days = (end_date - start_date).days
        total_cost = hotel.price_per_night * number_of_rooms * total_days

        if total_days <= 0:
            raise serializers.ValidationError(
                {'error': _('Invalid booking dates')})

        if user_account.balance < total_cost:
            raise serializers.ValidationError(
                {'error': _('Insufficient balance')})

        if hotel.available_room < number_of_rooms:
            raise serializers.ValidationError(
                {'error': _('Not enough rooms available')})

        data['hotel'] = hotel
        data['user_account'] = user_account
        data['total_cost'] = total_cost
        return data

    def create(self, validated_data):
        try:
            user_id = validated_data.pop('user_id')
            user_account = validated_data['user_account']
            total_cost = validated_data['total_cost']
            number_of_rooms = validated_data['number_of_rooms']
            start_date = validated_data['start_date']
            end_date = validated_data['end_date']

            with transaction.atomic():
                # Deduct balance from user account (if required)
                # user_account.balance -= total_cost
                # user_account.save(update_fields=['balance'])

                # Decrease available rooms in hotel

                # Initiate payment gateway process
                transaction_id = generate_transaction_id()

                settings = {
                    'store_id': 'your_store_id_here',
                    'store_pass': 'your_store_pass_here',
                    'issandbox': True  # Set to False for production environment
                }

                sslcz = SSLCOMMERZ(settings)

                # Prepare post body for SSLCOMMERZ session creation
                hotel = validated_data['hotel']
                post_body = {
                    'total_amount': total_cost,
                    'currency': "BDT",
                    'tran_id': transaction_id,
                    'success_url': 'https://blueskybooking.onrender.com/payment/success',
                    'fail_url': 'https://blueskybooking.onrender.com/payment/fail',
                    'cancel_url': 'https://blueskybooking.onrender.com/payment/cancel',
                    'emi_option': 0,
                    'cus_name': user_account.user.first_name,
                    'cus_email': user_account.user.email,
                    'cus_phone': "01401734642",  # Update with user's phone number
                    'cus_add1': "Mymensingh ",  # Update with user's address
                    'cus_city': "Dhaka",  # Update with user's city
                    'cus_country': "Bangladesh",  # Update with user's country
                    'shipping_method': "NO",
                    'num_of_item': number_of_rooms,
                    'product_name': hotel.name,
                    'product_category': "Room",
                    'product_profile': "general"
                }

                # Create SSLCOMMERZ session
                response = sslcz.createSession(post_body)

                if response.get('status') == 'SUCCESS':
                    gateway_url = response['GatewayPageURL']

                    # Create booking instance (if needed)
                    booking = Booking.objects.create(
                        user_id=user_id,
                        hotel=hotel,
                        start_date=start_date,
                        end_date=end_date,
                        number_of_rooms=number_of_rooms,
                        total_cost=total_cost,
                        transaction_id=transaction_id
                    )

                    hotel = validated_data['hotel']
                    hotel.available_room -= number_of_rooms
                    hotel.save(update_fields=['available_room'])

                    # Sending booking confirmation email
                    email_subject = _("Booking Confirmation")
                    email_body = render_to_string('book_confirm_email.html', {
                        'hotel_name': hotel.name,
                        'start_date': start_date,
                        'end_date': end_date,
                        'total_cost': total_cost,
                        'pdf_link': self.context['request'].build_absolute_uri(reverse('download_booking_pdf', args=[booking.id]))
                    })
                    email = EmailMultiAlternatives(
                        email_subject, '', to=[user_account.user.email])
                    email.attach_alternative(email_body, "text/html")
                    email.send()

                    return {
                        'booking_id': booking.id,
                        'payment_url': gateway_url,
                        'transaction_id': transaction_id
                    }
                else:
                    raise serializers.ValidationError(
                        {'error': _('Failed to create payment session')})

        except Exception as e:
            raise serializers.ValidationError(
                {'error': _('Failed to create booking.')})
