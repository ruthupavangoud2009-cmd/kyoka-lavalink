# Render Free Tier 24/7 Keep-Alive Guide

This guide explains how Render's Free Tier works and how to keep your **Kyoka Lavalink V4** service active **24/7** without paying anything.

---

## 1. How Render Free Tier Works

1. **Inactivity Sleep**: Render Free Web Services automatically spin down ("sleep") after **15 minutes** of no incoming HTTP traffic.
2. **Cold Starts**: When an incoming request arrives at a sleeping service, Render wakes it up. This cold start takes approximately **30 to 50 seconds**.
3. **Monthly Free Allowance**: Render grants **750 free instance hours per calendar month** per account.
   - In a 31-day month: $31 \times 24 = 744\text{ hours}$.
   - **744 hours < 750 hours**: This means **one free service can run 24 hours a day, 7 days a week, 365 days a year without incurring any charges!**

---

## 2. The 24/7 Keep-Alive Strategy

To prevent Render from ever going to sleep, you simply need an automated HTTP request to ping the server at least once every **10 to 14 minutes** (before the 15-minute inactivity timer expires).

The optimal endpoint to ping is:
```
GET https://<your-service-name>.onrender.com/version
```
- It is unauthenticated (no password needed).
- It returns HTTP `200 OK` in under 10ms with almost zero CPU/RAM consumption.
- It resets the Render idle timer continuously.

---

## 3. Four Methods to Keep Your Service Alive 24/7

Choose whichever method fits your setup:

### Method A: Free External Monitor (Recommended - Most Reliable)

Services like [Cron-job.org](https://cron-job.org) or [UptimeRobot](https://uptimerobot.com) are 100% free and run independently in the cloud.

#### Setup via Cron-job.org (Free):
1. Sign up for a free account at [cron-job.org](https://cron-job.org).
2. Click **Create Cronjob**.
3. Set **Title**: `Kyoka Lavalink Keepalive`.
4. Set **URL**: `https://<your-service-name>.onrender.com/version`.
5. Set **Execution schedule**: Every `10 minutes`.
6. Click **Create**.
*Your Lavalink node will now stay awake 24/7.*

#### Setup via UptimeRobot (Free):
1. Sign up for a free account at [uptimerobot.com](https://uptimerobot.com).
2. Click **Add New Monitor**.
3. Monitor Type: `HTTP(s)`.
4. Friendly Name: `Kyoka Lavalink`.
5. URL: `https://<your-service-name>.onrender.com/version`.
6. Monitoring Interval: `Every 5 minutes` or `Every 10 minutes`.
7. Click **Create Monitor**.

---

### Method B: GitHub Actions Keep-Alive Workflow (Built-in)

This repository includes a pre-built GitHub Actions workflow in [`workflows/keepalive.yml`](../workflows/keepalive.yml).

To activate it:
1. In your GitHub repository (`kyoka-lavalink`), move or copy `workflows/keepalive.yml` into `.github/workflows/keepalive.yml` (e.g. via the GitHub web editor or using a PAT with `workflow` scope).
2. Go to **Settings** -> **Secrets and variables** -> **Actions**.
2. Click **New repository variable**.
3. Name: `RENDER_SERVICE_URL`.
4. Value: `https://<your-service-name>.onrender.com`.
5. Click **Add variable**.
6. The workflow will run automatically every 10 minutes via GitHub Actions cron, pinging your Lavalink node and keeping it warm.

---

### Method C: Local or VPS Keep-Alive Daemon

If you are running Kyoka bot on a VPS or desktop, you can run the included Python keep-alive script in the background:

```bash
# Continuous daemon pinging every 9 minutes (540 seconds)
python scripts/keepalive.py --url https://<your-service-name>.onrender.com --interval 540
```

On Linux (using screen or systemd):
```bash
./scripts/keepalive.sh https://<your-service-name>.onrender.com 540 &
```

On Windows (PowerShell):
```powershell
.\scripts\keepalive.ps1 -Url "https://<your-service-name>.onrender.com" -Interval 540
```

---

### Method D: Kyoka Discord Bot Auto-Wake Behavior

If your Lavalink node does happen to sleep (e.g. before keep-alive was configured):
1. When a user in Discord runs a music command (e.g., `+play`), Kyoka attempts to connect.
2. The initial HTTP request wakes up the Render container.
3. Within 30-50 seconds, Render finishes starting Lavalink V4.
4. Kyoka's reconnect handler in `src/core/lavalink.py` automatically retries connection and links the audio player.

---

## 4. Free-Tier Quota Tracking

You can monitor your free tier usage anytime in the [Render Billing Dashboard](https://dashboard.render.com/billing).
As long as you only run **one Free Web Service**, your total usage will always stay under 750 hours/month ($0.00 bill).
