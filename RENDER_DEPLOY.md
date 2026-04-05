# Deploy to Render.com

## Quick Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. Fork this repository to your GitHub
2. Go to [render.com](https://render.com)
3. Click **"New +"** → **"Web Service"**
4. Connect your GitHub repo
5. Configure:
   - **Name:** `face-attendance`
   - **Region:** Singapore (or nearest)
   - **Branch:** `main`
   - **Runtime:** `Python 3.11`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`

6. Add Environment Variables:
   ```
   SENDER_EMAIL = your_email@gmail.com
   SENDER_PASSWORD = your_16char_app_password
   CLASS_ADVISOR_EMAIL = advisor@college.edu
   HOD_EMAIL = hod@college.edu
   CLASS_NAME = CS-A
   EMAIL_ENABLED = true
   ```

7. Click **"Create Web Service"**

---

## Features on Render

### ✅ Working
- Web Dashboard at `https://your-app.onrender.com`
- REST API endpoints
- Email alerts (daily reports, security alerts)
- PDF report generation
- Database (SQLite)

### ⚠️ Limitations
- **Camera NOT available** on cloud servers
- Use **Headless Mode** for testing
- Face recognition requires physical device

---

## Access After Deploy

- **Dashboard:** `https://your-app-name.onrender.com`
- **API:** `https://your-app-name.onrender.com/api/v1/`

---

## Environment Variables

Required for email to work:

| Variable | Description |
|----------|-------------|
| `SENDER_EMAIL` | Gmail address |
| `SENDER_PASSWORD` | Gmail App Password (16 chars) |
| `CLASS_ADVISOR_EMAIL` | Advisor email |
| `HOD_EMAIL` | HOD email |
| `CLASS_NAME` | Your class name |
| `EMAIL_ENABLED` | `true` |

---

## Troubleshooting

**Camera not working?**
→ Normal! Cloud servers don't have cameras. Use Headless Mode.

**Email not sending?**
→ Check Gmail App Password is correct (16 chars, not regular password)

**Build fails?**
→ Ensure you have `opencv-contrib-python` not `opencv-python`
