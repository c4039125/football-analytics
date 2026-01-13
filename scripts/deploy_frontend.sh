#!/bin/bash
# Deploy React Frontend to S3 + CloudFront
# Usage: ./scripts/deploy_frontend.sh

set -e  # Exit on error

echo "🚀 Deploying Football Analytics Frontend..."

# Colors for output
GREEN='\033[0.32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get API Gateway URL from Terraform
cd infrastructure/terraform
API_URL=$(terraform output -raw rest_api_endpoint 2>/dev/null || echo "")
BUCKET_NAME=$(terraform output -raw frontend_bucket_name 2>/dev/null || echo "")
CLOUDFRONT_ID=$(terraform output -raw frontend_cloudfront_id 2>/dev/null || echo "")
cd ../..

if [ -z "$BUCKET_NAME" ]; then
    echo "❌ Error: Frontend S3 bucket not found."
    echo "Run 'terraform apply' first to create frontend infrastructure."
    exit 1
fi

echo "📦 Bucket: $BUCKET_NAME"
echo "🌐 API URL: $API_URL"

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "❌ Error: frontend directory not found"
    exit 1
fi

cd frontend

# Create .env.production file with API URL
echo "Creating production environment configuration..."
cat > .env.production <<EOF
REACT_APP_API_URL=${API_URL}
REACT_APP_ENVIRONMENT=production
EOF

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Build React app
echo "🔨 Building React application..."
npm run build

if [ ! -d "build" ]; then
    echo "❌ Error: Build failed - build directory not found"
    exit 1
fi

# Sync build folder to S3
echo "☁️  Uploading to S3: ${BUCKET_NAME}..."
aws s3 sync build/ s3://${BUCKET_NAME}/ \
    --delete \
    --cache-control "public, max-age=31536000" \
    --exclude "index.html" \
    --exclude "*.map"

# Upload index.html separately with no-cache
aws s3 cp build/index.html s3://${BUCKET_NAME}/index.html \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html"

echo "✅ Files uploaded to S3"

# Invalidate CloudFront cache
if [ -n "$CLOUDFRONT_ID" ]; then
    echo "🔄 Invalidating CloudFront cache..."
    aws cloudfront create-invalidation \
        --distribution-id ${CLOUDFRONT_ID} \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text

    echo "✅ CloudFront cache invalidated"
fi

# Get CloudFront URL
CLOUDFRONT_URL=$(cd ../infrastructure/terraform && terraform output -raw frontend_cloudfront_url)

echo ""
echo -e "${GREEN}✅ Frontend deployment complete!${NC}"
echo ""
echo -e "${BLUE}🌐 Frontend URL:${NC}"
echo "$CLOUDFRONT_URL"
echo ""
echo -e "${BLUE}📊 S3 Bucket:${NC}"
echo "https://s3.console.aws.amazon.com/s3/buckets/${BUCKET_NAME}"
echo ""
echo "🎉 Open the URL above to see your live dashboard!"
echo ""

cd ..
