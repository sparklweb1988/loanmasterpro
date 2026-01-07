from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('signin/', views.signin_view, name='signin'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('transaction/', views.transaction, name='transaction'),
    path('delete-client/<int:client_id>/', views.delete_client, name='delete_client'),
    path('export-excel/', views.export_feed_excel, name='export_excel'),
    
    #  INDIVIDUAL
    
    path('create-client/', views.create_client, name='create_client'),
    path('create-deposit/', views.create_deposit, name='create_deposit'),
    path('create-loan/', views.create_loan, name='create_loan'), 
    
   
    path('edit-loan/<int:loan_id>/', views.edit_loan, name='edit_loan'),
    path('delete-loan/<int:loan_id>/', views.delete_loan, name='delete_loan'),
    
     path('create-deposit/', views.create_deposit, name='create_deposit'),
    path('edit-deposit/<int:deposit_id>/', views.edit_deposit, name='edit_deposit'),
    path('delete-deposit/<int:deposit_id>/', views.delete_deposit, name='delete_deposit'),
    
    
    

    path('edit-client/<int:client_id>/', views.edit_client, name='edit_client'),
    path('delete-client/<int:client_id>/', views.delete_client, name='delete_client'),
    
    
    path('client_list/', views.client_list, name='client_list'),
    path('deposit_list/', views.deposit_list, name='deposit_list'),
    path('loan_list/', views.loan_list, name='loan_list'),
    
    # CONTACT
    
    path('contact/', views.contact_view, name='contact'),
    
    
    # CREDITOFFICER
    path('credit_officer/', views.officer_view, name='officer_view'),
    path('branch/', views.branch_view, name='branch_view'),  
    path('center/', views.center_view, name='center_view'), 
    path('center/edit/<int:center_id>/', views.edit_center_view, name='edit_center_view'),  
    path('center/delete/<int:id>/', views.delete_center_view, name='delete_center_view'),  
    path('branch/edit/<int:branch_id>/', views.edit_branch_view, name='edit_branch_view'), 
    path('branch/delete/<int:id>/', views.delete_branch_view, name='delete_branch_view'),
    path('officer/edit/<int:officer_id>/', views.edit_officer_view, name='edit_officer_view'),
    path('officer/delete/<int:id>/', views.delete_officer_view, name='delete_officer_view'), 

 
    
    
    #  PAYSTACK PAYMENT
    
    path("pricing/", views.pricing_view, name="pricing"),
    path('upgrade-plan/<str:plan_name>/', views.upgrade_plan, name='upgrade_plan'),
    path('payment-success/<str:plan_name>/', views.payment_success, name='payment_success'),

# LOAN PAYMENT
    path('payment/history/', views.payment_history, name='payment_history'),
    path('payment/manual/', views.post_payment, name='post_payment'),


    path('payment/update/<int:payment_id>/', views.update_payment, name='update_payment'),
    path('payment/delete/<int:payment_id>/', views.delete_payment, name='delete_payment'), 
]
   
