from datetime import datetime
from django.db import models
import datetime  
from django.contrib.auth.models import User


# Create your models here.
DEPOSIT_CHOICES = [
    ('REGSAVG', 'REGSAVG'),
    ('VOLSAVG', 'VOLSAVG'),
]

class Branch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name


class CreditOfficer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    def __str__(self):
        return self.name


class Center(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    def __str__(self):
        return self.name


class Client(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    client_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    credit_officer = models.ForeignKey(CreditOfficer, on_delete=models.CASCADE)
    center = models.ForeignKey(Center, on_delete=models.CASCADE)
    date_created = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.client_id} - {self.name}"


class Deposit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    product = models.CharField(max_length=10, choices=DEPOSIT_CHOICES)
    expected = models.DecimalField(max_digits=12, decimal_places=2)
    collected = models.DecimalField(max_digits=12, decimal_places=2)

    @property
    def balance(self):
        return self.expected - self.collected




class Loan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True) 
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    product = models.CharField(max_length=100)

    principal = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)  # %

    paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    start_date = models.DateField()
    end_date = models.DateField()

    total_installments = models.IntegerField()
    paid_installments = models.IntegerField(default=0)

    @property
    def interest_amount(self):
        return (self.principal * self.interest_rate) / 100

    @property
    def principal_interest(self):
        return self.principal + self.interest_amount

    @property
    def installment_amount(self):
        """ Calculate the amount per installment (including principal + interest). """
        if self.total_installments > 0:
            return self.principal_interest / self.total_installments
        return 0

    @property
    def total_paid(self):
        """ Automatically calculates the total paid based on paid installments. """
        return self.installment_amount * self.paid_installments

    @property
    def olb(self):
        """ Outstanding Loan Balance. """
        return self.principal_interest - self.paid

    @property
    def unpaid_installments(self):
        """ Number of installments that haven't been paid yet. """
        return self.total_installments - self.paid_installments

    @property
    def overdue(self):
        """ Overdue amount (amount owed that is past due). """
    # If the loan is past due and there is still an outstanding balance
        if self.end_date < datetime.date.today() and self.olb > 0:
            return self.olb
        return 0

    
    def save(self, *args, **kwargs):
        # Automatically update 'paid' based on 'paid_installments'
        self.paid = self.total_paid
        super().save(*args, **kwargs)


   



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.CharField(max_length=50)  # e.g., 'starter', 'professional', 'business'
    plan_expiry_date = models.DateTimeField()  # The date and time when the user's plan expires

    def __str__(self):
        return self.user.username
