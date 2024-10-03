from django.shortcuts import render
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from .models import *
from .forms import *


import requests
import uuid
from django.shortcuts import render, redirect
from django.http import JsonResponse

APIID = "AP100034"
TOKEN = "6b549eed-2af0-488c-a2e1-3d10f37f11c6"



def basicdetailspl(request,instance_id=None):
    instance = get_object_or_404(personalbasicdetail, id=instance_id) if instance_id else None
    application_id=None

    if request.method == 'POST':
        form = plBasicDetailForm(request.POST,request.FILES,instance=instance)
        if form.is_valid():
            user_details = form.save()
            application_id=user_details.application_id
            orderid = str(uuid.uuid4())
            request.session['application_id']=application_id
            request.session['orderid'] = orderid
            request.session['user_id'] = user_details.id
            request.session['mobile_number']=user_details.phone_number
            
            payload = {
                "apiid": APIID,
                "token": TOKEN,
                "methodName": "UATCreditScoreOTP",
                "orderid": orderid,
                "phone_number": user_details.phone_number
            }

            response = requests.post("https://apimanage.websoftexpay.com/api/Uat_creditscore_OTP.aspx", json=payload)
            data = response.json()

            if response.status_code == 200 and data.get("status") == "success":
                otp = data["data"].split(":")[1]
                user_details.otp = otp  
                user_details.orderid = orderid
                user_details.save()
                print(f'otp is:{otp}')
                request.session['otp']=otp
                return redirect('plfetchcreditreport')
            else:
                return JsonResponse({"status": "error", "message": data.get("mess", "Failed to generate OTP")})
    else:
        form = plBasicDetailForm()

    return render(request, 'admin/basic.html', {'form': form})
def pl_fetch_credit_report(request):
    otp=request.session.get('otp')
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        user_details = personalbasicdetail.objects.get(id=user_id)
        otp = request.POST.get('otp').strip()  
        print(f'otp is:{otp}')
        payload = {
            "apiid": APIID,
            "token": TOKEN,
            "methodName": "UATcreditscore",
            "orderid": request.session.get('orderid'),  
            "fname": user_details.fname,
            "lname": user_details.lname,
            "Dob": user_details.Dob.isoformat() if isinstance(user_details.Dob, date) else user_details.Dob,
            "phone_number": user_details.phone_number,
            "pan_num": user_details.pan_num,
            "application_id":user_details.application_id,
            "otp": otp 
            
        }
        
        response = requests.post("https://apimanage.websoftexpay.com/api/Uat_credit_score.aspx", json=payload)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "success":
                if 'Dob' in data["data"]:
                    dob = data["data"]['Dob']
                    if isinstance(dob, date):
                        data["data"]['Dob'] = dob.isoformat()
                credit_score = data["data"].get("ScoreValue")
                
                if credit_score:
                    loan_application = PersonalDetail.objects.filter(basicdetailform=user_details).first()
                    if loan_application:
                        loan_application.credit_score = credit_score
                        loan_application.save()
                    return render(request, 'admin/plcibil_score.html', {'credit_score': credit_score, 'application_id': user_details.application_id})
            else:
                return JsonResponse({"status": "error", "message": data["mess"]})
        else:
            return JsonResponse({"status": "error", "message": "Failed to fetch credit report"})

    return render(request, 'admin/basic.html',{'otp':otp})

def personal_detail_view(request):
    # Get mobile number from session or POST data
    mobile_number = request.session.get('mobile_number') or request.POST.get('mobile_number')  
    print("Mobile number retrieved from session or form:", mobile_number)
    
    if not mobile_number:
        print("Mobile number not found. Redirecting to basic details form.")
        return redirect('personalbasicdetail')  # If no mobile number, redirect to the basic details form.

    if request.method == 'POST':
        form = PersonalDetailForm(request.POST, request.FILES)
        
        if form.is_valid():
            loan = form.save(commit=False)
            try:
                mobile_number_int = int(mobile_number)  # Ensure mobile_number is valid
                
                print(f"Attempting to find basic detail with mobile number: {mobile_number_int}")

                lap = personalbasicdetail.objects.filter(phone_number=mobile_number_int).first()
                
                if lap:
                    print("Basic Detail Object Retrieved:", lap)

                    # Check if there is already a loan application associated with this basic detail.
                    if PersonalDetail.objects.filter(basicdetailform=lap).exists():
                        print("This BasicDetail already has a LoanApplication.")
                        return redirect('error_page', message="This Details already has an associated Loan Application.")
                    
                    loan.basicdetailform = lap
                    loan.mobile_number = str(lap.phone_number)
                    loan.application_id = lap.application_id
                    loan.save()  
                    request.session['loanid'] = loan.id
                    return redirect('document_detail', application_id=lap.application_id)
                else:
                    print("No matching basic detail found for this phone number.")
                    return redirect('personalbasicdetail')

            except ValueError:
                print("Invalid mobile number format.")
                return redirect('personalbasicdetail')

    else:
        # Pre-populate mobile_number field with the session value
        form = PersonalDetailForm(initial={'mobile_number': mobile_number})

    return render(request, 'admin/personal_detail_form.html', {'form': form, 'mobile_number': mobile_number})



def document_details_view(request, application_id):
    
    basicdetailform = get_object_or_404(personalbasicdetail, application_id=application_id)
    personal_details = get_object_or_404(PersonalDetail, basicdetailform=basicdetailform)

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)  # Create a new record, but don't save yet
            print(f"Personal Details ID: {personal_details.id}")
            instance.personal_detail = personal_details
            instance.save()  # Save the instance with the related personal details
            return redirect('success',application_id=application_id)  # Redirect after saving
        else:
            print(f"Form errors: {form.errors}")  # Print errors to console for debugging
    else:
        form = DocumentUploadForm()

    return render(request, 'admin/document_upload_form.html', {
        'form': form,
    })

   



# ====================homelaon=
def basicdetailhl(request,instance_id=None):
    instance = get_object_or_404(homebasicdetail, id=instance_id) if instance_id else None
    application_id=None

    if request.method == 'POST':
        form = HomeBasicDetailForm(request.POST,request.FILES,instance=instance)
        if form.is_valid():
            user_details = form.save()
            application_id=user_details.application_id
            orderid = str(uuid.uuid4())
            request.session['application_id']=application_id
            request.session['orderid'] = orderid
            request.session['user_id'] = user_details.id
            request.session['mobile_number']=user_details.phone_number
            
            payload = {
                "apiid": APIID,
                "token": TOKEN,
                "methodName": "UATCreditScoreOTP",
                "orderid": orderid,
                "phone_number": user_details.phone_number
            }

            response = requests.post("https://apimanage.websoftexpay.com/api/Uat_creditscore_OTP.aspx", json=payload)
            data = response.json()

            if response.status_code == 200 and data.get("status") == "success":
                otp = data["data"].split(":")[1]
                user_details.otp = otp  
                user_details.orderid = orderid
                user_details.save()
                print(f'otp is:{otp}')
                request.session['otp']=otp
                return redirect('hlfetchcreditreport')
            else:
                return JsonResponse({"status": "error", "message": data.get("mess", "Failed to generate OTP")})
    else:
        form = HomeBasicDetailForm()

    return render(request, 'admin/hlbasic.html', {'form': form})
def hl_fetch_credit_report(request):
    otp=request.session.get('otp')
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        user_details = homebasicdetail.objects.get(id=user_id)
        otp = request.POST.get('otp').strip()  
        print(f'otp is:{otp}')
        payload = {
            "apiid": APIID,
            "token": TOKEN,
            "methodName": "UATcreditscore",
            "orderid": request.session.get('orderid'),  
            "fname": user_details.fname,
            "lname": user_details.lname,
            "Dob": user_details.Dob.isoformat() if isinstance(user_details.Dob, date) else user_details.Dob,
            "phone_number": user_details.phone_number,
            "pan_num": user_details.pan_num,
            "application_id":user_details.application_id,
            "otp": otp 
            
        }
        
        response = requests.post("https://apimanage.websoftexpay.com/api/Uat_credit_score.aspx", json=payload)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "success":
                if 'Dob' in data["data"]:
                    dob = data["data"]['Dob']
                    if isinstance(dob, date):
                        data["data"]['Dob'] = dob.isoformat()
                credit_score = data["data"].get("ScoreValue")
                
                if credit_score:
                    loan_application = CustomerProfile.objects.filter(basicdetailhome=user_details).first()
                    if loan_application:
                        loan_application.credit_score = credit_score
                        loan_application.save()
                    return render(request, 'admin/hlcibil_score.html', {'credit_score': credit_score, 'application_id': user_details.application_id})
            else:
                return JsonResponse({"status": "error", "message": data["mess"]})
        else:
            return JsonResponse({"status": "error", "message": "Failed to fetch credit report"})

    return render(request, 'admin/hlbasic.html',{'otp':otp})


def customer_profile_view(request):
    mobile_number = request.session.get('mobile_number')
    print("Mobile number retrieved from session:", mobile_number)

    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, request.FILES)
        
        if form.is_valid():
            loan = form.save(commit=False)

            if mobile_number is None:
                print("Mobile number is not found in session.")
                return redirect('homebasicdetail')

            print("Attempting to find basic detail with mobile number:", mobile_number)

            lap = homebasicdetail.objects.filter(phone_number=mobile_number).first()
            
            if lap:
                print("Basic Detail Object Retrieved:", lap)

                if CustomerProfile.objects.filter(basicdetailhome=lap).exists():
                    print("This BasicDetail already has a LoanApplication.")
                    return redirect('error_page', message="This Details already has an associated Loan Application.")
                
                loan.basicdetailhome = lap
                loan.mobile_number = str(lap.phone_number)
                loan.application_id = lap.application_id
                loan.save()  
                request.session['loanid'] = loan.id
                
                return redirect('applicant_document_create', application_id=lap.application_id)
            else:
                print("No matching basic detail found for this phone number.")
                return redirect('homebasicdetail')

    else:
        form = CustomerProfileForm()

    return render(request, 'admin/customer_profile_form.html', {'form': form, 'mobile_number':mobile_number})




def applicant_document_create_view(request, application_id):
   
    # Fetch the related instances
    basicdetailhome = get_object_or_404(homebasicdetail, application_id=application_id)
    applicant_profile = get_object_or_404(CustomerProfile, basicdetailhome=basicdetailhome)

    if request.method == 'POST':
        form = ApplicantDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)  # Create a new record, but don't save yet
            print(f"applicant_profile ID: {applicant_profile.id}")
            instance.applicant_profile = applicant_profile
            instance.save()  # Save the instance with the related personal details
            return redirect('success',application_id=application_id)  # Redirect after saving
        else:
            print(f"Form errors: {form.errors}")  # Print errors to console for debugging
    else:
        form = ApplicantDocumentForm()

    return render(request, 'admin/applicant_document_form.html', {
        'form': form,
        'incomesource': applicant_profile.income_source,
        'loan_type': applicant_profile.loan_type,
    })

   
def success(request, application_id):
    return render(request, 'admin/success.html', {'application_id': application_id})

#views and updates==================================================

def update_personal_detail_view(request, pk):
    personal_detail = get_object_or_404(PersonalDetail, pk=pk)
    if request.method == 'POST':
        form = PersonalDetailForm(request.POST, instance=personal_detail)
        if form.is_valid():
            form.save()
            return redirect('update_document_detail', instance_id=personal_detail.id)
    else:
        form = PersonalDetailForm(instance=personal_detail)
    return render(request, 'admin/personal_detail_form.html', {'form': form})

def update_document_detail_view(request, instance_id):
    personal_detail = get_object_or_404(PersonalDetail, id=instance_id)
    document_upload, created = DocumentUpload.objects.get_or_create(personal_detail=personal_detail)
  
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES, instance=document_upload)
        if form.is_valid():
            form.save()
            return redirect('success')
    else:
        form = DocumentUploadForm(instance=document_upload)

    return render(request, 'admin/document_upload_form.html', {'form': form})

def personal_detail_list_view(request):
    personal_details = PersonalDetail.objects.all()
    return render(request, 'admin/personal_detail_list.html', {'personal_details': personal_details})
def document_upload_list_view(request):
    document_uploads = DocumentUpload.objects.select_related('personal_detail').all()
    return render(request, 'admin/document_upload_list.html', {'document_uploads': document_uploads})
def view_personal_detail_view(request, pk):
    personal_detail = get_object_or_404(PersonalDetail, pk=pk)
    return render(request, 'admin/view_personal_detail.html', {'personal_detail': personal_detail})
def view_documents_view(request, pk):
    document_upload = get_object_or_404(DocumentUpload, pk=pk)
    return render(request, 'admin/view_documents.html', {'document_upload': document_upload})


def update_customer_profile_view(request, pk):
    customer_profile = get_object_or_404(CustomerProfile, pk=pk)
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, instance=customer_profile)
        if form.is_valid():
            form.save()
            return redirect('applicant_document_create', instance_id=customer_profile.id )
    else:
        form = CustomerProfileForm(instance=customer_profile)

    return render(request, 'admin/customer_profile_form.html', {'form': form})


def update_applicant_document_view(request, instance_id):
    applicant_profile = get_object_or_404(CustomerProfile, id=instance_id)
    applicant_document, created = ApplicantDocument.objects.get_or_create(applicant_profile=applicant_profile)

    if request.method == 'POST':
        form = ApplicantDocumentForm(request.POST, request.FILES, instance=applicant_document)
        if form.is_valid():
            form.save()
            return redirect('success')
    else:
        form = ApplicantDocumentForm(instance=applicant_document)

    return render(request, 'admin/applicant_document_form.html', {'form': form})
def customer_profile_list_view(request):
    customer_profiles = CustomerProfile.objects.all()
    return render(request, 'admin/customer_profile_list.html', {'customer_profiles': customer_profiles})

def applicant_document_list_view(request):
    applicant_documents = ApplicantDocument.objects.select_related('applicant_profile').all()
    return render(request, 'admin/applicant_document_list.html', {'applicant_documents': applicant_documents})

def view_customer_profile_view(request, pk):
    customer_profile = get_object_or_404(CustomerProfile, pk=pk)
    return render(request, 'admin/view_customer_profile.html', {'customer_profile': customer_profile})


def view_applicant_document_view(request, pk):
    applicant_document = get_object_or_404(ApplicantDocument, pk=pk)
    return render(request, 'admin/view_applicant.html', {'applicant_document': applicant_document})




def personal_detail_list_view(request):
    personal_details = PersonalDetail.objects.all()
    return render(request, 'admin/personal_detail_list.html', {'personal_details': personal_details})

def customer_profile_list_view(request):
    customer_profiles = CustomerProfile.objects.all()
    return render(request, 'admin/customer_profile_list.html', {'customer_profiles': customer_profiles})

 

def personal_verification_add(request, instance_id):
    personal_detail = get_object_or_404(PersonalDetail, id=instance_id)
    
    # Use filter() to handle multiple documents
    applicant_documents = ApplicationVerification.objects.filter(personal_detail=personal_detail)
    
    if applicant_documents.exists():
        applicant_document = applicant_documents.first()  # or any other logic to choose a document
    else:
        applicant_document = ApplicationVerification(personal_detail=personal_detail)

    if request.method == 'POST':
        form = ApplicationVerificationForm(request.POST, request.FILES, instance=applicant_document)
        if form.is_valid():
            form.save()
            return redirect('success')
        else:
            print('Form errors:', form.errors)
    else:
        form = ApplicationVerificationForm(instance=applicant_document)
    
    return render(request, 'admin/applyper.html', {
        'form': form,})

def personalcustomerverify(request, instance_id):
    # Fetch the loan application based on the given instance_id
    personal_detail = get_object_or_404(PersonalDetail, id=instance_id)
    # Try to get existing verification documents for this loan application
    verfyObj = ApplicationVerification.objects.filter(personal_detail=personal_detail).first()
    
    # Render the record details in the template
    return render(request, 'admin/perview.html', {
        'personal_detail': personal_detail,
        'verfyObj': verfyObj,
})




def update_plverify(request, instance_id):
    personal_detail = get_object_or_404(PersonalDetail, id=instance_id)
    
    # Get or create ApplicationVerification related to the personal detail
    applicant_document, created = ApplicationVerification.objects.get_or_create(personal_detail=personal_detail)

    if request.method == 'POST':
        form = ApplicationVerificationForm(request.POST, request.FILES, instance=applicant_document)

        if form.is_valid():
            verification = form.save()

            # Check if verification is approved
            if verification.verification_status == 'Approved' and verification.id:
                # Ensure the disbursement details exist before redirecting
                pldisbursementdetails.objects.get_or_create(verification=verification)
                return redirect('pldisbursement_details', verification_id=verification.id)
            
            # Check other fields for approval status
            other_fields_approved = any(
                getattr(verification, field.name) == 'Approved'
                for field in verification._meta.get_fields()
                if field.name != 'verification_status'
            )
            
            if other_fields_approved:
                return redirect('plpage', status='success')
            else:
                return redirect('plpage', status='rejected')
        else:
            print('Form errors:', form.errors)
    else:
        form = ApplicationVerificationForm(instance=applicant_document)

    return render(request, 'admin/update_per.html', {
        'form': form,
    })

def pldisbursement_details(request, verification_id):
    # Fetch the ApplicationVerification instance instead of CustomerProfile
    verification = get_object_or_404(PersonalDetail, id=verification_id)

    # Fetch or create the pldisbursementdetails using the correct verification instance
    details, created = pldisbursementdetails.objects.get_or_create(verification=verification)
    form_status = 'not_submitted'

    if request.method == 'POST':
        form = PlDisbursementDetailsForm(request.POST, instance=details)
        if form.is_valid():
            form.save()
            form_status = 'submitted'
            return redirect('pldisbursement_summary')
        else:
            print(f"Form errors: {form.errors}")
    else:
        form = PlDisbursementDetailsForm(instance=details)

    return render(request, 'admin/pldisbursement_details.html', {
        'details_form': form,
        'form_status': form_status,
    })

def pldisbursement_summary(request):
    details_list = pldisbursementdetails.objects.select_related('verification__personal_detail').all()

    # Optionally, print out the details to verify
    for details in details_list:
        print(f"Details: {details}, Verification ID: {details.verification.id if details.verification else 'No Verification'}")
        print(f"Application ID: {details.verification.personal_detail.basicdetailfrom}")  # Check if this prints the right value

    return render(request, 'admin/pldisbursementview.html', {
        'details_list': details_list,
    })


def plsuccess(request, application_id):
    goldapp = get_object_or_404(PersonalDetail, basicdetailform__application_id=application_id)
    context = {
        'application_id': application_id,
        'goldapp': goldapp,
    }
    return render(request, 'admin/plsuccess.html', context)

def rejected_pl(request, status):
    return render(request, 'admin/plreject.html', {'status': status})




from django.http import HttpResponse
def home_verification_add(request, instance_id):
    applicant_profile = get_object_or_404(CustomerProfile, id=instance_id)
    
    # Use filter() to handle multiple documents
    applicant_documents = HomeApplication.objects.filter(applicant_profile=applicant_profile)
    
    if applicant_documents.exists():
        applicant_document = applicant_documents.first()  # or any other logic to choose a document
    else:
        applicant_document = HomeApplication(applicant_profile=applicant_profile)

    if request.method == 'POST':
        form = HomeapplicationForm(request.POST, request.FILES, instance=applicant_document)
        if form.is_valid():
            form.save()
            return HttpResponse('<h1>success</h1>')
        else:
            print('Form errors:', form.errors)
    else:
        form = ApplicationVerificationForm(instance=applicant_document)
    
    return render(request, 'admin/applyhome.html', {'form': form})



def homecustomerverify(request, instance_id):
    # Fetch the loan application based on the given instance_id
    applicant_profile = get_object_or_404(CustomerProfile, id=instance_id)
    # Try to get existing verification documents for this loan application
    verfyObj = HomeApplication.objects.filter(applicant_profile=applicant_profile).first()
    
    # Render the record details in the template
    return render(request, 'admin/homeview.html', {
        'applicant_profile': applicant_profile,
        'verfyObj': verfyObj,
}) 



def update_hlverify(request, instance_id):
    applicant_profile = get_object_or_404(CustomerProfile, id=instance_id)
    
    # Get or create HomeApplication related to the applicant profile
    applicant_document, created = HomeApplication.objects.get_or_create(applicant_profile=applicant_profile)

    if request.method == 'POST':
        form = HomeapplicationForm(request.POST, request.FILES, instance=applicant_document)

        if form.is_valid():
            verification = form.save()

            # Check if verification is a HomeApplication instance
          

            # If verification is approved
            if verification.verification_status == 'Approved' and verification.id:
                return redirect('hldisbursement_details', verification_id=verification.id)
            
            # Check other fields for approval status
            other_fields_approved = any(
                getattr(verification, field.name) == 'Approved'
                for field in verification._meta.get_fields()
                if field.name != 'verification_status'
            )
            
            if other_fields_approved:
                return redirect('hlpage', status='success')
            else:
                return redirect('hlpage', status='rejected')
        else:
            print('Form errors:', form.errors)
    else:
        form = HomeapplicationForm(instance=applicant_document)

    return render(request, 'admin/update_home.html', {
        'form': form,
    })


def hldisbursement_details(request, verification_id):
    # Fetch the HomeApplication instance instead of CustomerProfile
    verification = get_object_or_404(CustomerProfile, id=verification_id)

    # Fetch or create the hldisbursementdetails using the correct verification instance
    details, created = hldisbursementdetails.objects.get_or_create(verification=verification)
    form_status = 'not_submitted'

    if request.method == 'POST':
        form = HlDisbursementDetailsForm(request.POST, instance=details)
        if form.is_valid():
            form.save()
            form_status = 'submitted'
            return redirect('hldisbursement_summary')
        else:
            print(f"Form errors: {form.errors}")
    else:
        form = HlDisbursementDetailsForm(instance=details)

    return render(request, 'admin/hldisbursement_details.html', {
        'details_form': form,
        'form_status': form_status,
    })






def hldisbursement_summary(request):
    details_list = hldisbursementdetails.objects.select_related('verification').all()

    # Optionally, print out the details to verify
    for details in details_list:
        print(f"Details: {details}, Verification ID: {details.verification.id if details.verification else 'No Verification'}")

    return render(request, 'admin/hldisbursementview.html', {
        'details_list': details_list,
})

def hlsuccess(request, application_id):
    goldapp=get_object_or_404(CustomerProfile,basicdetailhome__application_id=application_id)
    context = {
        
        'application_id': application_id,
        'goldapp':goldapp,
        
    }
    return render(request, 'admin/hlsuccess.html', context)

def rejected_hl(request,status):
    return render(request,'admin/hlreject.html',{'status':status})




# =======================homedisend=========================
from django.contrib.auth import authenticate, login

from .forms import LoginForm

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                if username == 'ravi' and password == 'Ravindra@1':  # Check specific credentials
                    login(request, user)
                    return redirect('dashboard')  # Redirect to the dashboard
                else:
                    form.add_error(None, 'Invalid credentials.')
    else:
        form = LoginForm()

    return render(request, 'main/login.html', {'form': form})

def dashboard(request):
    personal_loans_count = PersonalDetail.objects.count()
    home_loans_count = CustomerProfile.objects.count()
    business_loans_count = 10
    car_loans_count = 40
    educational_loans_count = 80
    other_loans_count = 100
    # Add more counts as needed

    context = {
        'personal_loans_count': personal_loans_count,
        'home_loans_count': home_loans_count,
        'business_loans_count': business_loans_count,
        'car_loans_count': car_loans_count,
        'educational_loans_count': educational_loans_count,
        'other_loans_count': other_loans_count,
        

        # Add more counts to context if needed
    }
    return render(request, 'main/admin.html', context)


def custom_logout(request):
    
    return redirect('login')

from django.contrib import messages
from django.contrib.auth.models import User

from .forms import LoginForm

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password']
        password2 = request.POST['password2']

        if password1 == password2:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return redirect('employee_login')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email is already taken.')
                return redirect('employee_login')
            else:
                user = User.objects.create_user(username=username, email=email, password=password1)
                user.save()
                request.session['registration_successful'] = True
                return redirect('success')
        else:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')
    else:
        return render(request, 'main/addemployee.html')

def employee_dashboard(request):
    return render(request, 'employeelogins/admin.html')

from django.shortcuts import render, redirect
from django.contrib import auth
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt

def Loginemployee(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate using Django's built-in authenticate function
        user = auth.authenticate(request, username=username, password=password)
        
        if user is not None:
            auth.login(request, user)
            print('login is successful')
            return redirect('personal_detail_list')
        else:
            print('invalid credentials')
            return redirect('employee_login')
    else:
        return render(request, 'employeelogins/perlogin.html')


@csrf_exempt

def Loginhome(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate using Django's built-in authenticate function
        user = auth.authenticate(request, username=username, password=password)
        
        if user is not None:
            auth.login(request, user)
            print('login is successful')
            return redirect('customer_profile_list')
        else:
            print('invalid credentials')
            return redirect('homelogin')
    else:
        return render(request, 'employeelogins/homelogin.html')

def homeregister(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password']
        password2 = request.POST['password2']

        if password1 == password2:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return redirect('homelogin')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email is already taken.')
                return redirect('homelogin')
            else:
                user = User.objects.create_user(username=username, email=email, password=password1)
                user.save()
                request.session['registration_successful'] = True
                return redirect('success')
        else:
            messages.error(request, 'Passwords do not match.')
            return redirect('homeregister')
    else:
        return render(request, 'main/homeemployee.html')

@csrf_exempt

def homeemployee(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate using Django's built-in authenticate function
        user = auth.authenticate(request, username=username, password=password)
        
        if user is not None:
            auth.login(request, user)
            print('login is successful')
            return redirect('customer_profile_list')
        else:
            print('invalid credentials')
            return redirect('homelogin')
    else:
        return render(request, 'employeelogins/homelogin.html')
    
    
    






    # =====/=====/extert

