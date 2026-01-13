#!/bin/bash

# Fix API Gateway Route Conflicts
# Deletes manually created routes so Terraform can manage them

set -e

cd "$(dirname "$0")/../infrastructure/terraform"

echo "Getting API ID..."
API_ID=$(terraform output -raw rest_api_id 2>/dev/null)

if [ -z "$API_ID" ]; then
    echo "❌ Could not get API ID from Terraform"
    exit 1
fi

echo "✅ API ID: $API_ID"
echo ""
echo "Finding conflicting routes..."

# Get all routes
ROUTES=$(aws apigatewayv2 get-routes --api-id "$API_ID" --output json)

# Find and delete GET / and GET /health routes
echo "$ROUTES" | jq -r '.Items[] | select(.RouteKey == "GET /" or .RouteKey == "GET /health") | "\(.RouteId) \(.RouteKey)"' | while read -r route_id route_key; do
    echo "  Deleting: $route_key (ID: $route_id)"
    aws apigatewayv2 delete-route --api-id "$API_ID" --route-id "$route_id"
    echo "  ✅ Deleted"
done

echo ""
echo "✅ Conflicting routes removed!"
echo ""
echo "Now run: terraform apply"
