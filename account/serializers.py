from .models import UserAccount
from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from rest_framework import serializers
from .models import Deposit

class UserAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ['id', 'user', 'account_no', 'balance']


class UserRegistrationSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name',
                  'email', 'password', 'confirm_password']

    def save(self):
        username = self.validated_data['username']
        email = self.validated_data['email']
        first_name = self.validated_data['first_name']
        last_name = self.validated_data['last_name']
        password = self.validated_data['password']
        password2 = self.validated_data['confirm_password']
        if password != password2:
            raise serializers.ValidationError(
                {'error': "Password doesn't match"})

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {'error': "Email already exists"})
        user = User(username=username, email=email,
                    first_name=first_name, last_name=last_name)
        print(user)

        user.set_password(password)
        user.is_active = False
        user.save()
        UserAccount.objects.create(
            user=user, balance=0, account_no=int(user.id) + 1000000)
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = ['id', 'user', 'amount', 'timestamp']