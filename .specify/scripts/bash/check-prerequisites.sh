#!/bin/bash

# Check prerequisites and list available documents
set -e

JSON_OUTPUT=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --json|--Json|-Json)
            JSON_OUTPUT=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Find the current feature directory
SPECS_DIR="specs"
FEATURE_DIR=""

# Try to find the most recent or current feature
if [ -d "$SPECS_DIR" ]; then
    FEATURE_DIR=$(find "$SPECS_DIR" -maxdepth 1 -type d -name "[0-9]*" | sort -V | tail -1)
fi

# If no feature found, try to detect from git branch
if [ -z "$FEATURE_DIR" ] && git rev-parse --git-dir > /dev/null 2>&1; then
    BRANCH_NAME=$(git branch --show-current 2>/dev/null || echo "")
    if [ -n "$BRANCH_NAME" ] && [[ "$BRANCH_NAME" =~ ^[0-9]+- ]]; then
        FEATURE_DIR="$SPECS_DIR/$BRANCH_NAME"
    fi
fi

# Default to the first feature if still not found
if [ -z "$FEATURE_DIR" ]; then
    FEATURE_DIR="$SPECS_DIR/1-anti-crawler-queue"
fi

# Convert to absolute path
FEATURE_DIR=$(cd "$(dirname "$FEATURE_DIR")" && pwd)/$(basename "$FEATURE_DIR")

# Check available documents
AVAILABLE_DOCS=()

if [ -f "$FEATURE_DIR/spec.md" ]; then
    AVAILABLE_DOCS+=("spec.md")
fi

if [ -f "$FEATURE_DIR/plan.md" ]; then
    AVAILABLE_DOCS+=("plan.md")
fi

if [ -f "$FEATURE_DIR/data-model.md" ]; then
    AVAILABLE_DOCS+=("data-model.md")
fi

if [ -f "$FEATURE_DIR/research.md" ]; then
    AVAILABLE_DOCS+=("research.md")
fi

if [ -f "$FEATURE_DIR/quickstart.md" ]; then
    AVAILABLE_DOCS+=("quickstart.md")
fi

if [ -d "$FEATURE_DIR/contracts" ]; then
    AVAILABLE_DOCS+=("contracts/")
fi

if [ "$JSON_OUTPUT" = true ]; then
    # Create JSON array of available docs
    DOCS_JSON="["
    for i in "${!AVAILABLE_DOCS[@]}"; do
        if [ $i -gt 0 ]; then
            DOCS_JSON+=", "
        fi
        DOCS_JSON+="\"${AVAILABLE_DOCS[$i]}\""
    done
    DOCS_JSON+="]"
    
    cat <<EOF
{
  "FEATURE_DIR": "$FEATURE_DIR",
  "AVAILABLE_DOCS": $DOCS_JSON
}
EOF
else
    echo "Feature Directory: $FEATURE_DIR"
    echo "Available Documents:"
    for doc in "${AVAILABLE_DOCS[@]}"; do
        echo "  - $doc"
    done
fi
