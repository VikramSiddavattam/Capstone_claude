#!/bin/bash
# Stage Completion Hook
# Triggered when an agent completes their stage

STAGE=$1
STAGE_FOLDER=$2
ISSUE_KEY=$3

# Create approval gate checkpoint
GATE_FILE="documents/.approval-gates/${STAGE}-completed-$(date +%s).txt"
mkdir -p documents/.approval-gates

cat > "$GATE_FILE" << EOF
Stage: $STAGE
Completed: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Status: PENDING_REVIEW
Artifacts: $STAGE_FOLDER
Jira Issue: $ISSUE_KEY
EOF

echo "Stage completion recorded: $GATE_FILE"
