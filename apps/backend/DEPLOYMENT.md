# Deployment Guide

This guide covers deploying the WAVY.ai backend to various platforms.

## Table of Contents
1. [Railway](#railway-recommended)
2. [Render](#render)
3. [Fly.io](#flyio)
4. [AWS EC2](#aws-ec2)
5. [Google Cloud Run](#google-cloud-run)
6. [Heroku](#heroku)

---

## Railway (Recommended)

**Best for:** Quick deployment with database included

### Steps:

1. **Install Railway CLI:**
```bash
npm install -g @railway/cli
# or
curl -fsSL https://railway.app/install.sh | sh
```

2. **Login and initialize:**
```bash
railway login
cd wavy-backend
railway init
```

3. **Add PostgreSQL database:**
```bash
railway add --plugin postgresql
```

4. **Set environment variables:**
```bash
railway variables set OPENAI_API_KEY=your_key_here
railway variables set ALLOWED_ORIGINS=https://your-frontend.com
railway variables set LLM_PROVIDER=openai
railway variables set DEBUG=False
```

5. **Deploy:**
```bash
railway up
```

6. **Get your URL:**
```bash
railway domain
```

### Cost: ~$5/month for starter plan

---

## Render

**Best for:** Simple deployment with free tier

### Steps:

1. **Connect GitHub:** Push code to GitHub

2. **Create Web Service:**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your repository
   
3. **Configure:**
   - **Name:** wavy-backend
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables:**
   ```
   OPENAI_API_KEY=your_key
   DATABASE_URL=your_postgres_url
   ALLOWED_ORIGINS=https://your-frontend.com
   DEBUG=False
   ```

5. **Add PostgreSQL:**
   - Create new PostgreSQL instance
   - Copy connection string to DATABASE_URL

### Cost: Free tier available, paid starts at $7/month

---

## Fly.io

**Best for:** Global edge deployment

### Steps:

1. **Install Fly CLI:**
```bash
curl -L https://fly.io/install.sh | sh
```

2. **Login and launch:**
```bash
fly auth login
cd wavy-backend
fly launch
```

3. **Configure fly.toml:** (generated automatically)
```toml
app = "wavy-backend"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8080"

[[services]]
  http_checks = []
  internal_port = 8080
  protocol = "tcp"

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
```

4. **Add PostgreSQL:**
```bash
fly postgres create
fly postgres attach --app wavy-backend
```

5. **Set secrets:**
```bash
fly secrets set OPENAI_API_KEY=your_key
fly secrets set ALLOWED_ORIGINS=https://your-frontend.com
fly secrets set DEBUG=False
```

6. **Deploy:**
```bash
fly deploy
```

### Cost: Free tier with $5 credit, then pay-as-you-go

---

## AWS EC2

**Best for:** Full control and scalability

### Steps:

1. **Launch EC2 Instance:**
   - AMI: Ubuntu 22.04 LTS
   - Instance type: t3.small (minimum)
   - Security group: Allow ports 22, 80, 443, 8080

2. **Connect and setup:**
```bash
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.11 python3.11-venv nginx -y

# Clone your repository
git clone your-repo-url
cd wavy-backend
```

3. **Setup application:**
```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
nano .env
# Add your configuration
```

4. **Setup systemd service:**
```bash
sudo nano /etc/systemd/system/wavy-backend.service
```

Add:
```ini
[Unit]
Description=WAVY.ai Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/wavy-backend
Environment="PATH=/home/ubuntu/wavy-backend/venv/bin"
EnvironmentFile=/home/ubuntu/wavy-backend/.env
ExecStart=/home/ubuntu/wavy-backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8080

[Install]
WantedBy=multi-user.target
```

5. **Start service:**
```bash
sudo systemctl enable wavy-backend
sudo systemctl start wavy-backend
```

6. **Setup Nginx reverse proxy:**
```bash
sudo nano /etc/nginx/sites-available/wavy-backend
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/wavy-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Cost: ~$15-30/month for t3.small

---

## Google Cloud Run

**Best for:** Serverless, auto-scaling

### Steps:

1. **Install gcloud CLI:**
```bash
curl https://sdk.cloud.google.com | bash
gcloud init
```

2. **Build and push container:**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/wavy-backend
```

3. **Deploy:**
```bash
gcloud run deploy wavy-backend \
  --image gcr.io/PROJECT_ID/wavy-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=your_key,DEBUG=False
```

4. **Add Cloud SQL (PostgreSQL):**
```bash
gcloud sql instances create wavy-db --tier=db-f1-micro --region=us-central1
gcloud sql databases create wavy_nutrition --instance=wavy-db
```

5. **Connect to database:**
```bash
gcloud run services update wavy-backend \
  --add-cloudsql-instances PROJECT_ID:us-central1:wavy-db \
  --set-env-vars DATABASE_URL=postgresql://...
```

### Cost: Pay per request, typically $5-20/month for small apps

---

## Heroku

**Best for:** Traditional PaaS, easy deployment

### Steps:

1. **Install Heroku CLI:**
```bash
curl https://cli-assets.heroku.com/install.sh | sh
heroku login
```

2. **Create app:**
```bash
cd wavy-backend
heroku create wavy-backend
```

3. **Add PostgreSQL:**
```bash
heroku addons:create heroku-postgresql:mini
```

4. **Create Procfile:**
```bash
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile
```

5. **Set environment variables:**
```bash
heroku config:set OPENAI_API_KEY=your_key
heroku config:set ALLOWED_ORIGINS=https://your-frontend.com
heroku config:set DEBUG=False
```

6. **Deploy:**
```bash
git push heroku main
```

### Cost: $7/month for Eco dynos + $5/month for mini PostgreSQL

---

## Environment Variables Checklist

For all platforms, ensure these are set:

**Required:**
- ✅ `OPENAI_API_KEY` - Your OpenAI API key
- ✅ `DATABASE_URL` - PostgreSQL connection string
- ✅ `ALLOWED_ORIGINS` - Frontend URLs (comma-separated)
- ✅ `SESSION_SECRET` - Random secret key for sessions

**Recommended:**
- ✅ `DEBUG` - Set to `False` in production
- ✅ `LLM_PROVIDER` - `openai` or `azure`
- ✅ `MAX_TOKENS` - Default: 2000
- ✅ `TEMPERATURE` - Default: 0.7

**Optional:**
- `REDIS_URL` - For caching
- `PORT` - Usually auto-set by platform
- `HOST` - Usually `0.0.0.0`

---

## Post-Deployment

### 1. Test the API
```bash
curl https://your-backend-url.com/health
```

### 2. Update frontend
Update `apps/frontend/.env.local`:
```
VITE_API_BASE_URL=https://your-backend-url.com/api
```

### 3. Monitor
- Check logs regularly
- Set up error tracking (Sentry)
- Monitor API usage and costs
- Set up uptime monitoring

### 4. Security
- Enable HTTPS (most platforms do this automatically)
- Rotate API keys regularly
- Set up rate limiting
- Enable CORS only for your frontend domain
- Use secrets manager for sensitive data

---

## Troubleshooting

**Issue: CORS errors**
- Check `ALLOWED_ORIGINS` includes your frontend URL
- Ensure no trailing slashes in URLs

**Issue: Database connection errors**
- Verify `DATABASE_URL` format
- Check database is running and accessible
- For Cloud SQL, ensure proper IAM permissions

**Issue: High latency**
- Use same region for frontend and backend
- Enable Redis caching
- Consider using CDN

**Issue: OpenAI API errors**
- Verify API key is valid
- Check billing/quota on OpenAI dashboard
- Implement fallback to rule-based generation

---

## Scaling Considerations

### For 100+ users:
- Use managed PostgreSQL (not SQLite)
- Add Redis for caching
- Enable connection pooling
- Consider read replicas

### For 1000+ users:
- Use load balancer
- Deploy multiple instances
- Add CDN for static content
- Implement request queuing
- Monitor and optimize database queries

### For 10,000+ users:
- Use microservices architecture
- Separate LLM service
- Implement caching layers
- Use message queue (RabbitMQ, Kafka)
- Auto-scaling based on load

---

## Cost Optimization

1. **Use rule-based generation by default**
   - Only use LLM when explicitly requested
   - Cache LLM responses

2. **Optimize database queries**
   - Add proper indexes
   - Use connection pooling
   - Implement query caching

3. **Choose right instance size**
   - Start small and scale up
   - Use auto-scaling
   - Monitor resource usage

4. **Reduce API calls**
   - Batch OpenAI requests
   - Cache common responses
   - Implement rate limiting

---

## Support

For deployment issues:
- Check platform-specific documentation
- Review application logs
- Test locally with production environment variables
- Contact platform support

Happy deploying! 🚀
