# 🌐 24/7 Cloud Deployment Guide (Runs When Laptop is OFF)

Follow this simple guide to deploy your **Kotak Neo Live Market Server Pro** to the cloud so it runs **24/7/365 with 99.99% uptime** even when your laptop is completely powered off.

---

## 🚀 Option 1: Deploy to Render.com (100% Free)

Render provides a free 24/7 web service with automated GitHub integration.

### Step 1: Create a GitHub Repository
1. Go to [github.com/new](https://github.com/new).
2. Name your repository (e.g. `kotak-neo-pro`) and set it to **Private** (recommended to keep your environment config private).
3. In your local terminal / PowerShell, link and push your code:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/kotak-neo-pro.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Create a Free Web Service on Render
1. Go to [dashboard.render.com](https://dashboard.render.com/) and click **"New +"** $\rightarrow$ **"Web Service"**.
2. Connect your GitHub repository `kotak-neo-pro`.
3. Fill in the basic settings:
   * **Name**: `kotak-neo-pro`
   * **Region**: `Singapore (ap-southeast-1)` or `Frankfurt` (closest to India)
   * **Branch**: `main`
   * **Runtime**: `Python 3`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `python server.py`
   * **Instance Type**: `Free`

### Step 3: Add Environment Variables in Render
Under **Environment Variables**, add your Kotak Neo credentials from `.env`:
* `KOTAK_NEO_CONSUMER_KEY` = your_consumer_key
* `KOTAK_NEO_CONSUMER_SECRET` = your_consumer_secret
* `KOTAK_NEO_MOBILE_NUMBER` = your_registered_mobile
* `KOTAK_NEO_PASSWORD` = your_password
* `KOTAK_NEO_MPIN` = your_mpin
* `KOTAK_NEO_TOTP_KEY` = your_totp_secret_key

### Step 4: Click "Create Web Service"
In 2-3 minutes, Render will build and deploy your app. You will receive a permanent HTTPS link:
$$\mathbf{https://kotak-neo-pro.onrender.com}$$

---

## ⚡ Option 2: Deploy to Railway.app (1-Click)

1. Go to [railway.app](https://railway.app) and sign up with GitHub.
2. Click **"New Project"** $\rightarrow$ **"Deploy from GitHub repo"**.
3. Select `kotak-neo-pro`.
4. Add your `.env` variables in the Railway Variables tab.
5. Railway will automatically detect the `Dockerfile` / `Procfile` and deploy your app instantly!

---

## 🏠 Option 3: Keep Running on Current Laptop (Lid Closed / Home Server)

If you don't want to use cloud hosting and want zero setup:
1. Open Windows **Control Panel** $\rightarrow$ **Power Options**.
2. Click **"Choose what closing the lid does"**.
3. Set **"When I close the lid"** (Plugged in) $\rightarrow$ **"Do nothing"**.
4. Leave your laptop plugged in with the lid closed.
5. Access your dashboard 24/7 worldwide at:
   $$\mathbf{https://inspiration-constant-governments-sail.trycloudflare.com}$$
