#!/bin/bash
# health-coach report generator
# Usage: ./report.sh [workspace_dir] [--weekly|--monthly] [--date YYYY-MM-DD]
# Generates weekly or monthly health reports from daily logs

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
WORKSPACE="${1:-.}"
HEALTH_DIR="$WORKSPACE/health"
LOGS_DIR="$HEALTH_DIR/logs"
REPORT_TYPE="weekly"
TARGET_DATE=$(date +%Y-%m-%d)

# Parse arguments
shift 2>/dev/null || true
while [[ $# -gt 0 ]]; do
  case $1 in
    --weekly) REPORT_TYPE="weekly"; shift ;;
    --monthly) REPORT_TYPE="monthly"; shift ;;
    --date) TARGET_DATE="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [ ! -d "$LOGS_DIR" ]; then
  echo "❌ No logs directory found at $LOGS_DIR"
  echo "   Run init.sh first, then start logging daily data."
  exit 1
fi

# Calculate date ranges
if [ "$(uname)" = "Darwin" ]; then
  # macOS date
  if [ "$REPORT_TYPE" = "weekly" ]; then
    DOW=$(date -j -f "%Y-%m-%d" "$TARGET_DATE" "+%u" 2>/dev/null || date "+%u")
    DAYS_BACK=$((DOW - 1))
    START_DATE=$(date -j -v-${DAYS_BACK}d -f "%Y-%m-%d" "$TARGET_DATE" "+%Y-%m-%d" 2>/dev/null || date "+%Y-%m-%d")
    END_DATE=$(date -j -v+$((7 - DOW))d -f "%Y-%m-%d" "$TARGET_DATE" "+%Y-%m-%d" 2>/dev/null || date "+%Y-%m-%d")
  else
    START_DATE=$(date -j -f "%Y-%m-%d" "$TARGET_DATE" "+%Y-%m-01" 2>/dev/null || date "+%Y-%m-01")
    END_DATE=$(date -j -v+1m -v-1d -f "%Y-%m-%d" "$START_DATE" "+%Y-%m-%d" 2>/dev/null || date "+%Y-%m-%d")
  fi
else
  # Linux date
  if [ "$REPORT_TYPE" = "weekly" ]; then
    DOW=$(date -d "$TARGET_DATE" "+%u")
    DAYS_BACK=$((DOW - 1))
    START_DATE=$(date -d "$TARGET_DATE - ${DAYS_BACK} days" "+%Y-%m-%d")
    END_DATE=$(date -d "$TARGET_DATE + $((7 - DOW)) days" "+%Y-%m-%d")
  else
    START_DATE=$(date -d "$TARGET_DATE" "+%Y-%m-01")
    END_DATE=$(date -d "$START_DATE + 1 month - 1 day" "+%Y-%m-%d")
  fi
fi

echo "📊 Generating $REPORT_TYPE report"
echo "   Period: $START_DATE — $END_DATE"
echo ""

# Collect log files in date range
LOG_FILES=()
current="$START_DATE"
while [[ "$current" < "$END_DATE" ]] || [[ "$current" == "$END_DATE" ]]; do
  log_file="$LOGS_DIR/$current.md"
  if [ -f "$log_file" ]; then
    LOG_FILES+=("$log_file")
  fi
  if [ "$(uname)" = "Darwin" ]; then
    current=$(date -j -v+1d -f "%Y-%m-%d" "$current" "+%Y-%m-%d" 2>/dev/null || break)
  else
    current=$(date -d "$current + 1 day" "+%Y-%m-%d" 2>/dev/null || break)
  fi
done

echo "📁 Found ${#LOG_FILES[@]} daily log(s)"

if [ ${#LOG_FILES[@]} -eq 0 ]; then
  echo ""
  echo "⚠️  No daily logs found for this period."
  echo "   Daily logs should be at: $LOGS_DIR/YYYY-MM-DD.md"
  echo ""
  echo "   Even without logs, generating a blank report template..."
fi

# Select template
if [ "$REPORT_TYPE" = "weekly" ]; then
  TEMPLATE="$SKILL_DIR/templates/weekly-report.md"
else
  TEMPLATE="$SKILL_DIR/templates/monthly-report.md"
fi

# Generate report
REPORT_FILE="$HEALTH_DIR/${REPORT_TYPE}-report-${START_DATE}.md"

if [ -f "$TEMPLATE" ]; then
  cp "$TEMPLATE" "$REPORT_FILE"

  # Replace date placeholders
  if [ "$REPORT_TYPE" = "weekly" ]; then
    sed -i '' "s/{{START_DATE}}/$START_DATE/g" "$REPORT_FILE" 2>/dev/null || \
    sed -i "s/{{START_DATE}}/$START_DATE/g" "$REPORT_FILE"
    sed -i '' "s/{{END_DATE}}/$END_DATE/g" "$REPORT_FILE" 2>/dev/null || \
    sed -i "s/{{END_DATE}}/$END_DATE/g" "$REPORT_FILE"
  else
    MONTH_NAME=$(date -j -f "%Y-%m-%d" "$START_DATE" "+%B" 2>/dev/null || date -d "$START_DATE" "+%B")
    YEAR=$(date -j -f "%Y-%m-%d" "$START_DATE" "+%Y" 2>/dev/null || date -d "$START_DATE" "+%Y")
    sed -i '' "s/{{MONTH}}/$MONTH_NAME/g" "$REPORT_FILE" 2>/dev/null || \
    sed -i "s/{{MONTH}}/$MONTH_NAME/g" "$REPORT_FILE"
    sed -i '' "s/{{YEAR}}/$YEAR/g" "$REPORT_FILE" 2>/dev/null || \
    sed -i "s/{{YEAR}}/$YEAR/g" "$REPORT_FILE"
  fi
else
  echo "❌ Template not found: $TEMPLATE"
  exit 1
fi

# Extract and aggregate data from logs
if [ ${#LOG_FILES[@]} -gt 0 ]; then
  echo ""
  echo "📈 Aggregating data from logs..."

  total_cal=0
  total_protein=0
  log_count=0
  weights=()
  exercises=()

  for log in "${LOG_FILES[@]}"; do
    log_count=$((log_count + 1))
    log_date=$(basename "$log" .md)

    # Extract weight if present
    w=$(grep -oP 'Weight:\*\*\s*\K[\d.]+' "$log" 2>/dev/null || true)
    if [ -n "$w" ]; then
      weights+=("$log_date:$w")
    fi

    # Extract calorie total if present
    cal=$(grep -oP 'Calories\s*\|\s*\d+\s*\|\s*\K\d+' "$log" 2>/dev/null || true)
    if [ -n "$cal" ]; then
      total_cal=$((total_cal + cal))
    fi

    # Extract exercise entries
    ex=$(grep -A1 '### Exercise' "$log" 2>/dev/null | tail -1 || true)
    if [ -n "$ex" ] && [ "$ex" != "| Activity | Duration | Calories | Avg HR | Notes |" ]; then
      exercises+=("$log_date: $ex")
    fi
  done

  echo "   Days logged: $log_count"
  echo "   Weight entries: ${#weights[@]}"
  echo "   Exercise entries: ${#exercises[@]}"

  if [ $log_count -gt 0 ] && [ $total_cal -gt 0 ]; then
    avg_cal=$((total_cal / log_count))
    echo "   Avg daily calories: $avg_cal"
  fi
fi

echo ""
echo "✅ Report generated: $REPORT_FILE"
echo ""
echo "📝 The report has been pre-filled with available data."
echo "   Review and complete the remaining fields manually or ask your health coach."
