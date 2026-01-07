# models.py
from datetime import date
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.timezone import now
from django.dispatch import receiver
from django.utils import timezone



DEPOSIT_CHOICES = [('REGSAVG','REGSAVG'),('VOLSAVG','VOLSAVG')]

class Branch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200)
    def __str__(self): return self.name

class CreditOfficer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200)
    branch = models.ForeignKey(Branch,on_delete=models.CASCADE)
    def __str__(self): return self.name

class Center(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200)
    branch = models.ForeignKey(Branch,on_delete=models.CASCADE)
    def __str__(self): return self.name

class Client(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    client_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    credit_officer = models.ForeignKey(CreditOfficer, on_delete=models.CASCADE)
    center = models.ForeignKey(Center, on_delete=models.CASCADE)
    date_created = models.DateField(auto_now_add=True)
    def __str__(self): return f"{self.client_id} - {self.name}"

class Deposit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    client = models.ForeignKey(Client,on_delete=models.CASCADE)
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

    # LOAN DEFINITION
    principal = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)  # %

    # PAYMENT TRACKING
    paid = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )  # total amount paid so far

    start_date = models.DateField()
    end_date = models.DateField()

    total_installments = models.IntegerField()
    paid_installments = models.IntegerField(default=0)

    last_paid = models.DateField(null=True, blank=True)

    # =============================
    # CALCULATED FIELDS (READ ONLY)
    # =============================

    @property
    def interest_amount(self):
        """
        Total interest charged on the loan
        """
        return (self.principal * self.interest_rate) / 100

    @property
    def principal_interest(self):
        """
        Total loan obligation (Principal + Interest)
        """
        return self.principal + self.interest_amount

    @property
    def installment_amount(self):
        """
        Amount to be paid per installment
        """
        if self.total_installments > 0:
            return self.principal_interest / self.total_installments
        return 0

    @property
    def olb(self):
        """
        Outstanding Loan Balance
        """
        balance = self.principal_interest - self.paid
        return max(balance, 0)

    @property
    def unpaid_installments(self):
        """
        Remaining installments
        """
        return max(self.total_installments - self.paid_installments, 0)

    @property
    def overdue(self):
        """
        Overdue amount if loan has passed end date
        """
        if self.end_date < date.today() and self.olb > 0:
            return self.olb
        return 0

    def __str__(self):
        return f"{self.client.name} - {self.product}"





class PaymentHistory(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    
    # default to now, callable, no arguments
    payment_date = models.DateField(default=now)
    
    recorded_by = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.client.name} - ₦{self.amount} - {self.payment_date}"





# Define your plans
PLAN_CHOICES = [
    ('starter', 'Starter'),
    ('professonal', 'Professional'),
    ('business', 'Business'),
]

PLAN_CHOICES = [
    ('starter', 'Starter'),
    ('professional', 'Professional'),
    ('business', 'Business'),
]

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='starter')
    is_paid = models.BooleanField(default=False)
    paid_until = models.DateTimeField(null=True, blank=True)

    @property
    def is_active(self):
        """
        Return True if the plan is paid and not expired
        Can now be used in templates and views as profile.is_active
        """
        return self.is_paid and self.paid_until and self.paid_until > timezone.now()

    def __str__(self):
        return f"{self.user.username} ({self.plan})"

        


# Signal to auto-create profile on new user
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)