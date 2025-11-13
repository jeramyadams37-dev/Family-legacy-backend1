#!/bin/bash

################################################################################
# Family Hub - Automated Setup Script
################################################################################
#
# This script automates the installation and setup of Family Hub.
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
#
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         Family Hub - Automated Setup Script               ║"
echo "║         Version 1.0.0 - November 4, 2025                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to print status messages
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running on supported OS
echo "Checking system compatibility..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    print_status "Running on Linux"
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    print_status "Running on macOS"
    OS="mac"
else
    print_error "Unsupported operating system: $OSTYPE"
    print_warning "This script supports Linux and macOS only."
    exit 1
fi

# Check Python version
echo ""
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_status "Python $PYTHON_VERSION found"
    
    # Check if version is 3.11+
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
        print_status "Python version is compatible (3.11+)"
    else
        print_warning "Python 3.11+ is recommended. You have $PYTHON_VERSION"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    print_error "Python 3 not found. Please install Python 3.11+ first."
    echo "Visit: https://www.python.org/downloads/"
    exit 1
fi

# Check PostgreSQL
echo ""
echo "Checking PostgreSQL installation..."
if command -v psql &> /dev/null; then
    PG_VERSION=$(psql --version | cut -d' ' -f3)
    print_status "PostgreSQL $PG_VERSION found"
else
    print_warning "PostgreSQL not found locally."
    print_warning "You'll need to configure a remote database or install PostgreSQL."
    echo "Visit: https://www.postgresql.org/download/"
fi

# Create virtual environment
echo ""
echo "Setting up Python virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    print_status "Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
print_status "Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet
print_status "pip upgraded to latest version"

# Install dependencies
echo ""
echo "Installing Python dependencies..."
echo "This may take a few minutes..."

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    print_status "All dependencies installed successfully"
else
    print_error "requirements.txt not found!"
    
    # Create requirements.txt from pyproject.toml if it exists
    if [ -f "pyproject.toml" ]; then
        print_warning "Creating requirements.txt from pyproject.toml..."
        cat > requirements.txt << EOF
flask>=3.0.0
gunicorn>=23.0.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
flask-login>=0.6.0
flask-dance>=7.0.0
openai>=1.0.0
werkzeug>=3.0.0
cryptography>=42.0.0
pyjwt>=2.0.0
requests>=2.31.0
EOF
        pip install -r requirements.txt --quiet
        print_status "Dependencies installed from generated requirements.txt"
    else
        print_error "No dependency file found. Cannot continue."
        exit 1
    fi
fi

# Create necessary directories
echo ""
echo "Creating directory structure..."
mkdir -p static/uploads
mkdir -p logs
mkdir -p backups
print_status "Directories created"

# Setup environment variables
echo ""
echo "Setting up environment variables..."
if [ -f ".env" ]; then
    print_warning ".env file already exists. Skipping creation."
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_status ".env file created from .env.example"
    else
        # Create .env from scratch
        cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://family_hub_user:changeme@localhost/family_hub

# Flask Configuration
FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
FLASK_ENV=production

# OpenAI (for AI Harmony)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Domain
DOMAIN=http://localhost:5000
EOF
        print_status ".env file created with defaults"
    fi
    
    print_warning "IMPORTANT: Edit .env file with your actual configuration!"
    print_warning "  - Set DATABASE_URL to your PostgreSQL connection"
    print_warning "  - Set OPENAI_API_KEY if using AI features"
    print_warning "  - Configure email settings if needed"
fi

# Database setup
echo ""
echo "Database setup..."
print_warning "Make sure PostgreSQL is running and you have created the database."
echo ""
read -p "Do you want to initialize the database now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating database tables..."
    python3 << PYEOF
import sys
sys.path.insert(0, '.')
try:
    from app import app, db
    with app.app_context():
        db.create_all()
    print("✓ Database tables created successfully")
except Exception as e:
    print(f"✗ Error creating tables: {e}")
    print("  You may need to configure DATABASE_URL in .env first")
    sys.exit(1)
PYEOF
    
    if [ $? -eq 0 ]; then
        print_status "Database initialized"
        
        # Ask about sample data
        echo ""
        read -p "Do you want to import sample Adams family data? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if [ -f "docs/database/safe_production_import.sql" ]; then
                # Extract database URL components
                source .env
                echo "Importing sample data..."
                psql "$DATABASE_URL" < docs/database/safe_production_import.sql
                print_status "Sample data imported"
            else
                print_warning "Sample data file not found. Skipping."
            fi
        fi
    else
        print_error "Database initialization failed"
        print_warning "You'll need to set up the database manually"
    fi
else
    print_warning "Skipping database initialization"
    print_warning "Run 'python main.py' later to create tables"
fi

# Create run script
echo ""
echo "Creating convenience scripts..."
cat > run_dev.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
export FLASK_DEBUG=1
python main.py
EOF
chmod +x run_dev.sh
print_status "Created run_dev.sh (development server)"

cat > run_prod.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
gunicorn --bind=0.0.0.0:5000 --reuse-port --workers=4 main:app
EOF
chmod +x run_prod.sh
print_status "Created run_prod.sh (production server)"

# Summary
echo ""
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                Setup Complete!                             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your configuration:"
echo -e "   ${YELLOW}nano .env${NC}"
echo ""
echo "2. Start the application:"
echo -e "   ${GREEN}./run_dev.sh${NC}    (development mode)"
echo -e "   ${GREEN}./run_prod.sh${NC}   (production mode)"
echo ""
echo "3. Open your browser:"
echo -e "   ${GREEN}http://localhost:5000${NC}"
echo ""
echo "For detailed documentation, see:"
echo "  - INSTALLATION.md (complete installation guide)"
echo "  - docs/ (full documentation suite)"
echo ""
echo -e "${GREEN}Happy family connecting! 🎉${NC}"
echo ""
