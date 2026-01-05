#!/bin/bash

# Installation script for Football Analytics Serverless System
# Author: Adebayo Oyeleye
# Description: Automated setup script for the complete system

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_header() {
    echo ""
    echo "=================================================="
    echo "$1"
    echo "=================================================="
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

print_header "Football Analytics Serverless - Installation Script"

# Check Python version
print_info "Checking Python version..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"

    # Check if version is 3.11 or higher
    REQUIRED_VERSION="3.11"
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
        print_success "Python version meets requirements (>= 3.11)"
    else
        print_error "Python 3.11 or higher is required. Current version: $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 is not installed"
    exit 1
fi

# Check pip
print_info "Checking pip..."
if command_exists pip3; then
    print_success "pip3 found"
else
    print_error "pip3 is not installed"
    exit 1
fi

# Create virtual environment
print_info "Creating virtual environment..."
if [ -d "venv" ]; then
    print_info "Virtual environment already exists, skipping..."
else
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip >/dev/null 2>&1
print_success "pip upgraded"

# Install production dependencies
print_info "Installing production dependencies..."
pip install -r requirements.txt
print_success "Production dependencies installed"

# Ask if development dependencies should be installed
read -p "Install development dependencies? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Installing development dependencies..."
    pip install -r requirements-dev.txt
    print_success "Development dependencies installed"
fi

# Create necessary directories
print_info "Creating project directories..."
mkdir -p data/raw data/processed data/synthetic
mkdir -p logs
mkdir -p lambda_deployment
touch data/raw/.gitkeep
touch data/processed/.gitkeep
touch data/synthetic/.gitkeep
print_success "Directories created"

# Copy configuration file
print_info "Setting up configuration..."
if [ -f "config/config.env" ]; then
    print_info "config.env already exists, skipping..."
else
    cp config/config.example.env config/config.env
    print_success "Configuration file created: config/config.env"
    print_info "Please edit config/config.env with your settings"
fi

# Check for AWS CLI
print_info "Checking for AWS CLI..."
if command_exists aws; then
    print_success "AWS CLI found"
    AWS_VERSION=$(aws --version | cut -d' ' -f1)
    print_info "Version: $AWS_VERSION"
else
    print_info "AWS CLI not found. Install it to deploy to AWS:"
    print_info "  https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html"
fi

# Check for Docker
print_info "Checking for Docker..."
if command_exists docker; then
    print_success "Docker found"
    print_info "You can use LocalStack for local development"
else
    print_info "Docker not found. Install it to use LocalStack:"
    print_info "  https://docs.docker.com/get-docker/"
fi

# Check for Terraform
print_info "Checking for Terraform..."
if command_exists terraform; then
    print_success "Terraform found"
    TERRAFORM_VERSION=$(terraform --version | head -n1)
    print_info "Version: $TERRAFORM_VERSION"
else
    print_info "Terraform not found. Install it to deploy infrastructure:"
    print_info "  https://www.terraform.io/downloads.html"
fi

# Run tests to verify installation
read -p "Run tests to verify installation? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Running tests..."
    if pytest tests/unit -v; then
        print_success "All tests passed!"
    else
        print_error "Some tests failed. Please check the output above."
    fi
fi

# Generate synthetic data
read -p "Generate synthetic match data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Generating synthetic data..."
    python scripts/generate_synthetic_data.py --matches 3 --output data/synthetic
    print_success "Synthetic data generated"
fi

print_header "Installation Complete!"

echo ""
echo "Next steps:"
echo "  1. Edit config/config.env with your settings"
echo "  2. Activate virtual environment: source venv/bin/activate"
echo "  3. Run tests: make test (or pytest tests/)"
echo "  4. Generate data: make generate-data"
echo "  5. Deploy to AWS: make deploy"
echo ""
echo "For more information, see:"
echo "  - README.md"
echo "  - QUICKSTART.md"
echo "  - docs/"
echo ""
echo "Happy coding!"
echo ""

print_success "Installation successful!"
