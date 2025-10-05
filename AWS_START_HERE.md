# 🎯 AWS DEPLOYMENT - START HERE

## ✅ **Files Created for You:**

1. **AWS_DEPLOYMENT.md** - Complete step-by-step deployment guide
2. **AWS_QUICKSTART.md** - Quick reference card with common commands
3. **deploy-aws.ps1** - Automated deployment script
4. **api/.ebignore** - Files to exclude from deployment
5. **.github/workflows/deploy-aws.yml** - CI/CD pipeline for auto-deployment

---

## 🚀 **Getting Started (Choose One Path)**

### **Option A: Automated Script (Easiest)** ⭐

```powershell
# Just run this!
.\deploy-aws.ps1
```

This script will:
- ✅ Check prerequisites
- ✅ Initialize Elastic Beanstalk
- ✅ Create environment
- ✅ Set environment variables
- ✅ Deploy your app

---

### **Option B: Manual Step-by-Step**

Follow the complete guide in **[AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md)**

Key steps:
1. Install AWS CLI & EB CLI
2. Configure AWS credentials
3. Initialize EB application
4. Create environment
5. Set environment variables
6. Deploy!

---

## 📋 **Before You Start - Prerequisites**

### **1. Install AWS CLI**

Download and install:
```
https://awscli.amazonaws.com/AWSCLIV2.msi
```

Verify:
```powershell
aws --version
```

### **2. Install EB CLI**

```powershell
pip install awsebcli --upgrade --user
```

Verify:
```powershell
eb --version
```

### **3. Get AWS Credentials**

1. Log into AWS Console: https://console.aws.amazon.com/
2. Go to: Your Name → Security credentials
3. Create access key for CLI
4. Save Access Key ID and Secret Access Key

Configure:
```powershell
aws configure
```

### **4. Prepare Your RDS**

Make sure your RDS database is:
- ✅ Publicly accessible
- ✅ Security Group allows inbound on port 5432
- ✅ Has pgvector extension installed

---

## ⚡ **Quick Deploy (3 Commands)**

```powershell
# 1. Navigate to API
cd api

# 2. Initialize EB
eb init

# 3. Create and deploy
eb create resumerag-prod
```

---

## 🔧 **Set Environment Variables**

After creating the environment, set your variables:

```powershell
eb setenv `
  DATABASE_URL="YOUR_RDS_URL" `
  OPENAI_API_KEY="YOUR_API_KEY" `
  SECRET_KEY="YOUR_SECRET" `
  PII_ENC_KEY="YOUR_PII_KEY" `
  ENVIRONMENT="production" `
  CORS_ALLOWED_ORIGINS="*"
```

**Replace placeholders with actual values from your `.env` file!**

---

## 🎯 **After Deployment**

### **Check Status:**
```powershell
eb status
```

### **View Logs:**
```powershell
eb logs
```

### **Test Your API:**
```powershell
$URL = "http://resumerag-prod.xxxxx.eu-north-1.elasticbeanstalk.com"
Invoke-WebRequest -Uri "$URL/api/health"
```

### **Open in Browser:**
```powershell
eb open
```

---

## 🎨 **Deploy Frontend to Vercel**

1. Go to: https://vercel.com/new
2. Import GitHub repo
3. Settings:
   - Framework: Vite
   - Root: `frontend`
   - Build: `npm run build`
   - Output: `dist`
4. Add environment variable:
   ```
   VITE_API_URL=http://your-eb-url.elasticbeanstalk.com
   ```
5. Deploy!

---

## 🔄 **Update Deployment**

When you make code changes:

```powershell
git add .
git commit -m "update"
git push

# Manual deploy
cd api
eb deploy

# OR just push - GitHub Actions will auto-deploy!
```

---

## 💰 **Cost**

**Free Tier (First 12 months):**
- EC2: FREE (750 hours/month)
- Load Balancer: FREE (750 hours/month)
- **Monthly Cost: $0**

**After Free Tier:**
- ~$25-30/month

---

## 📚 **Documentation**

- **Full Guide**: [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md)
- **Quick Reference**: [AWS_QUICKSTART.md](AWS_QUICKSTART.md)
- **AWS EB Docs**: https://docs.aws.amazon.com/elasticbeanstalk/

---

## 🆘 **Need Help?**

### **Common Issues:**

**1. Database connection fails:**
- Check RDS is publicly accessible
- Verify Security Group rules
- Test connection from local machine first

**2. Deployment fails:**
```powershell
eb logs --all
```

**3. App not responding:**
```powershell
eb ssh
docker logs $(docker ps -q)
```

---

## ✅ **Deployment Checklist**

Before deploying, make sure:

- [ ] AWS CLI installed (`aws --version`)
- [ ] EB CLI installed (`eb --version`)  
- [ ] AWS credentials configured (`aws configure`)
- [ ] RDS is publicly accessible
- [ ] RDS Security Group allows port 5432
- [ ] pgvector extension installed in RDS
- [ ] Docker is running
- [ ] All environment variables ready

---

## 🎉 **Ready to Deploy?**

**Option 1 - Automated:**
```powershell
.\deploy-aws.ps1
```

**Option 2 - Manual:**
```powershell
cd api
eb init
eb create resumerag-prod
```

**Option 3 - Read Full Guide:**
Open [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md)

---

**Good luck with your deployment!** 🚀

Your app will be live at:
```
http://resumerag-prod.[random].eu-north-1.elasticbeanstalk.com
```
