#!/bin/bash

# Deploy Swagger API Documentation to AWS Lambda
# This makes the Swagger docs accessible via a public URL

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY_DIR="${PROJECT_ROOT}/lambda_api_deployment"
ZIP_FILE="${PROJECT_ROOT}/api_handler.zip"

echo -e "${GREEN}⚽ Deploying Swagger Docs to AWS Lambda${NC}"
echo "========================================"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source "${PROJECT_ROOT}/env/bin/activate"
fi

# Clean up old deployment
echo "🧹 Cleaning up old deployment files..."
rm -rf "${DEPLOY_DIR}"
rm -f "${ZIP_FILE}"

# Create deployment directory
echo "📁 Creating deployment package..."
mkdir -p "${DEPLOY_DIR}"

# Copy API source files
echo "  → Copying source files..."
cp "${PROJECT_ROOT}/src/api/swagger_app.py" "${DEPLOY_DIR}/"
cp "${PROJECT_ROOT}/src/api/combined_api_handler.py" "${DEPLOY_DIR}/"

# Install dependencies
echo "  → Installing dependencies..."
pip install mangum fastapi pydantic uvicorn -t "${DEPLOY_DIR}/" --quiet

# Create deployment package
echo "  → Creating ZIP package..."
cd "${DEPLOY_DIR}"
zip -r "${ZIP_FILE}" . -q
cd "${PROJECT_ROOT}"

ZIP_SIZE=$(ls -lh "${ZIP_FILE}" | awk '{print $5}')
echo -e "${GREEN}✅ Package created: ${ZIP_SIZE}${NC}"
echo ""

# Deploy to AWS
echo "🚀 Deploying to AWS Lambda..."
FUNCTION_NAME="football-analytics-api-handler"

if aws lambda get-function --function-name "${FUNCTION_NAME}" &>/dev/null; then
    echo "  → Updating existing function: ${FUNCTION_NAME}"

    aws lambda update-function-code \
        --function-name "${FUNCTION_NAME}" \
        --zip-file "fileb://${ZIP_FILE}" \
        --no-cli-pager

    echo ""
    echo "  → Updating handler configuration..."
    aws lambda update-function-configuration \
        --function-name "${FUNCTION_NAME}" \
        --handler "combined_api_handler.handler" \
        --timeout 30 \
        --memory-size 512 \
        --no-cli-pager

    echo -e "${GREEN}✅ Lambda function updated!${NC}"
else
    echo -e "${RED}❌ Function '${FUNCTION_NAME}' not found${NC}"
    echo "Please create the function first or check the function name."
    exit 1
fi

echo ""
echo "========================================"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo ""
echo "📖 Your Swagger docs are now live at:"
echo "   https://d4pstbgzu1.execute-api.us-east-1.amazonaws.com/development/docs"
echo ""
echo "📋 Also available:"
echo "   ReDoc: https://d4pstbgzu1.execute-api.us-east-1.amazonaws.com/development/redoc"
echo "   Health: https://d4pstbgzu1.execute-api.us-east-1.amazonaws.com/development/health"
echo ""
echo "🧹 Cleaning up..."
rm -rf "${DEPLOY_DIR}"
echo ""
echo -e "${GREEN}Done!${NC}"
