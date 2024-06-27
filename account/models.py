from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    account_no = models.IntegerField(unique=True)
    profile_image = models.ImageField(upload_to='account/images', blank=True, null=True)
    
    def __str__(self) -> str:
        return f'{self.user.username} : {self.account_no}'
    
    
class Deposit (models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12,decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} on {self.timestamp}"
    
    
    
    




TRANSACTION_TYPE = [
    ("Deposit", "Deposit"), 
    ("Pay", "Pay"),
]
class Transaction(models.Model):

    account = models.ForeignKey(UserAccount, related_name='transactions', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after_transaction = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(choices=TRANSACTION_TYPE, max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    
    
    
    
    