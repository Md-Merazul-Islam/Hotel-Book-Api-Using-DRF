

from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Hotel, Booking
from .serializers import HotelSerializer
from account.models import UserAccount
from sslcommerz_python_sdk import SSLCOMMERZ
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
import string
import random


def transaction_id(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class PaymentViewSet(viewsets.ViewSet):
    def create(self, request):
        data = request.data

        # Extract user and cart items
        user_id = data.get("user")
        user = get_object_or_404(UserAccount, id=user_id)
        cart_items = CartItem.objects.filter(user=user, ordered=False)

        if not cart_items.exists():
            return Response({"detail": "No items in the cart."}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate total cost
        total_cost = sum(item.product.price *
                         item.quantity for item in cart_items)

        # Generate transaction ID
        tranction = transaction_id()

        # SSLCOMMERZ settings
        settings = {
            'store_id': 'your_store_id_here',
            'store_pass': 'your_store_pass_here',
            'issandbox': True  # Set to False for production environment
        }

        sslcz = SSLCOMMERZ(settings)

        # Prepare post body for SSLCOMMERZ session creation
        post_body = {
            'total_amount': total_cost,
            'currency': "BDT",
            'tran_id': tranction,
            'success_url': 'http://your-success-url/',
            'fail_url': 'http://your-fail-url/',
            'cancel_url': 'http://your-cancel-url/',
            'emi_option': 0,
            'cus_name': user.first_name,
            'cus_email': user.email,
            'cus_phone': "01700000000",  # Update with user's phone number
            'cus_add1': "customer address",  # Update with user's address
            'cus_city': "Dhaka",  # Update with user's city
            'cus_country': "Bangladesh",  # Update with user's country
            'shipping_method': "NO",
            'multi_card_name': "",
            'num_of_item': 1,
            'product_name': "Test Product",
            'product_category': "Test Category",
            'product_profile': "general"
        }

        # Create SSLCOMMERZ session
        response = sslcz.createSession(post_body)

        if response.get('status') == 'SUCCESS':
            gateway_url = response['GatewayPageURL']
            return Response({'payment_url': gateway_url}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': 'Failed to create payment session'}, status=status.HTTP_400_BAD_REQUEST)

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
