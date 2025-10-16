#!/bin/bash

# Purposeful Live Coaching - Environment Setup Script
# This script sets up the development/production environment

set -e

echo "=========================================="
echo "Purposeful Live Coaching - Setup Script"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
    echo -e "${GREEN}✓ Python 3.11 found${NC}"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if (( $(echo "$PYTHON_VERSION >= 3.11" | bc -l) )); then
        PYTHON_CMD=python3
        echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
    else
        echo -e "${RED}✗ Python 3.11+ required, found $PYTHON_VERSION${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Python not found${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install requirements
echo -e "${YELLOW}Installing Python dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}✗ requirements.txt not found${NC}"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created${NC}"
        echo -e "${YELLOW}⚠ Please edit .env file with your API credentials${NC}"
    else
        echo -e "${RED}✗ .env.example not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Check database configuration
echo -e "${YELLOW}Checking database configuration...${NC}"
if grep -q "DATABASE_URL=sqlite" .env; then
    echo -e "${GREEN}✓ Using SQLite database${NC}"
    
    # Check if database file exists
    if [ -f "instance/purposeful.db" ]; then
        echo -e "${GREEN}✓ Database file exists${NC}"
    else
        echo -e "${YELLOW}Database file will be created on first run${NC}"
    fi
else
    echo -e "${YELLOW}Using external database (PostgreSQL)${NC}"
fi

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p instance
mkdir -p logs
mkdir -p backend/migrations
echo -e "${GREEN}✓ Directories created${NC}"

# Check if migrations need to be run
echo -e "${YELLOW}Checking database migrations...${NC}"
if [ -f "backend/migrations/create_onboarding_tables.py" ]; then
    echo -e "${YELLOW}Run migrations with: python backend/migrations/create_onboarding_tables.py${NC}"
fi

# Test imports
echo -e "${YELLOW}Testing Python imports...${NC}"
$PYTHON_CMD -c "
import flask
import flask_sqlalchemy
import flask_jwt_extended
import flask_cors
import stripe
import openai
print('✓ All required packages imported successfully')
" 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All imports successful${NC}"
else
    echo -e "${RED}✗ Import errors detected${NC}"
    exit 1
fi

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API credentials"
echo "2. Run database migrations:"
echo "   python backend/migrations/create_onboarding_tables.py"
echo "3. Start the development server:"
echo "   python backend/app.py"
echo "4. Or use production server:"
echo "   gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app"
echo ""
echo "Testing:"
echo "  python test_complete_flow.py"
echo ""
echo "Health check:"
echo "  curl http://localhost:5000/api/health"
echo ""

# Check if running in production
if [ "$FLASK_ENV" = "production" ]; then
    echo -e "${YELLOW}⚠ Running in PRODUCTION mode${NC}"
else
    echo -e "${GREEN}Running in DEVELOPMENT mode${NC}"
fi

echo ""

