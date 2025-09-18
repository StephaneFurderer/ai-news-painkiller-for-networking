# 🚀 Production Deployment Guide

This guide will help you deploy your LinkedIn Content Generator to production using Railway.

## 📋 Prerequisites

1. **GitHub Repository**: Push your code to GitHub
2. **Railway Account**: Sign up at [railway.app](https://railway.app)
3. **Required Services**:
   - OpenAI API key
   - Supabase project
   - Telegram Bot Token (optional)
   - Readwise API Token (optional)

## 🎯 Deployment Options

### Option 1: Railway (Recommended)

Railway is the easiest option for your full-stack application.

#### Step 1: Prepare Your Repository

1. Push your code to GitHub:
```bash
git add .
git commit -m "Add deployment configuration"
git push origin main
```

#### Step 2: Deploy to Railway

**Option A: Deploy Backend Only (Recommended for first deployment)**

1. Go to [railway.app](https://railway.app) and sign in
2. Click "New Project"
3. Choose "Deploy from GitHub repo"
4. Select your repository
5. **Important**: Set the **Root Directory** to `standalone-chat`
6. Railway will use the `railway-backend.toml` configuration

**Option B: Deploy Both Services**

1. Create two separate Railway services:
   - **Backend Service**: Root directory = `standalone-chat`
   - **Frontend Service**: Root directory = `standalone-chat/standalone-chat-ui`

#### Step 3: Configure Environment Variables

In Railway dashboard, go to your project → Variables tab and add:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Optional
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
READWISE_API_TOKEN=your_readwise_api_token_here
ENVIRONMENT=production
```

#### Step 4: Deploy Frontend

1. In Railway, create a new service
2. Connect to your GitHub repo
3. Set root directory to `standalone-chat-ui`
4. Add environment variable:
```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
```

### Option 2: Vercel + Railway (Alternative)

If you prefer Vercel for the frontend:

#### Backend (Railway)
1. Follow Steps 1-3 from Option 1
2. Your backend will be available at `https://your-app.railway.app`

#### Frontend (Vercel)
1. Go to [vercel.com](https://vercel.com)
2. Import your GitHub repository
3. Set root directory to `standalone-chat-ui`
4. Add environment variable:
```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
```

### Option 3: Render (Alternative)

1. Go to [render.com](https://render.com)
2. Create a new Web Service
3. Connect your GitHub repository
4. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`

## 🔧 Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | Your OpenAI API key for GPT models |
| `SUPABASE_URL` | ✅ | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | Supabase service role key (for admin operations) |
| `SUPABASE_ANON_KEY` | ✅ | Supabase anonymous key (for client operations) |
| `TELEGRAM_BOT_TOKEN` | ❌ | Telegram bot token (if using Telegram integration) |
| `READWISE_API_TOKEN` | ❌ | Readwise API token (for article retrieval) |
| `ENVIRONMENT` | ❌ | Set to `production` for production deployments |

## 📊 Database Setup

Your app uses Supabase for data storage. Make sure your Supabase project has these tables:

1. **conversations** - Stores chat conversations
2. **messages** - Stores individual messages
3. **content_templates** - Stores LinkedIn post templates
4. **system_prompts** - Stores AI agent prompts

Run the SQL script in `src/tools/create_chat_store_tables.sql` in your Supabase SQL editor.

## 🔍 Post-Deployment Checklist

- [ ] Backend API is accessible at `/docs` endpoint
- [ ] Frontend loads without errors
- [ ] OpenAI API calls work
- [ ] Supabase connection is working
- [ ] Telegram bot responds (if configured)
- [ ] Readwise integration works (if configured)
- [ ] File uploads work
- [ ] CORS is properly configured

## 🚨 Troubleshooting

### Common Issues:

1. **CORS Errors**: Make sure your frontend URL is in the `allowed_origins` list in `server.py`
2. **Environment Variables**: Double-check all required variables are set
3. **Database Connection**: Verify Supabase credentials and table structure
4. **OpenAI API**: Ensure API key has sufficient credits

### Logs:
- Railway: Check logs in the Railway dashboard
- Vercel: Check logs in the Vercel dashboard
- Render: Check logs in the Render dashboard

## 💰 Cost Estimation

**Railway (Recommended)**:
- Backend: $5/month for hobby plan
- Frontend: Free (if using Railway for both)
- Total: ~$5/month

**Vercel + Railway**:
- Backend (Railway): $5/month
- Frontend (Vercel): Free for hobby plan
- Total: ~$5/month

**Render**:
- Backend: $7/month for starter plan
- Frontend: Free for static sites
- Total: ~$7/month

## 🔄 Continuous Deployment

Once set up, your deployments will be automatic:
- Push to `main` branch → Automatic deployment
- Environment variables persist across deployments
- Zero-downtime deployments

## 📞 Support

If you encounter issues:
1. Check the logs in your deployment platform
2. Verify environment variables
3. Test locally first with production environment variables
4. Check API quotas and limits

---

**Next Steps**: Choose your preferred option and follow the steps above. Railway is recommended for the easiest setup!
