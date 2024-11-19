from django.urls import path
from . import views

urlpatterns = [
    path('extract_info/', views.extract_info, name='extract_info'),
    path('customer/create/',views.get_customer_data,name='create_customer_data'),
    path('create_document/<str:customerId>',views.create_document,name='create_document'),
    path('create_document_front/<str:customerId>',views.create_document_front,name='create_document_front'),
    path('create_document_back/<str:customerId>',views.create_document_front,name='create_document_back'),
    path('get_customer_with_document/<str:customerId>',views.get_customer_with_document,name='get_customer_with_document'),
]