#!/bin/bash
# Approval Gate Hook
# Transitions Jira issue to next stage when approved

STAGE=$1
ISSUE_KEY=$2
REVIEWER=$3
APPROVAL_COMMENT=$4

# Record approval
APPROVAL_FILE="documents/.approval-gates/${STAGE}-approved-$(date +%s).txt"
mkdir -p documents/.approval-gates

cat > "$APPROVAL_FILE" << EOF
Stage: $STAGE
Approved: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Reviewer: $REVIEWER
Comment: $APPROVAL_COMMENT
Issue: $ISSUE_KEY
EOF

echo "Approval recorded: $APPROVAL_FILE"
