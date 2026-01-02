from django.contrib import admin

from core.models import Branch, Center, Client, CreditOfficer, Deposit, Loan,PaymentHistory

# Register your models here.


admin.site.register(Branch)
admin.site.register(CreditOfficer)
admin.site.register(Center)
admin.site.register(Client)
admin.site.register(Deposit)
admin.site.register(Loan)
admin.site.register(PaymentHistory)
