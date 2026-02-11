# HROne Attendance Bot 🤖

A Python Selenium automation script designed to log in to the **HROne** portal and automatically mark attendance. This bot is optimized to run in a headless environment using **GitHub Actions**, allowing for scheduled Check-Ins and Check-Outs without manual intervention.

## 🚀 Features

*   **Automated Login**: Securely logs in using credentials stored in environment variables.
*   **Smart Attendance Marking**: Navigates the dashboard and handles the "Mark Attendance" confirmation popup.
*   **Robust Error Handling**:
    *   Uses **JavaScript clicks** to bypass loading spinners and overlays.
    *   Detects if the attendance popup is already open upon login.
    *   Retries elements with explicit waits.
*   **CI/CD Ready**: Configured to run in **Headless Mode** on GitHub Actions.

## 📂 Project Structure

```text
Attendance-BotV2/
├── attendance_bot.py       # Main automation script
├── requirements.txt        # Python dependencies
└── .github/
    └── workflows/
        └── attendance.yml  # GitHub Actions scheduler
```

## 🛠️ Prerequisites

*   Python 3.9+
*   Google Chrome (for local testing)

## ⚙️ Local Installation & Testing

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/attendance-bot-v2.git
    cd attendance-bot-v2
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set Environment Variables**:
    *   **Mac/Linux**:
        ```bash
        export HRONE_USER="your.email@example.com"
        export HRONE_PASS="your_password"
        ```
    *   **Windows (PowerShell)**:
        ```powershell
        $env:HRONE_USER="your.email@example.com"
        $env:HRONE_PASS="your_password"
        ```

4.  **Run the script**:
    ```bash
    python attendance_bot.py
    ```
    *(Note: To see the browser visually, change `HEADLESS_MODE = True` to `False` in line 20 of `attendance_bot.py`)*.

## ☁️ Setting up GitHub Actions

To run this automatically on a schedule, you do not need a server. GitHub Actions will handle it.

### 1. Add Secrets (Credentials)
For security, **never** hardcode your password in the script.
1.  Go to your GitHub Repository.
2.  Navigate to **Settings** > **Secrets and variables** > **Actions**.
3.  Click **New repository secret**.
4.  Add the following two secrets:
    *   Name: `HRONE_USER` -> Value: `your.email@company.com`
    *   Name: `HRONE_PASS` -> Value: `your_password`

### 2. Configure the Schedule (`attendance.yml`)
Create a file at `.github/workflows/attendance.yml`.

**Note on Timezones:** GitHub Actions runs in **UTC**. You must convert your IST time to UTC.
*   **IST is UTC +5:30**.
*   *Example:* 10:00 AM IST = 04:30 UTC.

**Sample Workflow:**
```yaml
name: HROne Attendance Bot

on:
  schedule:
    # Check In: Mon-Fri at 10:00 AM IST (04:30 UTC)
    - cron: '30 4 * * 1-5'
    
    # Check Out: Mon-Fri at 10:00 PM IST (16:30 UTC)
    - cron: '30 16 * * 1-5'
    
  # Allow manual trigger for testing
  workflow_dispatch:

jobs:
  mark-attendance:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install Dependencies
        run: pip install -r requirements.txt

      - name: Run Bot
        env:
          HRONE_USER: ${{ secrets.HRONE_USER }}
          HRONE_PASS: ${{ secrets.HRONE_PASS }}
        run: python attendance_bot.py
```

## 🐛 Troubleshooting

*   **Login Fails**: Ensure `HRONE_USER` and `HRONE_PASS` are set correctly in GitHub Secrets.
*   **Element Click Intercepted**: The script now uses `driver.execute_script("arguments[0].click();", element)` to force clicks even if a loading spinner is present.
*   **Time Drift**: GitHub Actions is free and sometimes queues jobs. The script might run 5-10 minutes later than the scheduled cron time.

## ⚠️ Disclaimer
This bot is for educational and personal productivity purposes. Please ensure its usage complies with your company's IT and HR policies. The author is not responsible for any misuse.