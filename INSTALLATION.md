# Family Hub - Installation Guide

**Complete setup guide for deploying Family Hub on any platform**

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Installation Steps](#detailed-installation-steps)
4. [Configuration](#configuration)
5. [Database Setup](#database-setup)
6. [Running the Application](#running-the-application)
7. [Deployment Options](#deployment-options)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Python 3.11+** - [Download here](https://www.python.org/downloads/)
- **PostgreSQL 12+** - [Download here](https://www.postgresql.org/download/)
- **Git** (optional) - [Download here](https://git-scm.com/downloads/)

### Optional Tools

- **uv** (fast Python package installer) - `pip install uv`
- **virtualenv** - For isolated Python environments

---

## Quick Start

### Option 1: Automatic Setup (Recommended)

```bash
# 1. Extract the zip file
unzip family-hub.zip
cd family-hub

# 2. Run the setup script
chmod +x setup.sh
./setup.sh

# 3. Configure environment variables
cp .env.example .env
# Edit .env with your settings

# 4. Start the application
source venv/bin/activate  # On Windows: venv\Scripts\activate
gunicorn --bind=0.0.0.0:5000 --reuse-port main:app
```

### Option 2: Manual Setup

See [Detailed Installation Steps](#detailed-installation-steps) below.

---

## Detailed Installation Steps

### Step 1: Extract Files

```bash
# Extract the downloaded zip file
unzip family-hub.zip
cd family-hub

# Verify files are present
ls -la
```

You should see:
- `main.py`, `app.py`, `routes.py` (Python files)
- `templates/` (HTML templates)
- `static/` (CSS, JS, uploads)
- `docs/` (Documentation)
- `requirements.txt` (Python dependencies)

---

### Step 2: Create Virtual Environment

**On Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

---

### Step 3: Install Python Dependencies

**Using pip:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Using uv (faster):**
```bash
pip install uv
uv pip install -r requirements.txt
```

**Dependencies installed:**
- Flask 3.0+
- SQLAlchemy 2.0+
- Gunicorn
- psycopg2-binary
- OpenAI
- Flask-Login
- Flask-Dance
- And more...

---

### Step 4: Setup PostgreSQL Database

#### Create Database

```bash
# Open PostgreSQL terminal
psql -U postgres

# In PostgreSQL:
CREATE DATABASE family_hub;
CREATE USER family_hub_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE family_hub TO family_hub_user;
\q
```

#### Alternative: Use existing PostgreSQL service

If using a cloud PostgreSQL service (Heroku, Neon, Railway, etc.):
1. Copy the connection URL from your provider
2. Use it in the next step

---

### Step 5: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit with your favorite editor
nano .env  # or vim, code, etc.
```

**Required variables in `.env`:**

```bash
# Database
DATABASE_URL=postgresql://family_hub_user:your_secure_password@localhost/family_hub

# Flask
FLASK_SECRET_KEY=your-very-long-random-secret-key-here
FLASK_ENV=production

# OpenAI (for AI Harmony feature)
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1

# Email (optional - for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Domain (for OAuth callbacks)
DOMAIN=http://localhost:5000
# Or production: https://yourdomain.com
```

**Generate a secure Flask secret key:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

### Step 6: Initialize Database

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run the application once to create tables
python main.py
# Press Ctrl+C after you see "Running on http://0.0.0.0:5000"
```

This automatically creates all database tables.

#### Import Sample Data (Optional)

If you want the Adams family sample data:

```bash
# Import the provided data
psql -U family_hub_user -d family_hub < docs/database/safe_production_import.sql
```

---

### Step 7: Test the Installation

```bash
# Start the development server
python main.py

# Or use Gunicorn (production)
gunicorn --bind=0.0.0.0:5000 --reuse-port main:app
```

**Open your browser:**
- Navigate to: `http://localhost:5000`
- You should see the Family Hub landing page

**Test features:**
1. Click "Login" - OAuth should redirect properly
2. Create a family
3. Add profile information
4. Test messaging, calendar, etc.

---

## Configuration

### OAuth Authentication Setup

Family Hub uses OAuth for authentication. You need to configure providers:

#### Option 1: Use Replit Auth (Easiest)

If deploying on Replit, authentication is pre-configured. No additional setup needed.

#### Option 2: Configure Your Own OAuth

For deployment elsewhere, you need to set up OAuth apps:

**Google OAuth:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google+ API
4. Create OAuth credentials
5. Add redirect URI: `https://yourdomain.com/auth/google/callback`
6. Copy Client ID and Secret to `.env`

**GitHub OAuth:**
1. Go to [GitHub Settings](https://github.com/settings/developers)
2. Create new OAuth App
3. Set Authorization callback URL: `https://yourdomain.com/auth/github/callback`
4. Copy Client ID and Secret to `.env`

**Update `.env`:**
```bash
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
GITHUB_OAUTH_CLIENT_ID=your-client-id
GITHUB_OAUTH_CLIENT_SECRET=your-client-secret
```

**Update `replit_auth.py`:**
Replace Replit Auth blueprint with Flask-Dance blueprints for Google/GitHub.

---

### Email Configuration

For email notifications (optional):

**Gmail:**
1. Enable 2-factor authentication
2. Generate an App Password
3. Use in `.env`:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youremail@gmail.com
SMTP_PASSWORD=your-app-password
```

**SendGrid:**
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

---

### AI Harmony Configuration

For the AI assistant feature:

1. Get OpenAI API key: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Add to `.env`:
```bash
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
```

**Optional:** Use alternative AI providers:
- Anthropic Claude
- Azure OpenAI
- Local LLM (Ollama, LM Studio)

Update `ai_helper.py` to use different providers.

---

## Database Setup

### Production Database Recommendations

**Cloud PostgreSQL Services:**

1. **Neon** (Recommended for Replit)
   - Free tier available
   - Auto-scaling
   - Setup: [https://neon.tech](https://neon.tech)

2. **Railway**
   - Easy deployment
   - PostgreSQL included
   - Setup: [https://railway.app](https://railway.app)

3. **Heroku Postgres**
   - Reliable and mature
   - Easy integration
   - Setup: [https://www.heroku.com/postgres](https://www.heroku.com/postgres)

4. **Supabase**
   - Free tier
   - Additional features (auth, storage)
   - Setup: [https://supabase.com](https://supabase.com)

### Database Backups

**Backup command:**
```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

**Restore command:**
```bash
psql $DATABASE_URL < backup_20251104.sql
```

**Automated backups:**
```bash
# Add to crontab (daily backup at 2 AM)
0 2 * * * pg_dump $DATABASE_URL > /backups/family_hub_$(date +\%Y\%m\%d).sql
```

---

## Running the Application

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Run Flask development server
python main.py

# Or with debug mode
FLASK_DEBUG=1 python main.py
```

**Features:**
- Auto-reload on code changes
- Detailed error messages
- Debug toolbar

**Warning:** Never use development mode in production!

---

### Production Mode

**Using Gunicorn (Recommended):**

```bash
# Single worker
gunicorn --bind=0.0.0.0:5000 --reuse-port main:app

# Multiple workers (better performance)
gunicorn --bind=0.0.0.0:5000 --reuse-port --workers=4 --threads=2 main:app

# With logging
gunicorn --bind=0.0.0.0:5000 --reuse-port --workers=4 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  main:app
```

**Worker calculation:**
```
workers = (2 * CPU_cores) + 1
```

**Using systemd (Linux):**

Create `/etc/systemd/system/family-hub.service`:

```ini
[Unit]
Description=Family Hub Web Application
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/family-hub
Environment="PATH=/path/to/family-hub/venv/bin"
ExecStart=/path/to/family-hub/venv/bin/gunicorn --bind=0.0.0.0:5000 --workers=4 main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable family-hub
sudo systemctl start family-hub
sudo systemctl status family-hub
```

---

## Deployment Options

### Option 1: Replit Deployments

1. Upload files to Replit
2. Configure integrations (Auth, Database, AI)
3. Click "Deploy"
4. Add custom domain (optional)

**Pros:** Easiest, managed services  
**Cons:** Costs for production features

---

### Option 2: Heroku

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login

# Create app
heroku create family-hub-app

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set FLASK_SECRET_KEY=your-secret-key
heroku config:set OPENAI_API_KEY=your-openai-key

# Deploy
git push heroku main

# Run database migrations
heroku run python main.py

# Open app
heroku open
```

---

### Option 3: Railway

1. Go to [railway.app](https://railway.app)
2. Create new project from GitHub
3. Add PostgreSQL database
4. Set environment variables
5. Deploy automatically

---

### Option 4: DigitalOcean / VPS

```bash
# SSH into server
ssh root@your-server-ip

# Install dependencies
apt update
apt install python3 python3-pip postgresql nginx

# Clone or upload code
cd /var/www
git clone your-repo.git family-hub

# Follow installation steps above
cd family-hub
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure Nginx reverse proxy
# (See Nginx configuration in docs)

# Setup systemd service
# (See systemd configuration above)
```

---

### Option 5: Docker (Advanced)

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind=0.0.0.0:5000", "--workers=4", "main:app"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/family_hub
      - FLASK_SECRET_KEY=${FLASK_SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=family_hub
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Run:
```bash
docker-compose up -d
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Error

**Error:** `psycopg2.OperationalError: could not connect to server`

**Solution:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify DATABASE_URL in .env
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL
```

---

#### 2. Import Error: Module Not Found

**Error:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

---

#### 3. OAuth Redirect Mismatch

**Error:** `redirect_uri_mismatch`

**Solution:**
- Check OAuth app settings
- Ensure redirect URI matches exactly: `https://yourdomain.com/auth/provider/callback`
- No trailing slashes
- Use HTTPS in production

---

#### 4. Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>

# Or use different port
gunicorn --bind=0.0.0.0:8000 main:app
```

---

#### 5. Static Files Not Loading

**Error:** 404 on CSS/JS files

**Solution:**
```python
# In app.py, ensure static folder is configured
app = Flask(__name__, static_folder='static', static_url_path='/static')
```

---

#### 6. Database Tables Not Created

**Error:** `relation "users" does not exist`

**Solution:**
```bash
# Run Python shell
python

# Create tables
>>> from app import app, db
>>> app.app_context().push()
>>> db.create_all()
>>> exit()
```

---

### Getting Help

**Documentation:**
- See `docs/` folder for complete documentation
- `docs/deployment/DEPLOYMENT_GUIDE.md` for deployment help
- `docs/architecture/SYSTEM_ARCHITECTURE.md` for technical details

**Logs:**
```bash
# View application logs
tail -f logs/error.log

# View Gunicorn logs
journalctl -u family-hub -f
```

**Community:**
- GitHub Issues (if applicable)
- Stack Overflow: Tag `flask` and `sqlalchemy`

---

## Security Checklist

Before going to production:

- [ ] Change `FLASK_SECRET_KEY` to a strong random value
- [ ] Use HTTPS (SSL certificate)
- [ ] Set `FLASK_ENV=production`
- [ ] Disable debug mode
- [ ] Use strong database passwords
- [ ] Keep `OPENAI_API_KEY` secret
- [ ] Set up database backups
- [ ] Configure firewall rules
- [ ] Enable CSRF protection
- [ ] Validate all user inputs
- [ ] Update dependencies regularly

---

## Performance Optimization

### Production Settings

```bash
# In .env
FLASK_ENV=production
FLASK_DEBUG=False

# Gunicorn with optimal workers
gunicorn --bind=0.0.0.0:5000 \
  --workers=4 \
  --threads=2 \
  --worker-class=sync \
  --max-requests=1000 \
  --max-requests-jitter=50 \
  --timeout=30 \
  main:app
```

### Database Optimization

```sql
-- Add indexes for performance
CREATE INDEX idx_users_family_id ON users(family_id);
CREATE INDEX idx_messages_receiver ON messages(receiver_id);
CREATE INDEX idx_events_date ON events(event_date);
```

### Caching (Optional)

Install Redis:
```bash
pip install redis flask-caching
```

Configure in `app.py`:
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': 'redis://localhost:6379/0'})
```

---

## Monitoring

### Application Monitoring

**Sentry** (error tracking):
```bash
pip install sentry-sdk[flask]
```

```python
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

**Log Management:**
```bash
# Create log directory
mkdir logs

# Configure in app.py
import logging
logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
```

---

## Next Steps

After successful installation:

1. **Customize:** Edit templates, colors, branding
2. **Configure:** Set up OAuth, email, AI features
3. **Test:** Thoroughly test all features
4. **Deploy:** Choose a deployment platform
5. **Monitor:** Set up logging and monitoring
6. **Backup:** Configure automated backups
7. **Maintain:** Keep dependencies updated

---

## Support

For additional help:
- See complete documentation in `docs/` folder
- Review `docs/agent-notes/SESSION_HISTORY.md` for development insights
- Check `docs/troubleshooting/` for common issues

---

**Installation Guide Version:** 1.0  
**Last Updated:** November 4, 2025  
**Compatible With:** Family Hub v1.0.0
