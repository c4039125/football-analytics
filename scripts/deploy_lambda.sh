#!/bin/bash

# Lambda Deployment Script for Football Analytics Serverless
# Packages and deploys Lambda functions to AWS

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOYMENT_DIR="${PROJECT_ROOT}/lambda_deployment"
SRC_DIR="${PROJECT_ROOT}/src"

echo -e "${GREEN}Football Analytics - Lambda Deployment${NC}"
echo "========================================"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: Virtual environment not activated${NC}"
    echo "Activating virtual environment..."
    source "${PROJECT_ROOT}/env/bin/activate"
fi

# Create deployment directory
echo "Creating deployment directory..."
rm -rf "${DEPLOYMENT_DIR}"
mkdir -p "${DEPLOYMENT_DIR}"

# Function to package Lambda
package_lambda() {
    local function_name=$1
    local handler_file=$2
    local output_zip=$3
    local requirements_file=${4:-"${PROJECT_ROOT}/requirements-lambda.txt"}

    echo ""
    echo -e "${GREEN}Packaging ${function_name}...${NC}"

    local temp_dir="${DEPLOYMENT_DIR}/${function_name}"
    mkdir -p "${temp_dir}"

    # Copy source code
    echo "  - Copying source code..."
    cp -r "${SRC_DIR}"/* "${temp_dir}/"

    # Install dependencies (for Linux Lambda runtime)
    echo "  - Installing dependencies..."
    pip install -r "${requirements_file}" -t "${temp_dir}" \
        --platform manylinux2014_x86_64 \
        --implementation cp \
        --python-version 3.11 \
        --only-binary=:all: \
        --upgrade \
        --quiet

    # Create zip
    echo "  - Creating deployment package..."
    cd "${temp_dir}"
    zip -r "${output_zip}" . -q

    echo -e "${GREEN}  ✓ Package created: ${output_zip}${NC}"

    cd "${PROJECT_ROOT}"
}

# Package Event Processor Lambda
package_lambda \
    "event-processor" \
    "processing/event_processor.py" \
    "${DEPLOYMENT_DIR}/event_processor.zip"

# Package WebSocket Handler Lambda
package_lambda \
    "websocket-handler" \
    "delivery/websocket_handler.py" \
    "${DEPLOYMENT_DIR}/websocket_handler.zip"

# Package API Handler Lambda (Swagger docs)
package_lambda \
    "api-handler" \
    "api/combined_api_handler.py" \
    "${DEPLOYMENT_DIR}/api_handler.zip" \
    "${PROJECT_ROOT}/requirements-api.txt"

echo ""
echo "========================================"
echo -e "${GREEN}Deployment packages created successfully!${NC}"
echo ""
echo "Deployment packages:"
ls -lh "${DEPLOYMENT_DIR}"/*.zip
echo ""

# Optional: Deploy to AWS
read -p "Deploy to AWS now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Deploying to AWS..."

    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}Error: AWS CLI is not installed${NC}"
        exit 1
    fi

    # Get Lambda function names from Terraform outputs
    cd "${PROJECT_ROOT}/infrastructure/terraform"

    if [ -f "terraform.tfstate" ]; then
        LAMBDA_FUNCTION=$(terraform output -raw lambda_function_name 2>/dev/null || echo "")
        WEBSOCKET_FUNCTION=$(terraform output -raw websocket_function_name 2>/dev/null || echo "football-analytics-websocket-handler-development")
        API_HANDLER_FUNCTION="football-analytics-api-handler-development"

        if [ -n "$LAMBDA_FUNCTION" ]; then
            echo "Updating Lambda function: $LAMBDA_FUNCTION"
            aws lambda update-function-code \
                --function-name "$LAMBDA_FUNCTION" \
                --zip-file "fileb://${DEPLOYMENT_DIR}/event_processor.zip"
            echo -e "${GREEN}✓ Event processor updated${NC}"
        fi

        if [ -n "$WEBSOCKET_FUNCTION" ]; then
            echo "Updating Lambda function: $WEBSOCKET_FUNCTION"
            aws lambda update-function-code \
                --function-name "$WEBSOCKET_FUNCTION" \
                --zip-file "fileb://${DEPLOYMENT_DIR}/websocket_handler.zip"
            echo -e "${GREEN}✓ WebSocket handler updated${NC}"
        fi

        echo "Updating Lambda function: $API_HANDLER_FUNCTION"
        aws lambda update-function-code \
            --function-name "$API_HANDLER_FUNCTION" \
            --zip-file "fileb://${DEPLOYMENT_DIR}/api_handler.zip"
        echo -e "${GREEN}✓ API handler (Swagger docs) updated${NC}"
    else
        echo -e "${YELLOW}Terraform state not found. Please deploy infrastructure first:${NC}"
        echo "  cd infrastructure/terraform && terraform apply"
    fi

    cd "${PROJECT_ROOT}"
fi

echo ""
echo -e "${GREEN}Done!${NC}"
