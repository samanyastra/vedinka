from django.urls import path
from apps.finance import bill_views

urlpatterns = [
    # Charges management
    path('charges/', bill_views.list_charges, name='list_charges'),
    path('charges/create/', bill_views.create_charge, name='create_charge'),
    path('charges/<int:charge_id>/update/', bill_views.update_charge, name='update_charge'),
    path('charges/<int:charge_id>/delete/', bill_views.delete_charge, name='delete_charge'),
    
    # Bill ledger
    path('ledger/', bill_views.list_bill_ledger, name='list_bill_ledger'),
    path('ledger/<int:ledger_id>/', bill_views.get_bill_ledger_entry, name='get_bill_ledger_entry'),
]
