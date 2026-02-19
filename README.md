# 📅 Uni-Schedule Automated Notifier

A serverless Python automation tool that reads a university schedule from an Excel file, applies dynamic exceptions (like sick teachers or holidays), and emails a daily agenda. 

It runs completely in the cloud using **GitHub Actions**, requiring zero server maintenance.

## ✨ Key Features
* **Cloud Automation:** Runs automatically every morning at 07:00 AM using a GitHub Actions cron job.
* **Smart Parsing:** Uses `pandas` to extract only the relevant classes for the current day from a standard `.xlsx` schedule.
* **Granular Exceptions System:** Reads an `exceptions.json` file to cancel either full days (holidays) or specific time slots (e.g., "Skip the 10:00-12:00 class today").
* **Secure Email Delivery:** Sends HTML-formatted daily agendas using Python's `smtplib`, pulling credentials securely from GitHub Secrets.

## 🏗️ Architecture & Logic

1. **Trigger:** A GitHub Action workflow wakes up daily at 07:00 UTC.
2. **Fetch Data:** The script loads `schedule.xlsx`.
3. **Check Exceptions:** The script checks `exceptions.json`. If today has an exception, it modifies or clears the daily schedule.
4. **Notify:** If there are classes remaining, it formats them into a clean email and sends it via an SMTP server.

## 🛠️ How the Exception System Works

Instead of hardcoding days off, the script relies on `exceptions.json`. You can easily edit this file directly from the GitHub Mobile app whenever a teacher cancels a class.

**Example `exceptions.json`:**
```json
{
  "full_days_off": [
    "2024-12-25",
    "2024-05-01"
  ],
  "partial_cancellations": [
    {
      "date": "2024-10-12",
      "exclude_hours": ["10:00-12:00"],
      "reason": "USO Teacher Sick"
    }
  ]
}
```

## 🔐 Setup Instructions (For Forking)

If you want to use this for your own schedule, follow these steps:

1. **Fork the Repository** and replace `schedule.xlsx` with your own.
2. **Generate an App Password:** * Go to your Google Account > Security > 2-Step Verification > App Passwords.
   * Generate a new password (e.g., "GitHub Actions Bot").
3. **Set GitHub Secrets:**
   * Go to your repository `Settings > Secrets and variables > Actions`.
   * Add `SENDER_EMAIL` (your Gmail address).
   * Add `EMAIL_PASSWORD` (the 16-character App Password).
   * Add `RECEIVER_EMAIL` (where you want the schedule sent).
4. **Enable Actions:** Go to the "Actions" tab and enable workflows to start the daily cron job.

## 🧰 Built With
* Python 3
* `pandas` & `openpyxl` (Data Extraction)
* `smtplib` & `email` (Notification)
* GitHub Actions (CI/CD Pipeline)
