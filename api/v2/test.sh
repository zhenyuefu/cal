#!/bin/bash

# Test script for Go API v2

echo "Testing Go API v2..."
echo

# Base URL
BASE_URL="http://localhost:8080/api/v2"

# Function to test API endpoint
test_endpoint() {
    local url="$1"
    local description="$2"
    
    echo "Testing: $description"
    echo "URL: $url"
    
    response=$(curl -s -w "HTTP_STATUS:%{http_code}" "$url")
    http_status=$(echo "$response" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
    body=$(echo "$response" | sed 's/HTTP_STATUS:[0-9]*$//')
    
    echo "Status: $http_status"
    if [ "$http_status" = "200" ]; then
        if [[ "$url" == *"/health"* ]]; then
            echo "Response: $body"
        else
            # For iCal responses, show first few lines
            echo "First 5 lines of iCal:"
            echo "$body" | head -5
            echo "Events count: $(echo "$body" | grep -c "BEGIN:VEVENT")"
        fi
        echo "✅ SUCCESS"
    else
        echo "❌ FAILED"
        echo "Response: $body"
    fi
    echo "---"
    echo
}

# Test health endpoint
test_endpoint "$BASE_URL/health" "Health Check"

# Test basic calendar request
test_endpoint "$BASE_URL/cal?MAJ=DAC" "Basic calendar for DAC major"

# Test with specific UE and group
test_endpoint "$BASE_URL/cal?MAJ=DAC&LRC=2&MLBDA=1" "DAC with LRC group 2 and MLBDA group 1"

# Test with semester
test_endpoint "$BASE_URL/cal?MAJ=DAC&SEMESTER=s1" "DAC S1 semester"

# Test with M2 semester
test_endpoint "$BASE_URL/cal?MAJ=DAC&SEMESTER=s3" "DAC M2 semester (s3)"

# Test error case (missing MAJ)
test_endpoint "$BASE_URL/cal?LRC=2" "Error case - missing MAJ parameter"

echo "All tests completed!"