from django.forms import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from core.models import Branch, Center, Client, CreditOfficer, Deposit, Loan
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
            return redirect('signin')
    return render(request, 'signup.html')







def signin_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('pw')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful, welcome to your dashboard')

            # Check if user has a profile and whether their plan has expired
            try:
                profile = Profile.objects.get(user=user)

                # Check if the user has a plan and if it's expired
                if profile.plan_expiry_date < timezone.now():
                    # If plan expired, redirect to payment
                    return redirect('payment')
                else:
                    # If user has an active plan, redirect to dashboard
                    return redirect('dashboard')
            except Profile.DoesNotExist:
                # If the user doesn't have a profile, they're a first-time user and need to pay
                return redirect('payment')

        else:
            messages.error(request, 'Invalid username or password')
            return redirect('signin')

    return render(request, 'signin.html')







def contact_view(request):
    return render(request,'contact.html')




def officer_view(request):
    if request.user.is_staff:
        officers = CreditOfficer.objects.all()  # Admin can see all officers
    else:
        officers = CreditOfficer.objects.filter(user=request.user)  # Only officers associated with the user

    branches = Branch.objects.filter(user =request.user)

    if request.method == 'POST':
        name = request.POST.get('name')
        branch_id = request.POST.get('branch')
        
        branch = Branch.objects.get(id=branch_id)
        
        officer = CreditOfficer.objects.create(name=name, branch=branch)
        return redirect('officer')

    return render(request, 'credit_officer.html', {'branches': branches, 'officers': officers})




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



def delete_officer_view(request,id):
    officers = get_object_or_404(CreditOfficer, pk=id)
    officers.delete()
    return redirect('officer_view')



def center_view(request):
    if request.user.is_staff:
        centers = Center.objects.all()
        branches = Branch.objects.all()
        
    else:
        centers = Center.objects.filter(user=request.user)
        branches = Branch.objects.filter(user=request.user)
    if request.method =='POST':
        name = request.POST.get('name')
        branch_id = request.POST.get('branch')
        
        branch =Branch.objects.get(id=branch_id)
        
        center = Center.objects.create(name=name,branch=branch)
        return redirect('center_view')
    return render(request, 'center.html',{'branches':branches,'centers':centers})



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



def delete_center_view(request, id):
    centers = get_object_or_404(Center,pk=id)
    centers.delete()
    return redirect('center_view')



def branch_view(request):
    if request.method =='POST':
        name = request.POST.get('name')
        branch = Branch.objects.create(name=name)
        return redirect('branch_list')
    
    if request.user.is_staff:
        branches = Branch.objects.all()
        
    else:
        
        branches = Branch.objects.filter(user=request.user)
    return render(request,'branch.html',{'branches':branches})



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



def delete_branch_view(request, id):
    branchs = get_object_or_404(Branch, pk=id)
    branchs.delete()
    return redirect('branch_view')





def logout_view(request):
    logout(request)
    return redirect('home')


def dashboard(request):
    if request.user.is_staff:
        
        clients = Client.objects.all()
        deposits = Deposit.objects.all()
        loans = Loan.objects.all()
        total_clients = clients.count()
        total_deposit = deposits.count()
        total_loan = loans.count()
        
    else:
        clients = Client.objects.filter(user=request.user)
        deposits = Deposit.objects.filter(user=request.user)
        loans = Loan.objects.filter(user=request.user)
        total_clients = clients.count()
        total_deposit = deposits.count()
        total_loan = loans.count()
        
    
    
    
    context = {
        'total_clients':total_clients,
        'total_deposit':total_deposit,
        'total_loan':total_loan,
    }
    return render(request, 'dashboard.html',context)




def transaction(request):
    # Get all clients
    if request.user.is_staff:
        clients = Client.objects.all()
        
    else:
         clients = Client.objects.filter(user=request.user)

    report_data = []

    # Loop through clients and gather data for the report
    for client in clients:
        # Get deposits and loan data
        reg = Deposit.objects.filter(client=client, product='REGSAVG').first()
        vol = Deposit.objects.filter(client=client, product='VOLSAVG').first()
        loan = Loan.objects.filter(client=client).first()

        # Calculate deposit balances
        reg_balance = reg.balance if reg else Decimal("0.00")
        vol_balance = vol.balance if vol else Decimal("0.00")
        total_deposit = (reg.collected if reg else 0) + (vol.collected if vol else 0)

        # Calculate loan-related fields
        principal = loan.principal if loan else Decimal("0.00")
        interest_rate = loan.interest_rate if loan else Decimal("0.00")
        interest_amount = loan.interest_amount if loan else Decimal("0.00")
        principal_interest = loan.principal_interest if loan else Decimal("0.00")
        olb = loan.olb if loan else Decimal("0.00")
        total_installments = loan.total_installments if loan else 0
        paid_installments = loan.paid_installments if loan else 0
        unpaid_installments = loan.unpaid_installments if loan else 0
        installment_amount = loan.installment_amount if loan else Decimal("0.00")
        overdue = loan.overdue if loan else Decimal("0.00")
        paid = loan.paid if loan else Decimal("0.00")

        report_data.append({
            'client': client,
            'reg_balance': reg_balance,
            'vol_balance': vol_balance,
            'total_deposit': total_deposit,
            'loan': loan,
            'principal': principal,
            'interest_rate': interest_rate,
            'interest_amount': interest_amount,
            'principal_interest': principal_interest,
            'olb': olb,
            'total_installments': total_installments,
            'paid_installments': paid_installments,
            'unpaid_installments': unpaid_installments,
            'installment_amount': installment_amount,
            'overdue': overdue,
            'paid': paid,
        })

    return render(request, 'transaction.html', {'report_data': report_data})






#  HELPER FUNCTION



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


def save_loan(client, loan_data):
    loan, created = Loan.objects.get_or_create(client=client, defaults=loan_data)
    if not created:  # If loan already exists, update it
        for key, value in loan_data.items():
            setattr(loan, key, value)
        loan.save()
    return loan

#  DELETING VIEW


def delete_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    # Ensure the logged-in user is allowed to delete this client
    if not request.user.is_staff and client.credit_officer.user != request.user:
        messages.error(request, "You do not have permission to delete this client.")
        return redirect('client_list')









#  NEW EXCEL DOWNLOAD VIEW

def export_feed_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Feed Collection"

    headers = [
        # 1️⃣ ATTENTION / FLAG
        "ATTN",

        # 2️⃣ CLIENT IDENTIFICATION
        "Client ID",
        "Name",

        # 3️⃣ SAVINGS / DEPOSITS
        "Deprod1",
        "REGSAVG Bal",
        "Deprod2",
        "VOLSAVG Bal",
        "Total Deposit",

        # 4️⃣ LOAN DEFINITION
        "Loan Prod",
        "Start Date",
        "End Date",

        # 5️⃣ LOAN VALUE & INTEREST
        "Principal",
        "Interest %",
        "Interest",
        "Loan AMT (P+I)",
        "OLB",

        # 6️⃣ REPAYMENT STRUCTURE
        "Total Inst.",
        "Paid Inst.",
        "Unpaid Inst.",
        "Inst. Amount",

        # 7️⃣ PERFORMANCE / RISK
        "Overdue",
        "Payment"
    ]

    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    total_expected_deposit = Decimal("0.00")
    total_repayment_expected = Decimal("0.00")

    clients = Client.objects.all()

    for client in clients:
        reg = Deposit.objects.filter(client=client, product='REGSAVG').first()
        vol = Deposit.objects.filter(client=client, product='VOLSAVG').first()
        loan = Loan.objects.filter(client=client).first()

        # Get Deposit balances
        reg_bal = reg.balance if reg else Decimal("0.00")
        vol_bal = vol.balance if vol else Decimal("0.00")

        # Calculate total deposit
        total_deposit = (reg.collected if reg else 0) + (vol.collected if vol else 0)

        # Add to the overall totals
        total_expected_deposit += total_deposit
        total_repayment_expected += loan.principal_interest if loan else Decimal("0.00")

        # Append the row data for the client
        ws.append([
            # ATTENTION / FLAG
            client.credit_officer.name,

            # CLIENT
            client.client_id,
            client.name,

            # DEPOSITS
            "REGSAVG",
            float(reg_bal),
            "VOLSAVG",
            float(vol_bal),
            float(total_deposit),

            # LOAN DEFINITION
            loan.product if loan else "N/A",
            loan.start_date if loan else "N/A",
            loan.end_date if loan else "N/A",

            # LOAN VALUE & INTEREST
            float(loan.principal) if loan else 0.00,
            float(loan.interest_rate) if loan else 0.00,
            float(loan.interest_amount) if loan else 0.00,
            float(loan.principal_interest) if loan else 0.00,
            float(loan.olb) if loan else 0.00,

            # REPAYMENT STRUCTURE
            loan.total_installments if loan else 0,
            loan.paid_installments if loan else 0,
            loan.unpaid_installments if loan else 0,
            float(loan.installment_amount) if loan else 0.00,

            # PERFORMANCE
            float(loan.overdue) if loan else 0.00,
            float(loan.paid) if loan else 0.00,
        ])

    # Add an empty row for separation
    ws.append([])

    # Add totals row
    ws.append([
        "TOTALS", "", "", "", "", "", "",
        float(total_expected_deposit),
        "", "", "",
        "",
        float(total_repayment_expected),
        "", "", "", "", "", "", "", "", ""
    ])

    for cell in ws[ws.max_row]:
        cell.font = Font(bold=True)

    # Prepare the response for Excel download
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=feed_collection.xlsx"

    wb.save(response)
    return response










# INDIVIDUAL VIEWS

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

        return redirect('create_loan')  # Redirect back to the loan form page (or another page)

    # GET request: Display the form
    if request.user.is_staff:
        
        clients = Client.objects.all()
    else:
        
        clients = Client.objects.filter(user=request.user)

    return render(request, 'loan_form.html', {'clients': clients})







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
def delete_loan(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)

    if request.method == 'POST':
        loan.delete()
        return redirect('create_loan')

    return render(request, 'loan_confirm_delete.html', {'loan': loan})





def create_deposit(request):
    if request.method == 'POST':
        client_id = request.POST.get('client')
        product = request.POST.get('product')
        expected = request.POST.get('expected')
        collected = request.POST.get('collected')

        client = Client.objects.get(id=client_id)

        # Create a new deposit
        new_deposit = Deposit(client=client, product=product, expected=expected, collected=collected)
        new_deposit.save()

        messages.success(request, "Deposit created successfully.")
        return redirect('create_deposit')  # Redirect to the create_deposit page

    # GET request: Display the form
    if request.user.is_staff:
        
        clients = Client.objects.all()
    else:
        
        clients = Client.objects.filter(user=request.user)

    return render(request, 'deposit_form.html', {'clients': clients})



def edit_deposit(request, deposit_id):
    deposit = get_object_or_404(Deposit, id=deposit_id)
    clients = Client.objects.all()

    if request.method == 'POST':
        deposit.client = Client.objects.get(id=request.POST.get('client'))
        deposit.product = request.POST.get('product')
        deposit.expected = request.POST.get('expected')
        deposit.collected = request.POST.get('collected')
        deposit.save()

        return redirect('create_deposit')

    return render(request, 'deposit_edit.html', {'deposit': deposit, 'clients': clients})




# Delete Deposit View
def delete_deposit(request, deposit_id):
    deposit = get_object_or_404(Deposit, id=deposit_id)

    if request.method == 'POST':
        deposit.delete()
        return redirect('create_deposit')

    return render(request, 'deposit_confirm_delete.html', {'deposit': deposit})




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



def loan_list(request):

    if request.user.is_staff:
        loans = Loan.objects.all()  # Admin sees all loans
    else:
        loans = Loan.objects.filter(user=request.user)  
        return render(request, 'loan_list.html', {'loans': loans})

    loans = Loan.objects.all()
    return render(request,'loan_list.html',{'loans':loans})







# PAYSTACK PAYMENT VIEWS

# View to calculate price and initialize Paystack payment








def payment(request):
    if request.method == 'POST':
        # Get the plan and number of borrowers from the form
        plan = request.POST.get('plan')
        borrowers = int(request.POST.get('borrowers', 1))

        # Price per borrower (₦50 per borrower)
        price_per_borrower = 50
        total_price = borrowers * price_per_borrower
        
        # Ensure that the plan is valid and the number of borrowers is within limits
        if plan == 'starter' and borrowers > 50:
            return JsonResponse({'error': 'Starter plan supports 1-50 borrowers only!'}, status=400)
        elif plan == 'professional' and not (51 <= borrowers <= 200):
            return JsonResponse({'error': 'Professional plan supports 51-200 borrowers only!'}, status=400)
        elif plan == 'business' and borrowers < 201:
            return JsonResponse({'error': 'Business plan supports 201-100000 borrowers only!'}, status=400)

        # Prepare the payment request to Paystack
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }

        data = {
            'email': request.user.email,
            'amount': total_price * 100,  # Paystack expects the amount in kobo
            'reference': f"ref_{plan}_{borrowers}_{int(request.user.id)}",
            'callback_url': request.build_absolute_uri('/payment/verify/'),
        }

        try:
            # Initialize the transaction by making a request to Paystack
            response = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers)
            response.raise_for_status()  # Raise error if the request fails
            response_data = response.json()

            # Debugging: Print the response to see if it was successful
            print("Paystack Response:", response_data)

            # Check if the Paystack response has status as True
            if response_data.get('status') == True:  # Change this line to check for True status
                payment_url = response_data['data']['authorization_url']
                return redirect(payment_url)
            else:
                return JsonResponse({'error': 'Error initializing payment'}, status=500)

        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': f'Request failed: {str(e)}'}, status=500)

    return render(request, 'payment.html')




# View to verify Paystack payment

@login_required
def verify_payment(request):
    reference = request.GET.get('reference')

    if not reference:
        return JsonResponse({'error': 'No reference provided'}, status=400)

    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'
    }

    try:
        # Verify the payment with Paystack using the reference
        response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers)
        response.raise_for_status()  # Raise error if the request fails
        response_data = response.json()

        if response_data['status'] == 'success' and response_data['data']['status'] == 'success':
            # Payment was successful, process the payment and redirect to the dashboard
            # Here, you would update the user's account, create records, etc.
            return redirect('dashboard')  # Redirect to your dashboard after successful payment

        return JsonResponse({'error': 'Payment verification failed'}, status=400)

    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'Request failed: {str(e)}'}, status=500)
