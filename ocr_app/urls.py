from django.urls import path
from . import views

urlpatterns = [
    path('extract_info/', views.extract_info, name='extract_info'),
    # path('customer/view',views.get_customer_data,name='get_customer_data'),
    # path('document_data/<uuid:customerId>/',views.get_document_data,name='get_document_data'),
]