import pandas as pd
import smtplib
import json
import os
from datetime import date, timedelta
from email.message import EmailMessage

EXCEL_FILE = 'schedule.xlsx'
EXCEPTIONS_FILE = 'exceptions.json'
SEND_EMPTY_EMAIL = False # Set to True if you want an email saying "No classes"

SEMESTER_START_DATE = date(2026, 2, 23) 

# The script will pause the Odd/Even cycle during these weeks.
HOLIDAY_WEEKS_MONDAYS = [
    date(2026, 4, 13), # Example: Spring Break week
]

def load_data():
    """Loads the schedule and handles file not found errors."""
    if not os.path.exists(EXCEL_FILE):
        raise FileNotFoundError(f"Could not find {EXCEL_FILE}")
    
    # Load excel, treat all columns as strings to avoid format issues
    df = pd.read_excel(EXCEL_FILE, dtype=str)
    
    # Clean whitespace from column headers and values
    df.columns = df.columns.str.strip()
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    return df

def get_academic_week_parity(today_date):
    """
    Calculates if the current academic week is 'odd' or 'even', 
    accounting for holiday weeks that pause the cycle.
    """
    # Find the Monday of the current week and the start week
    current_monday = today_date - timedelta(days=today_date.weekday())
    start_monday = SEMESTER_START_DATE - timedelta(days=SEMESTER_START_DATE.weekday())
    
    if current_monday < start_monday:
        return "all" # Fallback if run before semester starts
        
    # Calculate total calendar weeks elapsed since semester start
    days_elapsed = (current_monday - start_monday).days
    calendar_weeks_elapsed = days_elapsed // 7
    
    # Count how many holiday weeks have occurred up to this point
    holidays_passed = sum(1 for hw in HOLIDAY_WEEKS_MONDAYS if hw <= current_monday)
    
    # Calculate true academic week index (0 = Week 1, 1 = Week 2)
    academic_week_index = calendar_weeks_elapsed - holidays_passed
    
    # If the current week IS a holiday week
    if current_monday in HOLIDAY_WEEKS_MONDAYS:
        return "holiday"
        
    return "even" if academic_week_index % 2 != 0 else "odd"

def get_todays_exceptions():
    """Parses exceptions.json to see if there are specific rules for today."""
    if not os.path.exists(EXCEPTIONS_FILE):
        return None

    try:
        with open(EXCEPTIONS_FILE, 'r') as f:
            data = json.load(f)
            
        today_str = date.today().strftime("%Y-%m-%d")
        
        for entry in data:
            if entry.get("date") == today_str:
                return entry
    except json.JSONDecodeError:
        print("Warning: JSON file is malformed. Ignoring exceptions.")
    
    return None

def format_email_body(classes, date_str):
    """Generates an HTML body for the email."""
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #2E86C1;">📅 Schedule for {date_str}</h2>
            <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Time</th>
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Course</th>
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Room</th>
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Type</th>
                </tr>
    """
    
    for _, row in classes.iterrows():
        html_content += f"""
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;">{row['Time']}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>{row['Course']}</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{row['Room']}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{row['Type']}</td>
                </tr>
        """
        
    html_content += """
            </table>
            <br>
            <p style="font-size: small; color: gray;">Automated by Python 🐍</p>
        </body>
    </html>
    """
    return html_content

def send_email(subject, body_html):
    """Sends the email using Environment Variables."""
    email_address = os.environ.get('EMAIL_USER')
    email_password = os.environ.get('EMAIL_PASS')

    if not email_address or not email_password:
        print("❌ Error: Environment variables EMAIL_USER or EMAIL_PASS are missing.")
        return

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = email_address
    msg['To'] = email_address
    msg.set_content("Your email client does not support HTML.") # Fallback
    msg.add_alternative(body_html, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email_address, email_password)
            smtp.send_message(msg)
            print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def main():
    # 1. Get Today's Info
    today = date.today()
    today_day_name = today.strftime("%A") # e.g., "Monday"
    today_str = today.strftime("%Y-%m-%d")
    
    print(f"Processing schedule for: {today_day_name}, {today_str}")

    # 2. Load Data
    try:
        df = load_data()
    except Exception as e:
        print(e)
        return

    # 3. Filter by Day of Week
    if 'Day' not in df.columns:
        print("❌ Error: 'Day' column not found in Excel file.")
        return
        
    daily_classes = df[df['Day'].str.lower() == today_day_name.lower()]

    if daily_classes.empty:
        print("No classes scheduled for today (based on Excel day).")
        if SEND_EMPTY_EMAIL:
             send_email(f"📅 Schedule: Free Day!", "<h3>No classes today! 🎉</h3>")
        return

    # 4. Filter by Academic Week Parity (Odd/Even)
    if 'WeekType' not in daily_classes.columns:
        print("❌ Error: 'WeekType' column not found in Excel file.")
        return
        
    current_parity = get_academic_week_parity(today)
    
    if current_parity == "holiday":
        print("Enjoy your holiday! No classes this week.")
        if SEND_EMPTY_EMAIL:
             send_email("📅 Schedule: Holiday!", "<h3>It's a holiday week! No classes. 🎉</h3>")
        return

    print(f"Current Academic Week Parity: {current_parity.capitalize()}")

    daily_classes = daily_classes[
        (daily_classes['WeekType'].fillna('all').str.lower() == 'all') | 
        (daily_classes['WeekType'].fillna('all').str.lower() == current_parity)
    ]

    exception_rule = get_todays_exceptions()
    
    if exception_rule:
        print(f"Found exceptions for today: {exception_rule.get('note', 'No note')}")
        
        # Filter out cancelled hours
        cancel_hours = exception_rule.get("cancel_hours", [])
        if cancel_hours:
            daily_classes = daily_classes[~daily_classes['Time'].isin(cancel_hours)]

        # Filter out cancelled courses
        cancel_courses = exception_rule.get("cancel_courses", [])
        if cancel_courses:
            pattern = '|'.join(cancel_courses) 
            if pattern:
                 daily_classes = daily_classes[~daily_classes['Course'].str.contains(pattern, case=False, na=False)]

    # 6. Final Check and Send
    if daily_classes.empty:
        print("All remaining classes for today were filtered out (parity or exceptions).")
        if SEND_EMPTY_EMAIL:
            send_email(f"📅 Schedule: {today_str}", "<h3>No classes to attend today! 🎉</h3>")
    else:
        print(f"Sending email with {len(daily_classes)} classes...")
        body = format_email_body(daily_classes, today_str)
        send_email(f"📅 Uni Schedule for {today_str}", body)

if __name__ == "__main__":
    main()