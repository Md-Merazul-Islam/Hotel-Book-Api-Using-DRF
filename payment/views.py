from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from .serializers import PaymentSerializer
from hotels.models import Booking
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

class PaymentViewSet(viewsets.ViewSet):
    def create(self, request):
        serializer = PaymentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            payment_data = serializer.save()
            return Response(payment_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



from django.shortcuts import render

# def booking_success(request):
#     return render(request, 'booking_success.html')


def booking_fail(request):
    return render(request, 'booking_fail.html')

def booking_cancel(request):
   
    return render(request, 'booking_cancel.html')





# views.py
from django.shortcuts import render
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.http import HttpResponse
from hotels.models import Booking
from account.models import UserAccount
from django.db import transaction

def booking_success(request):
    # Extract necessary information from request
    transaction_id = request.GET.get('tran_id')
    status = request.GET.get('status')

    if status == 'VALID':
        try:
            # Fetch booking associated with the transaction ID
            booking = Booking.objects.get(transaction_id=transaction_id)

            # Send booking confirmation email
            email_subject = "Booking Confirmation"
            email_body = render_to_string('book_confirm_email.html', {
                'hotel_name': booking.hotel.name,
                'start_date': booking.start_date,
                'end_date': booking.end_date,
                'total_cost': booking.total_cost,
                'pdf_link': request.build_absolute_uri(reverse('download_booking_pdf', args=[booking.id]))
            })
            email = EmailMultiAlternatives(
                email_subject, '', to=[booking.user.email])
            email.attach_alternative(email_body, "text/html")
            email.send()

            # Render success page
            return render(request, 'booking_success.html', {'booking': booking})
        except Booking.DoesNotExist:
            return HttpResponse('Booking not found.', status=404)
    else:
        return HttpResponse('Invalid transaction.', status=400)
