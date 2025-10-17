# Deployment Guide

This document explains how to deploy the project with:

- **Backend** running on [Koyeb](https://www.koyeb.com/) in the free tier.
- **Frontend** running on [Cloudflare Pages](https://pages.cloudflare.com/) using the free plan.

Please review the configuration section carefully before deploying.

---

## 1. Backend on Koyeb

### 1.1. Create the service

1. Push your latest changes to GitHub (or another Git provider supported by Koyeb).
2. In the Koyeb console, create a new **App**, and add a **Service**.
3. When prompted for the deployment method, choose **Git repository**.
4. Select your repository and the branch you want to deploy.
5. In **Build configuration**:
   - Set the **Build context** to `backend`.
   - Set the **Dockerfile path** to `backend/Dockerfile`.
6. In **Regions**, enable **Deploy to multiple regions** and select **Singapore** and **Tokyo** (or the closest Japan region available).
7. In **Instance size**, select the free `nano` instance type.
8. In **Autoscaling**, keep the free-tier default (1 instance).

### 1.2. Environment variables

Populate the environment variables required by the backend service:

| Variable | Purpose |
| --- | --- |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME_SOURCE`, `DB_NAME_TARGET` | Database connection (or leave blank when using Supabase). |
| `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_TABLE` | Enable Supabase integration if you rely on it. |
| `GEMINI_API_KEY` | Generative AI features. |
| `GMAIL_SENDER_EMAIL`, `GMAIL_APP_PASSWORD`, `GMAIL_SENDER_NAME` | Transactional emails (optional). |
| `HUNTER_API_KEY` | Email validation (optional). |
| `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRE_HOURS` | Authentication tokens. |
| `EMAIL_SEND_METHOD`, `RESEND_API_KEY`, `SENDGRID_API_KEY`, `MAILGUN_API_KEY`, `MAILGUN_DOMAIN` | Third-party email providers (if used). |
| Any additional secrets referenced in `backend/config/env.example` | Configure as needed. |

Optional OCR-specific variables:

- `TESSERACT_CMD`: Override the location of the `tesseract` binary if you install it in a non-default path.

> Keep secret values out of the repository. Add them only through Koyeb's UI or CLI.

### 1.3. Networking

- Expose port **8000** as HTTP.
- Add a route in Koyeb that targets `/` so that requests are forwarded to the FastAPI service.
- Once deployed, note the generated Koyeb domain (e.g., `https://your-app-your-service.koyeb.app`).

### 1.4. Health checks

The FastAPI app serves the OpenAPI schema at `/openapi.json`. You can use `/api/v1/auth/health` (if you add one) or any existing lightweight endpoint for Koyeb health checks. By default, the service will respond on `/`.

---

## 2. Frontend on Cloudflare Pages

### 2.1. Prepare the project

1. Ensure all frontend dependencies are committed (`package.json`, `package-lock.json`).
2. Verify the build locally with `npm run build`.

### 2.2. Deploy with Cloudflare Pages

1. In the Cloudflare dashboard, create a new **Pages** project.
2. Connect the same Git repository and choose the branch to deploy.
3. Use these build settings:
   - **Framework preset**: `Next.js`.
   - **Build command**: `npx @cloudflare/next-on-pages@latest build`.
   - **Build output directory**: `.vercel/output/static`.
   - **Functions directory**: `.vercel/output/functions`.
4. Set the **Node version** to `20` (Cloudflare's default is fine).
5. In **Environment variables**, add:
   - `NEXT_PUBLIC_API_URL`: set to the public Koyeb backend URL (for example, `https://your-app-your-service.koyeb.app`).
   - Any other `NEXT_PUBLIC_*` variables your frontend requires (see `src/lib/api.ts` and related modules).
6. Trigger the first deployment. Subsequent pushes to the connected branch will redeploy automatically.

### 2.3. Custom domain (optional)

If you want to use a custom domain:

1. Add the domain in Cloudflare Pages project settings.
2. Follow Cloudflare's DNS instructions to point the domain.
3. Configure CORS on the backend if you restrict origins (update `allow_origins` in `backend/app/main.py`).

---

## 3. Local verification

Before deploying, you can verify the Docker image and frontend build locally.

```bash
# Backend
cd backend
docker build -t study-backend .
docker run --rm -p 8000:8000 --env-file config.env study-backend

# Frontend
cd ..
npm run build
npm run start
```

Ensure the frontend's `.env.local` contains `NEXT_PUBLIC_API_URL=http://localhost:8000` when testing locally.

---

## 4. Operational overview

- Backend logs and metrics are available in the Koyeb console.
- Cloudflare Pages provides build logs and analytics per deployment.
- Keep the secrets updated in both platforms when they rotate.
- When you introduce breaking backend changes, redeploy the frontend after the backend deployment finishes to ensure clients load the latest build.

---

## 5. Checklist

- [ ] Secrets configured in Koyeb.
- [ ] Backend service running in Singapore and Japan regions.
- [ ] Cloudflare Pages build succeeds with the correct API URL.
- [ ] Optional custom domain configured for both backend and frontend.

Following these steps lets you deploy the project end-to-end using the free tiers of Koyeb and Cloudflare.
