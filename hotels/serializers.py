

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

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['user', 'hotel', 'start_date', 'end_date', 'number_of_rooms']
