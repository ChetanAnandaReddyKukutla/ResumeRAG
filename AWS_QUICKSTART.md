# 🚀 AWS DEPLOYMENT - QUICK REFERENCE

## 📦 **Installation Commands**

```powershell
# Install AWS CLI
Invoke-WebRequest -Uri "https://awscli.amazonaws.com/AWSCLIV2.msi" -Outfile "AWSCLIV2.msi"
Start-Process msiexec.exe -ArgumentList '/i AWSCLIV2.msi /quiet' -Wait

# Install EB CLI
pip install awsebcli --upgrade --user

# Configure AWS
aws configure
# Region: eu-north-1
# Format: json
```

---

## ⚡ **Quick Deploy (3 Commands)**

```powershell
# 1. Navigate to API
cd C:\Users\herok\Documents\ResumeRAG\api

# 2. Initialize (first time only)
eb init

# 3. Create and deploy
eb create resumerag-prod
```

---

## 🔧 **Common Commands**

```powershell
# Deploy updates
eb deploy

# View status
eb status

# View logs
eb logs

# Stream logs (real-time)
eb logs --stream

# Open app in browser
eb open

# SSH into instance
eb ssh

# Set environment variable
eb setenv KEY="value"

# List environments
eb list

# Terminate environment
eb terminate resumerag-prod
```

---

## 🌐 **Your Deployment URLs**

**Backend API:**
```
http://resumerag-prod.[random].eu-north-1.elasticbeanstalk.com
```

**API Documentation:**
```
http://resumerag-prod.[random].eu-north-1.elasticbeanstalk.com/docs
```

**Health Check:**
```
http://resumerag-prod.[random].eu-north-1.elasticbeanstalk.com/api/health
```

---

## 🔐 **Required Environment Variables**

Set these with `eb setenv`:

```bash
DATABASE_URL="postgresql+asyncpg://postgres:PASSWORD@resumerag-db.ct60em0aqkjg.eu-north-1.rds.amazonaws.com:5432/resumerag"
OPENAI_API_KEY="sk-proj-..."
SECRET_KEY="qpFaHJy44NBFPwLlcFc5DNfEHjyT0IyA3lzN1yuOh1o="
PII_ENC_KEY="qpFaHJy44NBFPwLlcFc5DNfEHjyT0IyA3lzN1yuOh1o="
ENVIRONMENT="production"
CORS_ALLOWED_ORIGINS="*"
```

---

## 🔍 **Troubleshooting**

### **Can't connect to database:**
```powershell
# Check RDS is publicly accessible
# Verify Security Group allows 0.0.0.0/0 on port 5432
# Test from local machine first
```

### **Deployment fails:**
```powershell
# View detailed logs
eb logs --all

# Check Docker locally first
cd api
docker build -t test .
docker run -p 8000:8000 test
```

### **App not responding:**
```powershell
# SSH and check container
eb ssh
docker ps
docker logs $(docker ps -q)
```

---

## 💰 **Cost Estimate**

**Free Tier (First 12 months):**
- EC2 t2.micro: FREE (750 hours/month)
- Load Balancer: FREE (750 hours/month)
- **Monthly Cost: $0**

**After Free Tier:**
- EC2 t3.micro: ~$7-10/month
- Application Load Balancer: ~$16-20/month
- **Monthly Cost: ~$25-30/month**

---

## 📱 **Auto-Deploy Setup**

Add to GitHub Secrets (Settings → Secrets → Actions):
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

Push to `main` branch = automatic deployment! 🎉

---

## ✅ **Deployment Checklist**

- [ ] AWS CLI installed (`aws --version`)
- [ ] EB CLI installed (`eb --version`)
- [ ] AWS credentials configured (`aws configure`)
- [ ] RDS publicly accessible
- [ ] RDS Security Group allows inbound
- [ ] pgvector extension installed
- [ ] Docker running
- [ ] Environment created (`eb create`)
- [ ] Environment variables set (`eb setenv`)
- [ ] Health check passes
- [ ] Frontend updated with API URL

---

## 🆘 **Need Help?**

```powershell
# View EB CLI help
eb --help

# View command-specific help
eb deploy --help

# Check AWS console
# https://console.aws.amazon.com/elasticbeanstalk/
```

---

**Ready to deploy?** Run: `.\deploy-aws.ps1`
