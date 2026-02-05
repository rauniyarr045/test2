
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from django.conf import settings
from .utils import SalaryGenerator,send_payslip_email
import smtplib
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
import json
import os
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
import smtplib
import os
import json
from django.http import JsonResponse
from django.conf import settings

# This is the line that was likely missing or wrong:
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

# Import your helper functions from your utils file
from .utils import SalaryGenerator, send_payslip_email_optimized

def manage_employees(request):
    json_path = os.path.join(settings.BASE_DIR, 'employees.json')
    
    # --- 1. LOAD DATA ---
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            try:
                employees = json.load(f)
            except json.JSONDecodeError:
                employees = []
    else:
        employees = []

    if request.method == 'POST':
        action = request.POST.get('action')

        # --- 2. HANDLE DELETE ---
        if action == 'delete':
            target_id = request.POST.get('emp_id')
            employees = [e for e in employees if str(e.get('id')) != str(target_id)]
            messages.warning(request, f"Employee {target_id} removed.")

        # --- 3. HANDLE ADD OR EDIT ---
        elif action in ['add', 'edit']:
          
            emp_data = {
                "id": request.POST.get('emp_id_code'),
                "name": request.POST.get('name'),
                "email": request.POST.get('email'),
                "month": request.POST.get('month'),
                "department": request.POST.get('department'),
                "doj": request.POST.get('doj'),
                "total_days": int(request.POST.get('total_days') or 30),
                "worked_days": int(request.POST.get('worked_days') or 30),
                "pan": request.POST.get('pan'),
                "emp_type": request.POST.get('emp_type'),
                "designation": request.POST.get('designation'),
                "location": request.POST.get('location'),
                "basic": int(request.POST.get('basic') or 0),
                "hra": int(request.POST.get('hra') or 0),
                "lta": int(request.POST.get('lta') or 0),
                "bonus": int(request.POST.get('bonus') or 0),
                "additional_allowance": int(request.POST.get('additional_allowance') or 0),
                "insurance": int(request.POST.get('insurance') or 0),
                "income_tax": int(request.POST.get('income_tax') or 0),
                "professional_tax": int(request.POST.get('professional_tax') or 0),
            }

            if action == 'add':
                employees.append(emp_data)
                messages.success(request, "New employee added successfully.")
            
            elif action == 'edit':
                target_id = request.POST.get('editing_id') 
                for i, emp in enumerate(employees):
                    if str(emp.get('id')) == str(target_id):
                        employees[i] = emp_data
                        break
                messages.success(request, "Employee record updated.")

        # --- 4. SAVE UPDATED JSON ---
        with open(json_path, 'w') as f:
            json.dump(employees, f, indent=4)
            
            
        return redirect('manage_employees') 

    return render(request, 'manage_employees.html', {'employees': employees})

def custom_login(request):
    if request.method == 'POST':
        user_name = request.POST.get('username')
        pass_word = request.POST.get('password')
        
        # Check if credentials are correct
        user = authenticate(request, username=user_name, password=pass_word)
        
        if user is not None:
            if user.is_staff: # Ensure they are an admin
                login(request, user)
                return redirect('home') # Redirect to your portal
            else:
                messages.error(request, "Access denied. Admins only.")
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'login.html')

def custom_logout(request):
    logout(request)
    return redirect('login')

def is_admin(user):
    return user.is_authenticated and user.is_staff
@user_passes_test(is_admin, login_url='/login/')


def index(request):
    # This renders the index.html file we just created
    return render(request, 'index.html')



from .utils import SalaryGenerator, send_payslip_email_optimized

def run_payslip_process(request):
    if request.method == "POST":
        hr_email = request.POST.get('email')
        hr_pass = request.POST.get('password')

        if not hr_email or not hr_pass:
            return JsonResponse({'status': 'error', 'message': 'Credentials missing'})

        success_count = 0
        failed_list = []
        
        try:
            # 1. Load the data
            json_path = os.path.join(settings.BASE_DIR, 'employees.json')
            with open(json_path, 'r') as f:
                employees = json.load(f)

            # 2. Try to Connect & Login (Credential Check)
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(hr_email, hr_pass)

                # 3. If login successful, process employees
                for emp in employees:
                    target_email = emp.get('email')
                    emp_name = emp.get('name', 'Unknown')
                    
                    try:
                        # Validate email format
                        validate_email(target_email)
                        
                        # Generate PDF
                        pdf = SalaryGenerator()
                        pdf.create_payslip_content(emp)
                        temp_file = f"Payslip_{emp.get('id')}.pdf"
                        pdf.output(temp_file)

                        # Send
                        was_sent=  send_payslip_email_optimized(
                            server, target_email, emp_name, 
                            emp.get('month'), temp_file, hr_email
                        )
                        if was_sent:
                            success_count += 1
                        else:
                            failed_list.append(f"{emp_name}:sever rejected email")    
                        if os.path.exists(temp_file): os.remove(temp_file)
                    
                    except (ValidationError, Exception) as e:
                        failed_list.append(f"{emp_name} ({target_email}): {str(e)}")

            # 4. Return the detailed report
            return JsonResponse({
                'status': 'success',
                'sent_count': success_count,
                'failed_count': len(failed_list),
                'errors': failed_list
            })

        except smtplib.SMTPAuthenticationError:
            return JsonResponse({'status': 'error', 'message': 'Gmail Login Failed. Check App Password.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'System Error: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'Only POST requests allowed'})


