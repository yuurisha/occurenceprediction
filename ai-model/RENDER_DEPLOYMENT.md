# Deploying AI Prediction API to Render

This guide helps you deploy the FastAPI AI prediction model to Render.com so it works with your Vercel frontend.

## Step 1: Prepare for Deployment

### Create a `build.sh` script in ai-model/:

```bash
#!/bin/bash
pip install -r requirements.txt
```

### Create a `start.sh` script in ai-model/:

```bash
#!/bin/bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app --bind 0.0.0.0:$PORT
```

Make it executable:
```powershell
# Windows - add to source control as-is
# Linux/Mac
chmod +x ai-model/start.sh
```

## Step 2: Create Render Web Service

1. Go to [render.com](https://render.com)
2. Sign in with GitHub
3. Click **New +** → **Web Service**
4. Connect your GitHub repository
5. Configure:
   - **Name**: `florai-ai-api` (or any name)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r ai-model/requirements.txt`
   - **Start Command**: `cd ai-model && gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app`
   - **Plan**: Free tier is fine for testing

6. Click **Create Web Service**
7. Wait for deployment (5-10 minutes)
8. Copy your API URL (e.g., `https://florai-ai-api.onrender.com`)

## Step 3: Add serviceAccountKey.json to Render

The API needs Firebase credentials. Add it as a secret:

1. In Render dashboard, go to your service
2. Click **Environment**
3. Add a secret file:
   - **Key**: `SERVICE_ACCOUNT_KEY` (or set in code)
   - **Value**: Paste contents of `florai/model_server/serviceAccountKey.json`

Or, copy the file to ai-model/:
```bash
cp florai/model_server/serviceAccountKey.json ai-model/
```

## Step 4: Update Frontend Environment Variables

Update your Vercel deployment:

1. Go to [vercel.com](https://vercel.com) dashboard
2. Select your `florai` project
3. Go to **Settings** → **Environment Variables**
4. Update or add:
   ```
   NEXT_PUBLIC_AI_MODEL_API=https://florai-ai-api.onrender.com
   ```

5. Redeploy your frontend

Or update locally and push:

```bash
cd florai
# Update .env.local
NEXT_PUBLIC_AI_MODEL_API=https://florai-ai-api.onrender.com

# Commit and push
git add .env.local
git commit -m "Update AI API endpoint to Render"
git push
```

## Step 5: Test the Deployment

1. Go to your Vercel frontend
2. Navigate to `/Dashboard/ai`
3. Click on the map
4. Check for predictions in the UI
5. Check AI notification bell for alerts

## Troubleshooting

### API returns 500 error

Check Render logs:
1. Go to Render dashboard → your service
2. Click **Logs** tab
3. Look for error messages

**Common issues:**
- Missing `serviceAccountKey.json`: Upload as environment secret
- Model files missing: Ensure `*.pkl` files are committed to git
- Port binding: Make sure START command uses `$PORT` variable

### No notifications appear

1. Check user preferences in Firebase
2. Verify `NOTIFICATIONS_ENABLED=True` in api.py
3. Check browser console for API errors

### Slow predictions

- Render free tier has limited resources
- Upgrade to paid plan for production
- Or use a more powerful cloud provider (AWS, GCP, Azure)

## Optional: Custom Domain

1. In Render dashboard, go to your service
2. Click **Settings** → **Custom Domain**
3. Add your domain (requires DNS configuration)

## Cost

- **Free tier**: $0 (limited resources, sleeps after inactivity)
- **Paid tiers**: Start at $7/month

For development/testing, free tier is sufficient. For production, upgrade to Starter plan.

## Next Steps

1. ✅ API deployed to Render
2. ✅ Frontend updated to use Render API
3. Test the complete flow
4. Monitor performance and logs
5. Consider upgrading plan if needed

## Deployment Checklist

- [ ] Build script created (`build.sh`)
- [ ] Start script created (`start.sh`)
- [ ] Repository pushed to GitHub
- [ ] Render service created
- [ ] Firebase credentials added
- [ ] Environment variables updated
- [ ] Frontend redeployed to Vercel
- [ ] Tested end-to-end flow
