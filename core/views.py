from django.forms import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from core.models import Branch, Center, Client, CreditOfficer, Deposit, Loan,PaymentHistory
from openpyxl import Workbook
from openpyxl.styles import Font
from django.http import HttpResponse, HttpResponseBadRequest
from decimal import Decimal
from datetime import date
from datetime import datetime  
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
import requests
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth import login,logout, authenticate
from django.contrib import messages
from .models import Profile
from django.utils import timezone
from django.utils.timezone import now
from datetime import timedelta
from django.db.models.signals import post_save










def home(request):
    return render(request,'home.html')



def signup_view(request):
    if request.method =='POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('pw')
        confirm_password = request.POST.get('pw-2')
        
        
        if User.objects.filter(username=username):
            messages.error(request, 'Bussiness name already exist')
            return redirect('signup')
        
        
        
        
        if User.objects.filter(email=username):
            messages.error(request, 'Email already exist')
            return redirect('signup')
        
        
        
        
        if User.objects.filter(password=password):
            messages.error(request, 'password already exist')
        
        
        
        if password !=confirm_password:
            messages.error(request, 'Password did not match')
            return redirect('signup')
        
        
        
        user = User.objects.create_user(username,email, password)
        if user is not None:
            login(request, user)
            messages.success(request, ' You have signup successfully')
            return redirect('pricing')
    return render(request, 'signup.html')







def signin_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('pw')

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')

            # Ensure profile exists
            profile, _ = Profile.objects.get_or_create(user=user)

            # Redirect based on subscription
            if profile.is_active:
                return redirect('dashboard')
            else:
                return redirect('pricing')
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('signin')
    return render(request, 'signin.html')




@login_required
def contact_view(request):
    return render(request,'contact.html')






@login_required
def pricing_view(request):
    profile = request.user.profile

    # Redirect paid users to dashboard
    if profile.is_active:
        return redirect("dashboard")

    plans = [
        {"name": "Starter", "price": 5000, "pay_url": "https://paystack.shop/pay/gzu54tykc6"},
        {"name": "Professional", "price": 10000, "pay_url": "https://paystack.shop/pay/b2hi35ebej"},
        {"name": "Business", "price": 25000, "pay_url": "https://paystack.shop/pay/058chi19tu"},
    ]

    return render(request, "pricing.html", {"plans": plans, "hide_navbar": True})






# Define plan durations (in days) and optional prices
PLAN_DURATION_DAYS = {
    'starter': 30,
    'professional': 30,  # adjust as needed
    'business': 30
}

@login_required
def upgrade_plan(request, plan_name):
    profile = get_object_or_404(Profile, user=request.user)

    plan_name = plan_name.lower()
    if plan_name not in PLAN_DURATION_DAYS:
        messages.error(request, "Invalid plan selected.")
        return redirect("dashboard")

    # If user is already on this plan
    if profile.plan.lower() == plan_name and profile.is_active():
        messages.info(request, f"You are already on the {plan_name.title()} plan.")
        return redirect("dashboard")

    # Calculate new expiration date
    now = timezone.now()
    # If current plan is active, extend from paid_until
    if profile.paid_until and profile.paid_until > now:
        new_paid_until = profile.paid_until + timedelta(days=PLAN_DURATION_DAYS[plan_name])
    else:
        new_paid_until = now + timedelta(days=PLAN_DURATION_DAYS[plan_name])

    # Update profile
    profile.plan = plan_name
    profile.is_paid = True
    profile.paid_until = new_paid_until
    profile.save()

    messages.success(request, f"Successfully upgraded to {plan_name.title()} plan. Valid until {new_paid_until.strftime('%d %b %Y')}.")
    return redirect("dashboard")




# Plan durations in days
PLAN_DURATION_DAYS = {
    'starter': 30,
    'professional': 30,
    'business': 30
}

@login_required
def payment_success(request, plan_name):
    """
    Called after successful payment
    Updates user's profile plan and paid_until
    """
    profile = get_object_or_404(Profile, user=request.user)
    plan_name = plan_name.lower()

    if plan_name not in PLAN_DURATION_DAYS:
        messages.error(request, "Invalid plan.")
        return redirect("dashboard")

    now = timezone.now()
    duration_days = PLAN_DURATION_DAYS[plan_name]

    # If the current plan is still active, extend it
    if profile.paid_until and profile.paid_until > now:
        new_paid_until = profile.paid_until + timedelta(days=duration_days)
    else:
        new_paid_until = now + timedelta(days=duration_days)

    profile.plan = plan_name
    profile.is_paid = True
    profile.paid_until = new_paid_until
    profile.save()

    messages.success(request, f"Payment successful! You are now on the {plan_name.title()} plan until {new_paid_until.strftime('%d %b %Y')}.")
    return redirect("dashboard")







@login_required
def pay_view(request, plan_slug):
   
    profile = request.user.profile

    profile.plan = plan_slug
    profile.is_paid = True
    profile.paid_until = timezone.now() + timedelta(days=30)  
    profile.save()

    messages.success(request, f"Payment successful! You are now on the {plan_slug.title()} plan.")
    return redirect("dashboard")




@login_required
def officer_view(request):
    if request.user.is_staff:
        officers = CreditOfficer.objects.all()
        branches = Branch.objects.all()
    else:
        officers = CreditOfficer.objects.filter(user=request.user)
        branches = Branch.objects.filter(user=request.user)

    if request.method == 'POST':
        name = request.POST.get('name')
        branch_id = request.POST.get('branch')

        if not branch_id:
            return render(request, 'credit_officer.html', {
                'branches': branches,
                'officers': officers,
                'error': 'Please select a branch.'
            })

        try:
            if request.user.is_staff:
                branch = Branch.objects.get(id=branch_id)
            else:
                branch = Branch.objects.get(id=branch_id, user=request.user)

            CreditOfficer.objects.create(
                name=name,
                branch=branch,
                user=request.user
            )

            return redirect('officer_view')

        except Branch.DoesNotExist:
            return render(request, 'credit_officer.html', {
                'branches': branches,
                'officers': officers,
                'error': 'Invalid branch selected.'
            })

    return render(request, 'credit_officer.html', {
        'branches': branches,
        'officers': officers
    })





@login_required
def edit_officer_view(request, officer_id):
    officer = get_object_or_404(CreditOfficer, id=officer_id)
    branches = Branch.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        branch_id = request.POST.get('branch')
        branch = Branch.objects.get(id=branch_id)

        # Update the credit officer
        officer.name = name
        officer.branch = branch
        officer.save()

        return redirect('officer_view')  # Redirect to the officer listing page after editing

    # Render the edit form with the current officer data
    return render(request, 'edit_officer.html', {'officer': officer, 'branches': branches})




@login_required
def delete_officer_view(request,id):
    officers = get_object_or_404(CreditOfficer, pk=id)
    officers.delete()
    return redirect('officer_view')





@login_required
def center_view(request):
    if request.user.is_staff:
        centers = Center.objects.all()
        branches = Branch.objects.all()
    else:
        centers = Center.objects.filter(user=request.user)
        branches = Branch.objects.filter(user=request.user)

    if request.method == 'POST':
        name = request.POST.get('name')
        branch_id = request.POST.get('branch')

        if not branch_id:
            return render(request, 'center.html', {
                'branches': branches,
                'centers': centers,
                'error': 'Please select a branch.'
            })

        try:
            if request.user.is_staff:
                branch = Branch.objects.get(id=branch_id)
            else:
                branch = Branch.objects.get(id=branch_id, user=request.user)

            Center.objects.create(
                name=name,
                branch=branch,
                user=request.user
            )

            return redirect('center_view')

        except Branch.DoesNotExist:
            return render(request, 'center.html', {
                'branches': branches,
                'centers': centers,
                'error': 'Invalid branch selected.'
            })

    return render(request, 'center.html', {
        'branches': branches,
        'centers': centers
    })






@login_required
def edit_center_view(request, center_id):
    # Fetch the center object that you want to edit
    center = get_object_or_404(Center, id=center_id)
    branches = Branch.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        branch_id = request.POST.get('branch')
        branch = Branch.objects.get(id=branch_id)

        # Update the center
        center.name = name
        center.branch = branch
        center.save()

        return redirect('center_view')  # Redirect to the center listing page after editing

    # Render the edit form with current center data
    return render(request, 'edit_center.html', {'center': center, 'branches': branches})


@login_required
def delete_center_view(request, id):
    centers = get_object_or_404(Center,pk=id)
    centers.delete()
    return redirect('center_view')


@login_required
def branch_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        Branch.objects.create(
            name=name,
            user=request.user
        )
        return redirect('branch_view')

    if request.user.is_staff:
        branches = Branch.objects.all()
    else:
        branches = Branch.objects.filter(user=request.user)

    return render(request, 'branch.html', {'branches': branches})





@login_required
def edit_branch_view(request, branch_id):
    # Fetch the branch object to edit
    branch = get_object_or_404(Branch, id=branch_id)

    if request.method == 'POST':
        # Update the branch
        branch.name = request.POST.get('name')
        branch.save()
        return redirect('branch_view')  # Redirect to the branch listing page

    # Render the edit form with the current branch data
    return render(request, 'edit_branch.html', {'branch': branch})


@login_required
def delete_branch_view(request, id):
    branchs = get_object_or_404(Branch, pk=id)
    branchs.delete()
    return redirect('branch_view')





def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    profile = request.user.profile  # current user profile

    if request.user.is_staff:
        clients = Client.objects.all()
        deposits = Deposit.objects.all()
        loans = Loan.objects.all()
    else:
        clients = Client.objects.filter(user=request.user)
        deposits = Deposit.objects.filter(client__user=request.user)  # adjust if needed
        loans = Loan.objects.filter(client__user=request.user)        # FIXED

    total_clients = clients.count()
    total_deposit = deposits.count()
    total_loan = loans.count()

    plans = [
        {"name": "Starter", "pay_url": "https://paystack.shop/pay/gzu54tykc6"},
        {"name": "Professional", "pay_url": "https://paystack.shop/pay/b2hi35ebej"},
        {"name": "Business", "pay_url": "https://paystack.shop/pay/058chi19tu"},
    ]

    context = {
        'total_clients': total_clients,
        'total_deposit': total_deposit,
        'total_loan': total_loan,
        'profile': profile,
        'plans': plans, 
    }
    return render(request, 'dashboard.html', context)





@login_required
def transaction(request):

    if request.user.is_staff:
        clients = Client.objects.all()
    else:
        clients = Client.objects.filter(user=request.user)

    # FILTER VALUES
    branch_id = request.GET.get("branch")
    center_id = request.GET.get("center")
    officer_id = request.GET.get("officer")

    # APPLY FILTERS
    if branch_id:
        clients = clients.filter(branch_id=branch_id)

    if center_id:
        clients = clients.filter(center_id=center_id)

    if officer_id:
        clients = clients.filter(credit_officer_id=officer_id)

    report_data = []

    for client in clients:
        reg = Deposit.objects.filter(client=client, product="REGSAVG").first()
        vol = Deposit.objects.filter(client=client, product="VOLSAVG").first()
        loan = Loan.objects.filter(client=client).first()

        if not loan:
            continue

        report_data.append({
            "client": client,
            "reg_balance": reg.balance if reg else 0,
            "vol_balance": vol.balance if vol else 0,
            "total_deposit": (reg.collected if reg else 0) + (vol.collected if vol else 0),
            "loan": loan,
        })

    context = {
        "report_data": report_data,
        "branches": Branch.objects.all(),
        "centers": Center.objects.all(),
        "officers": CreditOfficer.objects.all(),
    }

    return render(request, "transaction.html", context)



#  HELPER FUNCTION


@login_required
def save_deposit(client, product, expected, collected):
    deposit, created = Deposit.objects.get_or_create(
        client=client, product=product, 
        defaults={'expected': expected, 'collected': collected}
    )
    if not created:  # If deposit already exists, update it
        deposit.expected = expected
        deposit.collected = collected
        deposit.save()
    return deposit



# Helper function to create or update loan
@login_required
def save_loan(client, loan_data):
    loan, created = Loan.objects.get_or_create(client=client, defaults=loan_data)
    if not created:  # If loan already exists, update it
        for key, value in loan_data.items():
            setattr(loan, key, value)
        loan.save()
    return loan

#  DELETING VIEW

@login_required
def delete_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    # Ensure the logged-in user is allowed to delete this client
    if not request.user.is_staff and client.credit_officer.user != request.user:
        messages.error(request, "You do not have permission to delete this client.")
        return redirect('client_list')









#  NEW EXCEL DOWNLOAD VIEW
@login_required
def export_feed_excel(request):

    wb = Workbook()
    ws = wb.active
    ws.title = "Feed Collection"

    headers = [
        "ATTN", "CLIENT ID", "NAME",
        "REGSAVG BAL", "VOLSAVG BAL", "TOTAL DEPOSIT",
        "PRINCIPAL", "INTEREST %", "INTEREST",
        "LOAN AMOUNT (P+I)", "OLB",
        "TOTAL INST.", "PAID INST.", "UNPAID INST.",
        "INST. AMOUNT", "OVERDUE", "PAYMENT"
    ]
    ws.append(headers)

    if request.user.is_staff:
        clients = Client.objects.all()
    else:
        clients = Client.objects.filter(user=request.user)

    # SAME FILTERS AS TRANSACTION
    branch_id = request.GET.get("branch")
    center_id = request.GET.get("center")
    officer_id = request.GET.get("officer")

    if branch_id:
        clients = clients.filter(branch_id=branch_id)

    if center_id:
        clients = clients.filter(center_id=center_id)

    if officer_id:
        clients = clients.filter(credit_officer_id=officer_id)

    for client in clients:
        reg = Deposit.objects.filter(client=client, product="REGSAVG").first()
        vol = Deposit.objects.filter(client=client, product="VOLSAVG").first()
        loan = Loan.objects.filter(client=client).first()

        if not loan:
            continue

        ws.append([
            client.credit_officer.name,
            client.client_id,
            client.name,
            float(reg.balance if reg else 0),
            float(vol.balance if vol else 0),
            float((reg.collected if reg else 0) + (vol.collected if vol else 0)),
            float(loan.principal),
            float(loan.interest_rate),
            float(loan.interest_amount),
            float(loan.principal_interest),
            float(loan.olb),
            loan.total_installments,
            loan.paid_installments,
            loan.unpaid_installments,
            float(loan.installment_amount),
            float(loan.overdue),
            float(loan.paid),
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=feed_collection.xlsx"
    wb.save(response)
    return response






# INDIVIDUAL VIEWS
@login_required
def create_client(request):
    if request.method == 'POST':
        # Get data from the form
        client_id = request.POST.get('client_id')
        name = request.POST.get('name')
        branch_id = request.POST.get('branch')
        credit_officer_id = request.POST.get('credit_officer')
        center_id = request.POST.get('center')

        # Fetch the selected instances from the database
        branch = Branch.objects.get(id=branch_id)
        credit_officer = CreditOfficer.objects.get(id=credit_officer_id)
        center = Center.objects.get(id=center_id)

        # Create the new client and associate it with the logged-in user
        new_client = Client(
            client_id=client_id,
            name=name,
            branch=branch,
            credit_officer=credit_officer,
            center=center,
            user=request.user
        )
        new_client.save()

        # Redirect to the client list page after saving
        return redirect('client_list')

    # GET request: Display the form with appropriate dropdown options
    if request.user.is_staff:
        # If the user is an admin, show all options
        branches = Branch.objects.all()
        credit_officers = CreditOfficer.objects.all()
        centers = Center.objects.all()
    else:
        # If the user is a regular user, show only related options
        branches = Branch.objects.filter(user=request.user)
        credit_officers = CreditOfficer.objects.filter(user=request.user)
        centers = Center.objects.filter(user=request.user)

    # Render the form with the dropdown options
    return render(request, 'client_form.html', {
        'branches': branches,
        'credit_officers': credit_officers,
        'centers': centers
    })





# LOAN

@login_required
def create_loan(request):
    if request.method == 'POST':
        # Get data from the form
        client_id = request.POST.get('client')
        product = request.POST.get('product')
        principal = request.POST.get('principal')
        interest_rate = request.POST.get('interest_rate')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        total_installments = request.POST.get('total_installments')

        client = Client.objects.get(id=client_id)

        # Create a new loan
        new_loan = Loan(
            client=client,
            product=product,
            principal=principal,
            interest_rate=interest_rate,
            start_date=start_date,
            end_date=end_date,
            total_installments=total_installments
        )
        new_loan.save()

        return redirect('loan_list')  # Redirect back to the loan form page (or another page)

    # GET request: Display the form
    if request.user.is_staff:
        
        clients = Client.objects.all()
    else:
        
        clients = Client.objects.filter(user=request.user)

    return render(request, 'loan_form.html', {'clients': clients})






@login_required
def edit_loan(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    clients = Client.objects.all()

    if request.method == 'POST':
        loan.client = Client.objects.get(id=request.POST.get('client'))
        loan.product = request.POST.get('product')
        loan.principal = request.POST.get('principal')
        loan.interest_rate = request.POST.get('interest_rate')
        loan.start_date = request.POST.get('start_date')
        loan.end_date = request.POST.get('end_date')
        loan.total_installments = request.POST.get('total_installments')
        loan.save()

        return redirect('create_loan')

    return render(request, 'loan_edit.html', {'loan': loan, 'clients': clients})




# Delete Loan View
@login_required
def delete_loan(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)

    if request.method == 'POST':
        loan.delete()
        return redirect('create_loan')

    return render(request, 'loan_confirm_delete.html', {'loan': loan})




@login_required
def create_deposit(request):
    if request.method == 'POST':
        client_id = request.POST.get('client')
        product = request.POST.get('product')
        expected = request.POST.get('expected')
        collected = request.POST.get('collected')

        if not client_id:
            messages.error(request, "Please select a client.")
            return redirect('create_deposit')

        try:
            if request.user.is_staff:
                client = Client.objects.get(id=client_id)
            else:
                client = Client.objects.get(id=client_id, user=request.user)

            Deposit.objects.create(
                client=client,
                product=product,
                expected=expected,
                collected=collected,
                user=request.user
            )

            messages.success(request, "Deposit created successfully.")
            return redirect('deposit_list')

        except Client.DoesNotExist:
            messages.error(request, "Invalid client selected.")
            return redirect('create_deposit')

    # GET request
    if request.user.is_staff:
        clients = Client.objects.all()
    else:
        clients = Client.objects.filter(user=request.user)

    return render(request, 'deposit_form.html', {'clients': clients})





@login_required
def edit_deposit(request, deposit_id):
    deposit = get_object_or_404(Deposit, id=deposit_id)
    clients = Client.objects.all()

    if request.method == 'POST':
        deposit.client = Client.objects.get(id=request.POST.get('client'))
        deposit.product = request.POST.get('product')
        deposit.expected = request.POST.get('expected')
        deposit.collected = request.POST.get('collected')
        deposit.save()

        return redirect('deposit_list')

    return render(request, 'deposit_edit.html', {'deposit': deposit, 'clients': clients})




# Delete Deposit View
@login_required
def delete_deposit(request, deposit_id):
    deposit = get_object_or_404(Deposit, id=deposit_id)

    if request.method == 'POST':
        deposit.delete()
        return redirect('create_deposit')

    return render(request, 'deposit_confirm_delete.html', {'deposit': deposit})



@login_required
def edit_client(request, client_id):
    # Fetch the client object that the user is trying to edit
    client = get_object_or_404(Client, id=client_id)

    # Check if the logged-in user is an admin, or if the client is assigned to them
    if not request.user.is_staff:  # Non-admin users can only edit their own clients
        if client.credit_officer.user != request.user:
            messages.error(request, "You do not have permission to edit this client.")
            return redirect('client_list')  # Redirect to the client list if unauthorized

    # Fetch necessary data for the form (Branches, Credit Officers, Centers)
    branches = Branch.objects.all()
    credit_officers = CreditOfficer.objects.all()
    centers = Center.objects.all()

    if request.method == 'POST':
        # Get the updated data from the form
        client_id = request.POST.get('client_id')
        name = request.POST.get('name')
        branch_id = request.POST.get('branch')
        credit_officer_id = request.POST.get('credit_officer')
        center_id = request.POST.get('center')

        # Get the related objects based on the form data
        branch = Branch.objects.get(id=branch_id)
        credit_officer = CreditOfficer.objects.get(id=credit_officer_id)
        center = Center.objects.get(id=center_id)

        # Update the client with the new values
        client.client_id = client_id
        client.name = name
        client.branch = branch
        client.credit_officer = credit_officer
        client.center = center
        client.save()

        messages.success(request, "Client details updated successfully.")
        return redirect('client_list')  # Redirect to the client list page after update

    # If it's a GET request, just render the form with the current client data
    return render(request, 'client_edit.html', {
        'client': client,
        'branches': branches,
        'credit_officers': credit_officers,
        'centers': centers
    })
    
    
    
# Delete Client View
@login_required
def delete_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    if request.method == 'POST':
        client.delete()
        return redirect('client_list')  

    return render(request, 'client_confirm_delete.html', {'client': client})


def client_list(request):
    # Filter clients for the logged-in user
    if request.user.is_staff:  # Admin can see all clients
        clients = Client.objects.all()
    else:
        clients = Client.objects.filter(user=request.user)  # Only clients assigned to this user
    
    return render(request, 'client_list.html', {'clients': clients})



@login_required
def deposit_list(request):
    if request.user.is_staff:
        deposits = Deposit.objects.all()  # Admin sees all deposits
    else:
        deposits = Deposit.objects.filter(user=request.user)  # Only deposits for clients assigned to the user

    # Manually filter duplicates
    seen = set()
    unique_deposits = []

    for deposit in deposits:
        if (deposit.client, deposit.product) not in seen:
            unique_deposits.append(deposit)
            seen.add((deposit.client, deposit.product))

    return render(request, 'deposit_list.html', {'deposits': unique_deposits})





@login_required
def loan_list(request):
    if request.user.is_staff:
        loans = Loan.objects.all()
    else:
        # Only loans for the logged-in user’s clients
        loans = Loan.objects.filter(client__user=request.user)

    return render(request, 'loan_list.html', {'loans': loans})




# POST PAYMENT

@login_required
def post_payment(request):
    if request.user.is_superuser:
        clients = Client.objects.all()
        loans = Loan.objects.all()
    else:
        clients = Client.objects.filter(user=request.user)
        loans = Loan.objects.filter(client__user=request.user)  # FIXED

    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        loan_id = request.POST.get('loan_id')
        recorded_by = request.POST.get('recorded_by')
        amount = request.POST.get('amount')

        # Validate client and loan
        client = get_object_or_404(Client, id=client_id, user=request.user if not request.user.is_superuser else None)
        loan = get_object_or_404(Loan, id=loan_id, client=client)

        # Validate amount
        try:
            amount = Decimal(amount)
        except:
            messages.error(request, "Invalid amount")
            return redirect("post_payment")

        if amount <= 0:
            messages.error(request, "Payment must be greater than 0")
            return redirect("post_payment")

        if amount > loan.olb:
            messages.error(request, "Payment exceeds outstanding balance")
            return redirect("post_payment")

        # Save payment
        PaymentHistory.objects.create(
            client=client,
            loan=loan,
            amount=amount,
            payment_date=datetime.now().date(),
            recorded_by=recorded_by
        )

        # Update loan
        loan.paid += amount
        if loan.installment_amount > 0:
            loan.paid_installments = min(
                loan.total_installments,
                loan.paid_installments + int(amount / loan.installment_amount)
            )
        loan.last_paid = datetime.now().date()
        loan.save()

        messages.success(request, "Payment posted successfully")
        return redirect("payment_history")

    return render(request, "post_payment.html", {'clients': clients, 'loans': loans})





@login_required
def update_payment(request, payment_id):
    # Admin can edit any payment, normal user only their own
    if request.user.is_superuser:
        payment = get_object_or_404(PaymentHistory, id=payment_id)
        clients = Client.objects.all()
        loans = Loan.objects.all()
    else:
        payment = get_object_or_404(PaymentHistory, id=payment_id, loan__client__user=request.user)
        clients = Client.objects.filter(user=request.user)
        loans = Loan.objects.filter(client__user=request.user)

    if request.method == "POST":
        client_id = request.POST.get("client_id")
        loan_id = request.POST.get("loan_id")
        raw_amount = request.POST.get("amount", "0")

        # Validate client
        if request.user.is_superuser:
            client = get_object_or_404(Client, id=client_id)
            loan = get_object_or_404(Loan, id=loan_id, client=client)
        else:
            client = get_object_or_404(Client, id=client_id, user=request.user)
            loan = get_object_or_404(Loan, id=loan_id, client__user=request.user)

        # Validate amount
        try:
            amount = Decimal(raw_amount)
        except:
            messages.error(request, "Invalid payment amount")
            return redirect("update_payment", payment_id=payment.id)

        if amount <= 0:
            messages.error(request, "Payment must be greater than 0")
            return redirect("update_payment", payment_id=payment.id)

        if amount > loan.olb + payment.amount:  # allow editing previous amount
            messages.error(request, "Payment exceeds outstanding balance")
            return redirect("update_payment", payment_id=payment.id)

        # Adjust previous loan paid amount
        loan.paid -= payment.amount  # remove old payment

        # Update payment record
        payment.amount = amount
        payment.client = client
        payment.loan = loan
        payment.payment_date = now().date()
        payment.recorded_by = request.user.username
        payment.save()

        # Recalculate loan paid and installments
        loan.paid += amount
        if loan.installment_amount > 0:
            loan.paid_installments = min(
                loan.total_installments,
                int(loan.paid / loan.installment_amount)
            )
        loan.last_paid = now().date()
        loan.save()

        messages.success(request, "Payment updated successfully")
        return redirect("payment_history")

    return render(request, "post_payment.html", {
        "clients": clients,
        "loans": loans,
        "payment": payment
    })






@login_required
def delete_payment(request, payment_id):
    payment = get_object_or_404(PaymentHistory, id=payment_id, loan__user=request.user)
    loan = payment.loan

    # Reverse payment effect on loan
    loan.paid -= payment.amount
    if loan.installment_amount > 0:
        loan.paid_installments = min(
            loan.total_installments,
            int(loan.paid / loan.installment_amount)
        )
    loan.save()

    payment.delete()
    messages.success(request, "Payment deleted successfully")
    return redirect("payment_history")




@login_required
def payment_history(request):
    try:
        if request.user.is_superuser:
            payments = PaymentHistory.objects.all().order_by('-payment_date')
        else:
            payments = PaymentHistory.objects.filter(
                loan__client__user=request.user
            ).order_by('-payment_date')

        return render(request, "payment_history.html", {"payments": payments})
    
    except Exception as e:
        return render(request, "payment_history.html", {
            "error": "An error occurred while fetching payment history."
        })
