import os
import json
import smtplib
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .utils import SalaryGenerator, send_payslip_email_optimized

# This dictionary stores the result of the last run in memory
# Note: In a real production app, you'd use a database model for this.
PAYS_STATUS = {
    "is_running": False,
    "success_count": 0,
    "failed_emails": [],
    "total": 0
}

def process_all_payslips_logic(hr_email, hr_pass):
    global PAYS_STATUS
    PAYS_STATUS["is_running"] = True
    PAYS_STATUS["success_count"] = 0
    PAYS_STATUS["failed_emails"] = []

    json_path = os.path.join(settings.BASE_DIR, 'employees.json')
    with open(json_path, 'r') as f:
        employees = json.load(f)
    
    PAYS_STATUS["total"] = len(employees)

    server = None
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(hr_email, hr_pass)

        for emp in employees:
            email = emp.get('email')
            name = emp.get('name', 'Unknown')
            
            try:
                # 1. VALIDATE EMAIL FORMAT
                validate_email(email)

                # 2. GENERATE & SEND
                pdf = SalaryGenerator()
                pdf.create_payslip_content(emp)
                temp_file = f"Payslip_{emp.get('id')}.pdf"
                pdf.output(temp_file)

                was_sent = send_payslip_email_optimized(server, email, name, emp.get('month'), temp_file, hr_email)
                
                if was_sent:
                    PAYS_STATUS["success_count"] += 1
                else:
                    PAYS_STATUS["failed_emails"].append(f"{name} (SMTP Reject)")
                
                if os.path.exists(temp_file): os.remove(temp_file)

            except ValidationError:
                PAYS_STATUS["failed_emails"].append(f"{name} (Invalid Email: {email})")
            except Exception as e:
                PAYS_STATUS["failed_emails"].append(f"{name} (Error: {str(e)})")

    finally:
        if server: server.quit()
        PAYS_STATUS["is_running"] = False