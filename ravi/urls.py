from django.contrib import admin
from django.urls import path,include
from . import views

from ravi.hlapi import CustomerViewSet,PlViewSet
from rest_framework.routers import DefaultRouter


router=DefaultRouter()
router.register('hlapi',CustomerViewSet,basename='hlapi')
router.register('plapi',PlViewSet,basename='plapi')



urlpatterns = [

    # Personal Details URLs
    path('personal/', views.personal_detail_view, name='personal'),  # View personal details
    path('personaldoc/<str:application_id>/', views.document_details_view, name='document_detail'),  # Upload personal documents
    path('personal/<int:pk>/update/', views.update_personal_detail_view, name='update_personal_detail'),  # Update personal details
    path('personal/<int:pk>/view/', views.view_personal_detail_view, name='view_personal_detail'),  # View personal detail
    path('personallist/', views.personal_detail_list_view, name='personal_detail_list'),  # List personal details

    # Document Management URLs
    path('document/<int:instance_id>/update/', views.update_document_detail_view, name='update_document_detail'),  # Update document details
    path('document/uploads/', views.document_upload_list_view, name='document_upload_list'),  # List uploaded documents
    path('document/upload/<int:pk>/view/', views.view_documents_view, name='view_documents'),  # View a specific document

    # Home/Customer Profile URLs
    path('home/', views.customer_profile_view, name='customer_profile'),  # View a specific customer profile
    path('home/<int:pk>/update/', views.update_customer_profile_view, name='update_customer_profile'),  # Update a customer profile
    path('home/<int:pk>/view/', views.view_customer_profile_view, name='view_customer_profile'),  # View a specific customer profile
    path('homelist/', views.customer_profile_list_view, name='customer_profile_list'),  # List customer profiles

    # Applicant Document URLs
    path('homedoc/<str:application_id>/', views.applicant_document_create_view, name='applicant_document_create'),  # Create an applicant document
    path('applicant/<int:instance_id>/update/', views.update_applicant_document_view, name='update_applicant_document'),  # Update an applicant document
    path('applicant/documents/', views.applicant_document_list_view, name='applicant_document_list'),  # List applicant documents
    path('applicant/<int:pk>/view/', views.view_applicant_document_view, name='view_applicant_document'),  # View a specific applicant document

    # Success page
    path('success/<str:application_id>/', views.success, name='success'),  # Success page after submission

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),  # Dashboard view

    # Verification for Personal and Home Customers
    path('perstatus/<int:instance_id>/', views.personal_verification_add, name='personal_verification_add'),  # Add personal verification
    path('perstatus/<int:instance_id>/update/', views.update_plverify, name='update_personal_verify'),  # Update personal verification
    path('perstatus/<int:instance_id>/view/', views.personalcustomerverify, name='view_personal_verify'),  # View personal verification
    path('applyhome/<int:instance_id>/', views.home_verification_add, name='applyhome'),  # Add home verification
    path('applyhome/<int:instance_id>/update/', views.update_hlverify, name='update_home_verify'),  # Update home verification
    path('applyhome/<int:instance_id>/view/', views.homecustomerverify, name='view_home_verify'),  # View home verification

    # Authentication URLs
    path('logout/', views.custom_logout, name='logout'),  # Logout
    path('register/', views.register, name='register'),  # Register a new user
    path('employee_login/', views.Loginemployee, name='employee_login'),  # Employee login
    path('homelogin/', views.Loginhome, name='homelogin'),  # Home login
    path('homeregister/', views.homeregister, name='homeregister'),  # Home register

    # Basic Detail Views
    path('perbasicdetail/', views.basicdetailspl, name='personalbasicdetail'),
    path('pl-fetch-credit-report/', views.pl_fetch_credit_report, name='plfetchcreditreport'),
  # Personal basic detail
    path('homebasicdetail/', views.basicdetailhl, name='homebasicdetail'),
    path('hl-fetch-credit-report/', views.hl_fetch_credit_report, name='hlfetchcreditreport'),
  # Home basic detail

    path('disbursement/<int:verification_id>/', views.hldisbursement_details, name='hldisbursement_details'),#disbursement
    path('hldisbursement-summary/', views.hldisbursement_summary, name='hldisbursement_summary'),#disbursement-summary
    path('hlsuccess/<str:application_id>', views.hlsuccess, name='hlsuccess'),#success
    path('rejected/<str:status>',views.rejected_hl,name='hlpage'),#rejected

    
    path('pldisbursement/<int:verification_id>/', views.pldisbursement_details, name='pldisbursement_details'),#disbursement
    path('pldisbursement-summary/', views.pldisbursement_summary, name='pldisbursement_summary'),#disbursement-summary
    path('plsuccess/<str:application_id>', views.plsuccess, name='plsuccess'),#success
    path('rejected/<str:status>',views.rejected_pl,name='plpage'),#rejected
    

    path('',include(router.urls))


]


    

