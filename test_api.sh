#!/bin/bash
# Simple script to test BMA Social API endpoints

# Load environment variables
source .env.local

echo "Testing BMA Social API..."
echo "========================="

# Test 1: Get conversations
echo -e "\n1. Getting conversations:"
curl -s -X GET "$BMA_SOCIAL_API_URL/api/$BMA_SOCIAL_API_VERSION/conversations" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Accept: application/json" | jq

# Test 2: Get specific conversation messages (you'll need to update the ID)
# echo -e "\n2. Getting messages for conversation:"
# CONVERSATION_ID="your-conversation-id-here"
# curl -s -X GET "$BMA_SOCIAL_API_URL/api/$BMA_SOCIAL_API_VERSION/messages/conversation/$CONVERSATION_ID" \
#   -H "Authorization: Bearer $ACCESS_TOKEN" \
#   -H "Accept: application/json" | jq