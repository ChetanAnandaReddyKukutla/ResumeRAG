# 🚀 Deployment Guide - ResumeRAG

## Prerequisites

- GitHub repository with latest code (✅ Done!)
- OpenAI API key for embeddings
- Choose a deployment platform

---

## 🎯 Recommended: Render.com Deployment

### Why Render?
- ✅ Free PostgreSQL database (with pgvector)
- ✅ Free Redis instance
- ✅ Docker support
- ✅ Automatic HTTPS
- ✅ Easy environment variable management
- ✅ GitHub integration for auto-deploy

### Step-by-Step Deployment

#### 1. **Prepare Environment Variables**

Create a `.env.production` file locally (DON'T commit this):

```bash
# Required
OPENAI_API_KEY=sk-your-actual-openai-key
SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Optional (Render will provide)
DATABASE_URL=<from-render-dashboard>
REDIS_URL=<from-render-dashboard>
```

#### 2. **Deploy Backend API to Render**

1. **Go to Render Dashboard**: https://dashboard.render.com/
2. **Create New Web Service**:
   - Connect your GitHub repo: `ChetanAnandaReddyKukutla/ResumeRAG`
   - Root Directory: `api`
   - Environment: `Docker`
   - Branch: `main`

3. **Set Environment Variables** in Render:
   ```
   OPENAI_API_KEY=<your-key>
   SECRET_KEY=<generated-key>
   ENCRYPTION_KEY=<generated-key>
   DATABASE_URL=<from-render-db>
   REDIS_URL=<from-render-redis>
   CORS_ALLOWED_ORIGINS=https://your-frontend-url.vercel.app
   ```

4. **Create PostgreSQL Database**:
   - New PostgreSQL
   - Name: `resumerag-db`
   - Plan: Free
   - Copy connection string to `DATABASE_URL`

5. **Create Redis Instance**:
   - New Redis
   - Name: `resumerag-redis`
   - Plan: Free
   - Copy connection string to `REDIS_URL`

6. **Deploy!** 🎉

#### 3. **Deploy Frontend to Vercel**

Vercel is perfect for React apps:

1. **Go to Vercel**: https://vercel.com
2. **Import Git Repository**: `ChetanAnandaReddyKukutla/ResumeRAG`
3. **Configure Project**:
   - Framework Preset: `Vite`
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`

4. **Environment Variables** (in Vercel):
   ```
   VITE_API_URL=https://your-render-api.onrender.com
   ```

5. **Update `vite.config.js`**:
   ```javascript
   export default defineConfig({
     server: {
       proxy: {
         '/api': {
           target: process.env.VITE_API_URL || 'http://localhost:8000',
           changeOrigin: true
         }
       }
     }
   })
   ```

6. **Deploy!** 🎉

---

## 🐳 Alternative: Docker-Based Platforms

### **Railway.app** (Easiest Docker Deployment)

1. **Go to Railway**: https://railway.app
2. **New Project** → **Deploy from GitHub**
3. **Select repo**: `ChetanAnandaReddyKukutla/ResumeRAG`
4. **Railway will automatically**:
   - Detect `docker-compose.yml`
   - Create services for each container
   - Set up networking
   - Provide URLs

5. **Set Environment Variables**:
   - Add `OPENAI_API_KEY`
   - Railway auto-generates `DATABASE_URL`, `REDIS_URL`

6. **Cost**: ~$5-10/month for starter

**Pros**: One-click deploy, Docker-native, very simple
**Cons**: Not free (but affordable)

### **DigitalOcean App Platform**

1. **Create Account**: https://cloud.digitalocean.com
2. **Apps** → **Create App**
3. **Choose Source**: GitHub → `ResumeRAG`
4. **App Spec**:
   - Frontend: Static Site (from `frontend/`)
   - Backend: Web Service (from `api/`)
   - Database: Managed PostgreSQL
   - Redis: Managed Redis

5. **Cost**: ~$12/month (includes DB)

---

## ☁️ Production-Grade: AWS/Azure/GCP

### **AWS Deployment (Container-based)**

**Services Needed**:
- **ECS Fargate**: Run Docker containers
- **RDS PostgreSQL**: Managed database
- **ElastiCache Redis**: Managed Redis
- **CloudFront + S3**: Frontend hosting
- **ALB**: Load balancer
- **Route53**: DNS

**Estimated Cost**: $50-100/month

**Steps**: See `docs/DEPLOYMENT.md` for detailed AWS guide

### **Azure Deployment**

**Services Needed**:
- **Azure Container Apps**: Run containers
- **Azure Database for PostgreSQL**: With pgvector
- **Azure Cache for Redis**
- **Azure Storage + CDN**: Frontend
- **Azure App Gateway**: Load balancer

**Estimated Cost**: $50-100/month

---

## 🔒 Security Checklist Before Deployment

- [ ] Change all default passwords
- [ ] Generate strong `SECRET_KEY` and `ENCRYPTION_KEY`
- [ ] Set `CORS_ALLOWED_ORIGINS` to your frontend domain only
- [ ] Add OpenAI API key
- [ ] Enable HTTPS (most platforms do this automatically)
- [ ] Set `DEBUG=false` in production
- [ ] Configure rate limiting appropriately
- [ ] Review `render.yaml` / deployment config
- [ ] Set up monitoring (Sentry, LogRocket, etc.)
- [ ] Configure backups for database
- [ ] Set up domain name (optional)

---

## 📊 Deployment Comparison

| Platform | Difficulty | Cost (Monthly) | Best For |
|----------|-----------|----------------|----------|
| **Render + Vercel** | ⭐ Easy | Free - $7 | Side projects, demos |
| **Railway** | ⭐ Easy | $5 - $20 | Quick Docker deploy |
| **DigitalOcean** | ⭐⭐ Medium | $12 - $50 | Small production apps |
| **Heroku** | ⭐ Easy | $7 - $50 | Simple apps (deprecated) |
| **AWS/Azure/GCP** | ⭐⭐⭐⭐ Hard | $50 - $500+ | Enterprise production |
| **Self-hosted VPS** | ⭐⭐⭐ Medium | $5 - $40 | Full control needed |

---

## 🚦 Quick Start Recommendation

### For Demo/Portfolio (Free):
1. **Frontend**: Vercel (Free)
2. **Backend**: Render Web Service (Free after trial)
3. **Database**: Render PostgreSQL (Free)
4. **Redis**: Render Redis (Free)

### For Production (Budget):
1. **All Services**: Railway ($5-20/month)
   - Simplest Docker deployment
   - Automatic scaling
   - Built-in monitoring

### For Enterprise:
1. **Infrastructure**: AWS/Azure/GCP
2. **Monitoring**: Datadog/New Relic
3. **Logging**: ELK Stack
4. **CI/CD**: GitHub Actions

---

## 🔧 Post-Deployment

### Test Your Deployment

```bash
# Test backend health
curl https://your-api-url.onrender.com/api/health

# Test frontend
curl https://your-app.vercel.app

# Upload a test resume
# Search for candidates
# Create a job posting
```

### Monitor Performance

- Set up **Sentry** for error tracking
- Use **LogRocket** for user session replay
- Monitor **API response times**
- Track **database query performance**
- Set up **alerts** for downtime

### Enable Analytics

- Google Analytics for frontend
- Mixpanel for user behavior
- PostHog for product analytics

---

## 📝 Environment Variables Reference

### Required for All Platforms:

```bash
# OpenAI (Required)
OPENAI_API_KEY=sk-...

# Security (Generate with openssl/Python)
SECRET_KEY=<random-64-char-hex>
ENCRYPTION_KEY=<base64-fernet-key>

# Database (Platform provides or self-managed)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Redis (Platform provides or self-managed)
REDIS_URL=redis://host:6379/0

# CORS (Your frontend URL)
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app

# Environment
ENVIRONMENT=production
DEBUG=false
```

---

## 🆘 Troubleshooting Deployment Issues

### Backend won't start
- Check `DATABASE_URL` is correct
- Verify `OPENAI_API_KEY` is set
- Check logs: `render logs` or platform dashboard

### Frontend can't reach backend
- Verify `VITE_API_URL` is set correctly
- Check CORS settings in backend
- Ensure backend is accessible publicly

### Database connection failed
- Check PostgreSQL version supports pgvector
- Verify connection string format
- Check firewall rules

### Slow performance
- Enable Redis caching
- Add database indexes
- Use CDN for frontend assets
- Enable gzip compression

---

## 📚 Additional Resources

- [Render Docs](https://render.com/docs)
- [Vercel Docs](https://vercel.com/docs)
- [Railway Docs](https://docs.railway.app)
- [Docker Deployment Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [pgvector Installation](https://github.com/pgvector/pgvector)

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] `.env.example` created (no secrets)
- [ ] Production environment variables prepared
- [ ] OpenAI API key obtained
- [ ] Platform account created (Render/Vercel/Railway)
- [ ] Backend deployed and healthy
- [ ] Database created with pgvector
- [ ] Redis instance running
- [ ] Frontend deployed
- [ ] DNS configured (if custom domain)
- [ ] HTTPS enabled
- [ ] Error monitoring set up
- [ ] Backups configured
- [ ] Load tested
- [ ] Documentation updated

---

**Ready to deploy?** Choose your platform and follow the guide above! 🚀
