import os
import smtplib
import json


from fpdf import FPDF, XPos, YPos
from num2words import num2words
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from django.conf import settings

class SalaryGenerator(FPDF):
 def header(self):
    # 1. THE WATERMARK (Drawn first so it stays behind the text)
    try:
        # Use Django's BASE_DIR to find the image in the static folder
        watermark_path = os.path.join(settings.BASE_DIR, 'static', 'logoo.png')
        if os.path.exists(watermark_path):
            with self.local_context(fill_opacity=0.05): # Lower opacity (0.05) for clarity
                # Center the watermark in the middle of the page
                self.image(watermark_path, x=20, y=60, w=170)
    except Exception as e:
        print(f"Watermark error: {e}")

    # 2. THE TOP LOGO
    try:
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'mainLogo.png')
        if os.path.exists(logo_path):
            logo_width = 70
            center_x = (self.w - logo_width) / 2
            self.image(logo_path, center_x, 8, logo_width)
            self.set_y(35) # Move cursor below the logo
        else:
            self.set_y(15)
    except:
        self.set_y(15)

    # 3. COMPANY TEXT (Drawn last so it is sharp and clear)
    self.set_font('helvetica', 'B', 15)
    self.set_text_color(0, 0, 0) # Ensure text is solid black
    self.cell(0, 8, 'Star Dynamic Logistics India  Pvt Ltd', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    self.set_font('helvetica', 'I', 8)
    self.cell(0, 5, 'PROUDLY MOVING INDIA FORWARD', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    self.set_font('helvetica', '', 9)
    self.cell(0, 5, 'Office Location:- SM001, Spandan Mansion, Himanagar, Dankuni, WB-712311', align='C',
              new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    self.ln(5)
 def create_payslip_content(self, data):
        self.add_page()
        self.set_font('helvetica', 'B', 11)
        self.cell(0, 8, f"PAYSLIP FOR THE MONTH OF: {str(data['month']).upper()}-2026", align='C', new_x=XPos.LMARGIN,
                  new_y=YPos.NEXT)
        self.ln(2)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

        # --- EMPLOYEE INFORMATION ---
        self.set_font('helvetica', 'B', 9)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 7, " EMPLOYEE INFORMATION", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font('helvetica', '', 9)

        # FIXED: Each tuple now has exactly 4 elements
        merged_rows = [
            ("Employee Name:", data['name'], "Employee Id:", data['id']),
            ("Department:", data['department'], "Date of Joining:", data['doj']),
            ("Calendar Days:", data['total_days'], "PAN No:", data['pan']),
            ("Employee Type:", data['emp_type'], "Designation:", data['designation']),
            ("Working Days:", data['worked_days'], "Current Location:", data['location'])
        ]

        for label1, val1, label2, val2 in merged_rows:
            self.cell(45, 7, f" {label1}", border='L')
            self.cell(50, 7, f"{val1}", border='R')
            self.cell(45, 7, f" {label2}", border=0)
            self.cell(50, 7, f"{val2}", border='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)

        # --- EARNINGS & DEDUCTIONS ---
        self.set_font('helvetica', 'B', 10)
        self.cell(95, 8, "Earnings", border=1, align='C')
        self.cell(95, 8, "Deductions", border=1, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        earn_list = [
            ("Basic", data.get('basic', 0)),
            ("HRA", data.get('hra', 0)),
            ("LTA", data.get('lta', 0)),
            ("Statutory Bonus", data.get('bonus', 0)),
            ("Additional Allowance", data.get('additional_allowance', 0))
        ]

        deduct_list = [
            ("Provident Fund", data.get('insurance', 0)),
            ("Income Tax", data.get('income_tax', 0)),
            ("Professional Tax", data.get('professional_tax', 200)),
            ("", 0), ("", 0)
        ]

        for i in range(len(earn_list)):
            self.set_font('helvetica', '', 9)
            self.cell(60, 7, f" {earn_list[i][0]}", border=1)
            self.cell(35, 7, f"{earn_list[i][1]:.0f}", border=1, align='R')
            self.cell(60, 7, f" {deduct_list[i][0]}", border=1)
            val_deduct = f"{deduct_list[i][1]:.0f}" if deduct_list[i][0] != "" else ""
            self.cell(35, 7, val_deduct, border=1, align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        gross_earnings = sum(val for name, val in earn_list)
        total_deductions = sum(val for name, val in deduct_list)
        net_pay = gross_earnings - total_deductions

        self.set_font('helvetica', 'B', 9)
        self.cell(60, 8, "Gross Earnings (A)", border=1)
        self.cell(35, 8, f"{gross_earnings:.0f}", border=1, align='R')
        self.cell(60, 8, "Total Deductions (B)", border=1)
        self.cell(35, 8, f"{total_deductions:.0f}", border=1, align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.ln(5)
        self.set_font('helvetica', 'B', 10)
        self.cell(40, 8, "Net Pay (A - B):")
        self.cell(0, 8, f"Rs. {net_pay:,.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pay_words = num2words(int(net_pay), lang='en_IN').title() + " Rupees Only"
        self.cell(40, 8, "Total Pay in Words:")
        self.set_font('helvetica', '', 10)
        self.cell(0, 8, pay_words, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.ln(10)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, "This is a computer-generated document and requires no signature.", align='C')


def send_payslip_email(to_email, emp_name, month, file_path, hr_email, hr_pass):
    msg = MIMEMultipart()
    msg['From'] = hr_email
    msg['To'] = to_email
    msg['Subject'] = f"Payslip {month} - {emp_name}"
    msg.attach(MIMEText(f"Hello {emp_name}, please find your payslip attached.", 'plain'))

    with open(file_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(file_path)}")
        msg.attach(part)
# try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(hr_email, hr_pass)
        server.send_message(msg)
#     return True  
# except Exception as e:
#     print(f"Failed to send to {to_email}:{e}")  
#     return False
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.mime.base import MIMEBase
# from email import encoders

# def send_payslip_email_optimized(server, recipient_email, name, month, pdf_path, sender_email):
#     try:
#         # 1. Setup the Email Container
#         msg = MIMEMultipart()
#         msg['From'] = sender_email
#         msg['To'] = recipient_email
#         msg['Subject'] = f"Payslip for {month}"

#         body = f"Hello {name},\n\nPlease find your payslip for {month} attached."
#         msg.attach(MIMEText(body, 'plain'))

#         # 2. Attach the PDF
#         with open(pdf_path, "rb") as attachment:
#             part = MIMEBase('application', 'octet-stream')
#             part.set_payload(attachment.read())
            
#         encoders.encode_base64(part)
#         part.add_header(
#             'Content-Disposition',
#             f'attachment; filename={os.path.basename(pdf_path)}',
#         )
#         msg.attach(part)

#         # 3. Send using the existing server connection (No login needed here)
#         server.send_message(msg)
#         return True

#     except Exception as e:
#         print(f"Failed to send to {recipient_email}: {e}")
#         return False
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_payslip_email_optimized(server, recipient_email, name, month, pdf_path, sender_email):
    try:
        # 1. Setup the Email Container
        msg = MIMEMultipart()
        
       
        msg['From'] = f"Star Dynamic Logistics India Pvt Ltd <{sender_email}>"
        msg['To'] = recipient_email
        
    
        msg['Subject'] = f"Payslip — {month}"

        # 2. Create the Forwarded-style HTML Body
        html_body = f"""
        <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #1a202c; line-height: 1.6;">
                <div style="margin-bottom: 20px; color: #718096; font-size: 13px;">
                    <p>---------- Forwarded message ---------</p>
                    <p><b>From:</b> Star Dynamic Logistics India Pvt Ltd &lt;{sender_email}&gt;</p>
                    <p><b>Subject:</b> Payslip — {month} </p>
                </div>
                
                <p>Dear <b>{name}</b>,</p>
                <p>Your payslip for <b>{month}</b> has been generated and is ready for your review. 
                                            Please find the detailed breakdown in the <b>PDF attachment</b> below.</p>
                <p>Regards,<br><b>FleetNxtGen Team</b></p>
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
                <p style="font-size: 11px; color: #a0aec0;">This is an automated system email. Please do not reply.</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html'))

        # 3. Attach the PDF
        with open(pdf_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename={os.path.basename(pdf_path)}',
        )
        msg.attach(part)

        # 4. Send the email
        server.send_message(msg)
        return True

    except Exception as e:
        print(f"Failed to send to {recipient_email}: {e}")
        return False    