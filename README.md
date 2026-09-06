# HROne Attendance Bot 🤖

A Python Selenium automation script designed to log in to the **HROne** portal and automatically mark attendance. This bot runs in a headless environment on **GitHub Actions**, triggered on a schedule by a **cron job on a home server** (not GitHub's native `schedule:` event — see [Scheduling](#-scheduling-why-a-home-server-cron-job) below for why).

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
        └── attendace.yml   # GitHub Actions workflow (manually/API-dispatched)
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

### 1. Add Secrets (Credentials)
For security, **never** hardcode your password in the script.
1.  Go to your GitHub Repository.
2.  Navigate to **Settings** > **Secrets and variables** > **Actions**.
3.  Click **New repository secret**.
4.  Add: `HRONE_URL`, `HRONE_USER`, `HRONE_PASS`, `LATITUDE`, `LONGITUDE`.

### 2. Workflow trigger
`.github/workflows/attendace.yml` defines only `workflow_dispatch:` (no `schedule:`). It runs when triggered manually from the Actions tab, or via the GitHub API/`gh` CLI — see below.

## ⏰ Scheduling: why a home-server cron job

GitHub's native `schedule:` (cron) trigger is **best-effort, not guaranteed to fire on time** — during high load it can be dispatched hours late (observed up to ~12h late in this project), which defeats the purpose of a 10 AM check-in. GitHub itself creates the run late; it's not a runner-queue issue, so a self-hosted runner would **not** fix it.

The fix: keep execution on GitHub's hosted runner (free, zero maintenance, full Actions-tab visibility/logs/artifacts/failure emails), but move the **trigger** to a cron job on a machine you control, which calls the GitHub API to dispatch the workflow at the exact time.

### One-time setup on the home server

1.  **Install the GitHub CLI** (`gh`):
    ```bash
    # Debian/Ubuntu
    type -p curl >/dev/null || (sudo apt update && sudo apt install curl -y)
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt update && sudo apt install gh -y

    # macOS
    brew install gh
    ```

2.  **Create a scoped token**: on github.com go to **Settings > Developer settings > Personal access tokens > Fine-grained tokens** and generate one limited to just this repository, with **Actions: Read and write** permission. (Do *not* reuse a broad, all-repo token here.)

3.  **Authenticate `gh` non-interactively** (needed for cron, which has no TTY):
    ```bash
    echo "PASTE_YOUR_TOKEN_HERE" | gh auth login --with-token
    gh auth status
    ```

4.  **Smoke-test the dispatch**:
    ```bash
    gh workflow run attendace.yml --repo snipep/Attendance-botV2 --ref main
    gh run list --repo snipep/Attendance-botV2 --workflow=attendace.yml --limit 1
    ```

5.  **Check the server's timezone** (`timedatectl` or `date`) so the crontab times below are correct for either IST or UTC.

6.  **Add the crontab entries** (`crontab -e`) — targets 10:00 AM / 10:00 PM IST, Mon–Fri:
    ```cron
    # If the server clock is IST:
    0 10 * * 1-5 gh workflow run attendace.yml --repo snipep/Attendance-botV2 --ref main >> ~/attendance-trigger.log 2>&1
    0 22 * * 1-5 gh workflow run attendace.yml --repo snipep/Attendance-botV2 --ref main >> ~/attendance-trigger.log 2>&1

    # If the server clock is UTC (10:00/22:00 IST = 04:30/16:30 UTC):
    30 4  * * 1-5 gh workflow run attendace.yml --repo snipep/Attendance-botV2 --ref main >> ~/attendance-trigger.log 2>&1
    30 16 * * 1-5 gh workflow run attendace.yml --repo snipep/Attendance-botV2 --ref main >> ~/attendance-trigger.log 2>&1
    ```
    Use only the block matching your server's timezone.

7.  **Keep the server always-on and time-synced** (NTP). A machine that sleeps/hibernates will silently miss the cron firing — this reintroduces the exact problem being fixed. On Linux, prefer a `systemd` timer with `Persistent=true` over plain cron if the box can be briefly offline, since it catches up missed runs on boot.

8.  *(Optional but recommended)* Add a watchdog cron ~30 minutes after each trigger to confirm the run actually succeeded, and alert yourself (email/Telegram) if not:
    ```bash
    gh run list --repo snipep/Attendance-botV2 --workflow=attendace.yml --limit 1 --json conclusion,createdAt
    ```

### Verifying / monitoring runs
Because the trigger is still a normal GitHub Actions run (`workflow_dispatch` event), everything you already rely on keeps working, from anywhere with `gh` access:
```bash
gh run list --repo snipep/Attendance-botV2 --workflow=attendace.yml --limit 10
gh run view <run-id> --repo snipep/Attendance-botV2 --log
```
Or in the browser: repo → **Actions** tab → *HROne Attendance Bot*. Failed runs upload an `error-screenshot` artifact (see workflow), and GitHub emails you on workflow failure if that's enabled in your notification settings.

## 🐛 Troubleshooting

*   **Login Fails**: Ensure `HRONE_USER` and `HRONE_PASS` are set correctly in GitHub Secrets.
*   **Element Click Intercepted**: The script now uses `driver.execute_script("arguments[0].click();", element)` to force clicks even if a loading spinner is present.
*   **Run didn't fire at all**: Check the home server's cron actually executed (`~/attendance-trigger.log`, `grep CRON /var/log/syslog`) — GitHub's native `schedule:` trigger is no longer used, so a missed run now means the server-side cron or `gh auth` token failed, not GitHub-side delay.
*   **`gh: To use GitHub CLI...` auth errors on cron**: the token likely expired or wasn't set up with `--with-token` (interactive `gh auth login` doesn't persist for a non-login cron shell in some setups) — re-run step 3 above.

## ⚠️ Disclaimer
This bot is for educational and personal productivity purposes. Please ensure its usage complies with your company's IT and HR policies. The author is not responsible for any misuse.