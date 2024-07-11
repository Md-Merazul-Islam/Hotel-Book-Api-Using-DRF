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

def booking_success(request):
    return render(request, 'booking_success.html')

def booking_fail(request):
    return render(request, 'booking_fail.html')

def booking_cancel(request):
   
    return render(request, 'booking_cancel.html')
