#!/bin/bash

# Create new feature branch and spec structure
set -e

NUMBER=""
SHORT_NAME=""
FEATURE_DESC=""
JSON_OUTPUT=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --number)
            NUMBER="$2"
            shift 2
            ;;
        --short-name)
            SHORT_NAME="$2"
            shift 2
            ;;
        --json|--Json|-Json)
            JSON_OUTPUT=true
            shift
            ;;
        *)
            if [ -z "$FEATURE_DESC" ]; then
                FEATURE_DESC="$1"
            fi
            shift
            ;;
    esac
done

if [ -z "$NUMBER" ] || [ -z "$SHORT_NAME" ]; then
    echo "Error: --number and --short-name are required" >&2
    exit 1
fi

BRANCH_NAME="${NUMBER}-${SHORT_NAME}"
FEATURE_DIR="specs/${BRANCH_NAME}"
SPEC_FILE="${FEATURE_DIR}/spec.md"

# Create directory structure
mkdir -p "$FEATURE_DIR"
mkdir -p "${FEATURE_DIR}/checklists"

# Create git branch if git is initialized
if git rev-parse --git-dir > /dev/null 2>&1; then
    git checkout -b "$BRANCH_NAME" 2>/dev/null || git checkout "$BRANCH_NAME" 2>/dev/null || true
fi

# Create empty spec file
touch "$SPEC_FILE"

if [ "$JSON_OUTPUT" = true ]; then
    cat <<EOF
{
  "BRANCH_NAME": "$BRANCH_NAME",
  "SPEC_FILE": "$SPEC_FILE",
  "FEATURE_DIR": "$FEATURE_DIR",
  "NUMBER": "$NUMBER",
  "SHORT_NAME": "$SHORT_NAME"
}
EOF
else
    echo "Created feature: $BRANCH_NAME"
    echo "Spec file: $SPEC_FILE"
fi
