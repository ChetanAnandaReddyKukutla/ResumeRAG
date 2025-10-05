# 🚀 AWS DEPLOYMENT GUIDE - Complete Step-by-Step

Deploy your ResumeRAG backend to AWS using **AWS Elastic Beanstalk** (easiest) or **ECS Fargate** (production-grade).

---

## 📋 **Prerequisites**

- ✅ AWS Account (Free Tier eligible)
- ✅ AWS RDS PostgreSQL already set up (you have this!)
- ✅ Docker Desktop running
- ✅ Git installed

---

## 🎯 **Method 1: AWS Elastic Beanstalk (RECOMMENDED - Easiest)**

### **Why Elastic Beanstalk?**
- ✅ Easiest AWS deployment option
- ✅ Handles load balancing, auto-scaling, monitoring
- ✅ Free tier eligible
- ✅ Simple configuration
- ✅ Perfect for Docker containers

---

## 📦 **STEP-BY-STEP: AWS ELASTIC BEANSTALK DEPLOYMENT**

### **Step 1: Install AWS CLI (5 minutes)**

**Option A - Using MSI Installer (Recommended for Windows):**

1. Download AWS CLI:
   - Go to: https://awscli.amazonaws.com/AWSCLIV2.msi
   - Run the installer
   - Click "Next" → "Next" → "Install"
   - Restart PowerShell after installation

2. Verify installation:
   ```powershell
   aws --version
   # Should show: aws-cli/2.x.x Python/3.x.x Windows/...
   ```

**Option B - Using PowerShell:**
```powershell
# Download and install
$progressPreference = 'silentlyContinue'
Invoke-WebRequest -Uri "https://awscli.amazonaws.com/AWSCLIV2.msi" -Outfile "AWSCLIV2.msi"
Start-Process msiexec.exe -ArgumentList '/i AWSCLIV2.msi /quiet' -Wait
Remove-Item AWSCLIV2.msi

# Verify
aws --version
```

---

### **Step 2: Configure AWS Credentials (5 minutes)**

1. **Get AWS Access Keys:**
   - Log into AWS Console: https://console.aws.amazon.com/
   - Click your username (top-right) → **Security credentials**
   - Scroll to **Access keys** → Click **Create access key**
   - Choose **Command Line Interface (CLI)**
   - Check the box "I understand..."
   - Click **Create access key**
   - **IMPORTANT**: Copy both:
     - Access Key ID
     - Secret Access Key
   - Click **Done**

2. **Configure AWS CLI:**
   ```powershell
   aws configure
   ```
   
   Enter when prompted:
   ```
   AWS Access Key ID: [paste your access key]
   AWS Secret Access Key: [paste your secret key]
   Default region name: eu-north-1
   Default output format: json
   ```

3. **Test configuration:**
   ```powershell
   aws sts get-caller-identity
   # Should show your AWS account info
   ```

---

### **Step 3: Install EB CLI (3 minutes)**

```powershell
# Install EB CLI using pip
pip install awsebcli --upgrade --user

# Verify installation
eb --version
# Should show: EB CLI 3.x.x (Python 3.x.x)
```

If `eb` command not found, add to PATH:
```powershell
$env:Path += ";$env:USERPROFILE\AppData\Roaming\Python\Python313\Scripts"
```

---

### **Step 4: Prepare Your RDS Database (5 minutes)**

1. **Make RDS Publicly Accessible:**
   - Go to AWS RDS Console: https://console.aws.amazon.com/rds/
   - Region: **eu-north-1 (Stockholm)**
   - Click **Databases** → Click your database **"resumerag-db"**
   - Click **Modify**
   - Scroll to **Connectivity** → **Public access** → Select **Yes**
   - Scroll down → Click **Continue**
   - Select **Apply immediately**
   - Click **Modify DB instance**

2. **Update Security Group:**
   - On database page, scroll to **Connectivity & security**
   - Click the **VPC security group** link (sg-xxxxx)
   - Click **Inbound rules** tab
   - Click **Edit inbound rules**
   - Click **Add rule**:
     - Type: **PostgreSQL**
     - Source: **Anywhere-IPv4** (0.0.0.0/0)
     - Description: **Allow EB access**
   - Click **Save rules**

3. **Install pgvector Extension:**
   - You need a PostgreSQL client (pgAdmin, DBeaver, or psql)
   - Connect to your RDS:
     ```
     Host: resumerag-db.ct60em0aqkjg.eu-north-1.rds.amazonaws.com
     Port: 5432
     Database: resumerag
     Username: postgres
     Password: M6THe<po6SG]RsS2V5MhC$n6A9TJ
     ```
   - Run this SQL:
     ```sql
     CREATE EXTENSION IF NOT EXISTS vector;
     ```

---

### **Step 5: Create Elastic Beanstalk Application (10 minutes)**

1. **Navigate to your API directory:**
   ```powershell
   cd C:\Users\herok\Documents\ResumeRAG\api
   ```

2. **Initialize Elastic Beanstalk:**
   ```powershell
   eb init
   ```
   
   Answer the prompts:
   ```
   Select a default region: 10 (eu-north-1 : EU (Stockholm))
   Enter Application Name: resumerag-api
   It appears you are using Docker. Is this correct? Y
   Select a platform branch: Docker running on 64bit Amazon Linux 2023
   Do you wish to continue with CodeCommit? n
   Do you want to set up SSH for your instances? n
   ```

3. **Create Environment:**
   ```powershell
   eb create resumerag-prod
   ```
   
   This will:
   - Create EC2 instances
   - Set up Load Balancer
   - Configure Auto Scaling
   - Deploy your Docker container
   
   **Wait 5-10 minutes** for environment creation.

---

### **Step 6: Configure Environment Variables (5 minutes)**

1. **Set all environment variables:**
   ```powershell
   eb setenv `
     DATABASE_URL="postgresql+asyncpg://postgres:YOUR_PASSWORD@resumerag-db.ct60em0aqkjg.eu-north-1.rds.amazonaws.com:5432/resumerag" `
     REDIS_URL="redis://localhost:6379/0" `
     OPENAI_API_KEY="YOUR_OPENAI_API_KEY" `
     SECRET_KEY="YOUR_SECRET_KEY" `
     PII_ENC_KEY="YOUR_PII_ENC_KEY" `
     ALGORITHM="HS256" `
     ENVIRONMENT="production" `
     CORS_ALLOWED_ORIGINS="*" `
     PGVECTOR_DIM="1536" `
     USE_WORKER="false" `
     ACCESS_TOKEN_EXPIRE_MINUTES="30" `
     REFRESH_TOKEN_EXPIRE_DAYS="7" `
     MAX_FAILED_ATTEMPTS="5" `
     LOCKOUT_DURATION_MINUTES="15" `
     RATE_LIMIT_REQUESTS="60" `
     RATE_LIMIT_WINDOW="60" `
     MAX_UPLOAD_SIZE_MB="10" `
     MAX_FILE_SIZE="10485760" `
     ALLOWED_EXTENSIONS="pdf,docx,txt,zip"
   ```

2. **Wait for update to complete** (2-3 minutes)

---

### **Step 7: Test Your Deployment**

1. **Get your application URL:**
   ```powershell
   eb status
   ```
   
   Look for: `CNAME: resumerag-prod.xxxxxxxxxx.eu-north-1.elasticbeanstalk.com`

2. **Test the API:**
   ```powershell
   $URL = "http://resumerag-prod.xxxxxxxxxx.eu-north-1.elasticbeanstalk.com"
   Invoke-WebRequest -Uri "$URL/api/health"
   ```
   
   Should return: `{"status":"ok","time":"..."}`

3. **Check API docs:**
   Open in browser: `http://resumerag-prod.xxxxxxxxxx.eu-north-1.elasticbeanstalk.com/docs`

---

### **Step 8: View Logs (If Issues Occur)**

```powershell
# View recent logs
eb logs

# Stream logs in real-time
eb logs --stream
```

---

### **Step 9: Deploy Updates**

When you make code changes:

```powershell
cd C:\Users\herok\Documents\ResumeRAG\api
git add .
git commit -m "update"
eb deploy
```

---

## 🎨 **DEPLOY FRONTEND TO VERCEL**

1. **Go to Vercel:**
   - https://vercel.com/new
   - Import your GitHub repo

2. **Configure:**
   ```
   Framework: Vite
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: dist
   ```

3. **Environment Variable:**
   ```
   VITE_API_URL=http://resumerag-prod.xxxxxxxxxx.eu-north-1.elasticbeanstalk.com
   ```

4. **Deploy!**

5. **Update CORS:**
   ```powershell
   cd C:\Users\herok\Documents\ResumeRAG\api
   eb setenv CORS_ALLOWED_ORIGINS="https://your-app.vercel.app"
   ```

---

## 💰 **COST ESTIMATE**

### **Elastic Beanstalk Free Tier:**
- ✅ 750 hours/month EC2 (t2.micro/t3.micro)
- ✅ 750 hours/month Load Balancer
- ✅ RDS: Already using (paid or free tier)
- **Total: $0/month for first year** (if within free tier)

### **After Free Tier:**
- EC2 t3.micro: ~$7-10/month
- Application Load Balancer: ~$16-20/month
- RDS db.t3.micro: ~$15-25/month
- **Total: ~$40-55/month**

---

## 🔄 **CI/CD: Auto-Deploy from GitHub**

Create `.github/workflows/deploy-aws.yml`:

```yaml
name: Deploy to AWS Elastic Beanstalk

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: eu-north-1
      
      - name: Install EB CLI
        run: |
          pip install awsebcli
      
      - name: Deploy to EB
        working-directory: ./api
        run: |
          eb deploy resumerag-prod
```

Add secrets in GitHub: Settings → Secrets → Actions

---

## 🆘 **TROUBLESHOOTING**

### **Problem: Environment won't start**
```powershell
eb logs
# Check for database connection errors
```

### **Problem: Can't connect to RDS**
- Verify RDS is publicly accessible
- Check Security Group allows inbound on port 5432
- Test connection from local machine first

### **Problem: Health check failing**
- Ensure app binds to `0.0.0.0:8000` (not `127.0.0.1`)
- Check Dockerfile CMD/ENTRYPOINT
- Verify `/api/health` endpoint works

### **Problem: Container won't start**
```powershell
eb ssh  # SSH into instance
docker logs $(docker ps -q)  # View container logs
```

---

## 🎯 **Quick Commands Reference**

```powershell
# View environment status
eb status

# View logs
eb logs

# Stream logs
eb logs --stream

# Deploy updates
eb deploy

# Open app in browser
eb open

# SSH into instance
eb ssh

# Terminate environment (careful!)
eb terminate resumerag-prod
```

---

## ✅ **SUCCESS CHECKLIST**

- [ ] AWS CLI installed and configured
- [ ] EB CLI installed
- [ ] RDS publicly accessible
- [ ] RDS Security Group allows inbound
- [ ] pgvector extension installed
- [ ] EB application created
- [ ] Environment variables set
- [ ] Application accessible at EB URL
- [ ] `/api/health` returns 200
- [ ] Frontend deployed to Vercel
- [ ] CORS configured

---

**You're now running on AWS!** 🎉

Your backend is deployed on AWS Elastic Beanstalk with auto-scaling, load balancing, and monitoring built-in!
