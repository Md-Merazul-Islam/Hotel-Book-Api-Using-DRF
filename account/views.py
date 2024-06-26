from decimal import Decimal
from django.contrib.auth.models import User
from django.shortcuts import render, redirect,get_object_or_404
from rest_framework import viewsets
from . models import UserAccount
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.encoding import force_bytes
from . serializers import UserAccountSerializer, UserRegistrationSerializer, UserLoginSerializer,AllUserSerializer
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import  EmailMultiAlternatives
from django.contrib.auth import authenticate, login, logout
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework import  status
from django.contrib.auth import get_user_model


class AllUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = AllUserSerializer



    
class UserAccountViewSet(viewsets.ModelViewSet):
    serializer_class = UserAccountSerializer
    permission_classes = [IsAuthenticated]  

    def get_queryset(self):
        if self.request.user.is_authenticated:
 
            return UserAccount.objects.filter(user=self.request.user)
        else:
            return UserAccount.objects.none()  

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


    
    
    
class UserRegistrationSerializerViewSet(APIView):
    serializer_class = UserRegistrationSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            print(user)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            confirm_link = f"https://blueskybooking.onrender.com/user/active/{uid}/{token}"
            email_subject = "Confirm Your Email"
            email_body = render_to_string(
                'confirm_email.html', {'confirm_link': confirm_link})

            email = EmailMultiAlternatives(email_subject, '', to=[user.email])
            email.attach_alternative(email_body, "text/html")

            email.send()

            return Response('Check your email for confirmation')
        return Response(serializer.errors)



User = get_user_model()

def activate(request, uid64, token):
    try:
        uid = urlsafe_base64_decode(uid64).decode()
    except (TypeError, ValueError, UnicodeDecodeError):
        return redirect('verified_unsuccess')

    user = get_object_or_404(User, pk=uid)

    if default_token_generator.check_token(user, token):
        if not user.is_active:  
            user.is_active = True
            user.save()
        return redirect('verified_success')
    else:
        return redirect('verified_unsuccess')




class UserLoginApiView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=self.request.data)

        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(username=username, password=password)

            if user:
                token, _ = Token.objects.get_or_create(user=user)
                print(token, _)
                login(request, user)
                return Response({'token': token.key, 'user_id': user.id})
            else:
                return Response({'error': 'Invalid Credentials'})
        return Response(serializer.errors)


class UserLogoutApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.auth_token:
            request.user.auth_token.delete()
        logout(request)
        return redirect('login')


class DepositCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        amount = Decimal(request.data.get('amount', 0.0))
        if amount <500:
             return Response({'error': 'Minimum you need deposit 500 tk.'}, status=status.HTTP_400_BAD_REQUEST)
            

        try:
            user_account = user.account
        except UserAccount.DoesNotExist:
            return Response({'error': 'User account not found.'}, status=status.HTTP_400_BAD_REQUEST)

        user_account.balance += amount  
        user_account.save()

        # Send confirmation email
        email_subject = "Deposit Confirmation"
        email_body = render_to_string('deposit_confirm_email.html', {
            'user': user.username,
            'amount': amount,
        })
        email = EmailMultiAlternatives(email_subject, '', to=[user.email])
        email.attach_alternative(email_body, "text/html")
        email.send()

        return Response({'message': 'Deposit successful.'}, status=status.HTTP_201_CREATED)
    
    
    
    
    
#add success or fail message 
def successful(request):
    return render(request,'successful.html')
    
# add unsuccessful message 
def unsuccessful(request):
    return render(request,'unsuccessful.html')
