#!/bin/bash

# Setup plan script - returns paths for planning workflow
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
# Look for spec.md files in specs/ directory
SPECS_DIR="specs"
FEATURE_DIR=""

# Try to find the most recent or current feature
if [ -d "$SPECS_DIR" ]; then
    # Get the first feature directory (or we can make it smarter)
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

FEATURE_SPEC="${FEATURE_DIR}/spec.md"
IMPL_PLAN="${FEATURE_DIR}/plan.md"
BRANCH=$(basename "$FEATURE_DIR")

if [ "$JSON_OUTPUT" = true ]; then
    cat <<EOF
{
  "FEATURE_SPEC": "$FEATURE_SPEC",
  "IMPL_PLAN": "$IMPL_PLAN",
  "SPECS_DIR": "$SPECS_DIR",
  "BRANCH": "$BRANCH",
  "FEATURE_DIR": "$FEATURE_DIR"
}
EOF
else
    echo "Feature Spec: $FEATURE_SPEC"
    echo "Implementation Plan: $IMPL_PLAN"
    echo "Specs Directory: $SPECS_DIR"
    echo "Branch: $BRANCH"
fi
