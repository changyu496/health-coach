#!/bin/bash
# health-coach init script
# Usage: ./init.sh [workspace_dir]
# Initializes health tracking in the user's workspace

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
WORKSPACE="${1:-.}"
HEALTH_DIR="$WORKSPACE/health"

echo "🏥 Health Coach — Setup"
echo "========================"

# Create directory structure
mkdir -p "$HEALTH_DIR/logs"
echo "✅ Created $HEALTH_DIR/logs/"

# Copy templates if not already present
for file in profile goals reminders; do
  target="$HEALTH_DIR/${file}.md"
  if [ -f "$target" ]; then
    echo "⏭️  $target already exists, skipping"
  else
    cp "$SKILL_DIR/config/${file}.template.md" "$target"
    echo "✅ Created $target"
  fi
done

# Interactive profile setup
echo ""
echo "📋 Let's set up your profile."
echo "   (Press Enter to skip any field)"
echo ""

read -p "Name: " name
read -p "Age: " age
read -p "Sex (male/female/other): " sex
read -p "Height (cm): " height
read -p "Current weight (kg): " weight
read -p "Target weight (kg): " target_weight
read -p "Units (metric/imperial) [metric]: " units
units="${units:-metric}"

# Calculate BMR if we have enough data
if [ -n "$weight" ] && [ -n "$height" ] && [ -n "$age" ] && [ -n "$sex" ]; then
  if [ "$sex" = "male" ]; then
    bmr=$(echo "10 * $weight + 6.25 * $height - 5 * $age + 5" | bc -l)
  else
    bmr=$(echo "10 * $weight + 6.25 * $height - 5 * $age - 161" | bc -l)
  fi
  bmr=$(printf "%.0f" "$bmr")
  tdee=$(printf "%.0f" "$(echo "$bmr * 1.2" | bc -l)")
  target_cal=$(printf "%.0f" "$(echo "$tdee - 650" | bc -l)")
  protein_low=$(printf "%.0f" "$(echo "$weight * 1.6" | bc -l)")
  protein_high=$(printf "%.0f" "$(echo "$weight * 2.0" | bc -l)")

  echo ""
  echo "📊 Calculated values:"
  echo "   BMR: $bmr kcal"
  echo "   TDEE (sedentary): $tdee kcal"
  echo "   Target calories (~650 deficit): $target_cal kcal"
  echo "   Protein target: ${protein_low}-${protein_high}g/day"
fi

# Fill in profile.md
PROFILE="$HEALTH_DIR/profile.md"
if [ -n "$name" ]; then
  sed -i '' "s/^- \*\*Name:\*\*.*/- **Name:** $name/" "$PROFILE" 2>/dev/null || true
fi
if [ -n "$age" ]; then
  sed -i '' "s/^- \*\*Age:\*\*.*/- **Age:** $age/" "$PROFILE" 2>/dev/null || true
fi
if [ -n "$sex" ]; then
  sed -i '' "s/^- \*\*Sex:\*\*.*/- **Sex:** $sex/" "$PROFILE" 2>/dev/null || true
fi
if [ -n "$height" ]; then
  sed -i '' "s/^- \*\*Height:\*\*.*/- **Height:** ${height} cm/" "$PROFILE" 2>/dev/null || true
fi
if [ -n "$weight" ]; then
  sed -i '' "s/^- \*\*Weight:\*\*.*/- **Weight:** ${weight} kg ($(date +%Y-%m-%d))/" "$PROFILE" 2>/dev/null || true
fi
if [ -n "$units" ]; then
  sed -i '' "s/^- \*\*Units:\*\*.*/- **Units:** $units/" "$PROFILE" 2>/dev/null || true
fi

# Fill in calculated values if available
if [ -n "$bmr" ]; then
  sed -i '' "s/^- \*\*BMR:\*\*.*/- **BMR:** $bmr kcal/" "$PROFILE" 2>/dev/null || true
  sed -i '' "s/^- \*\*TDEE:\*\*.*/- **TDEE:** ~$tdee kcal (sedentary)/" "$PROFILE" 2>/dev/null || true
  sed -i '' "s/^- \*\*Target Daily Calories:\*\*.*/- **Target Daily Calories:** ~$target_cal kcal/" "$PROFILE" 2>/dev/null || true
  sed -i '' "s/^- \*\*Target Protein:\*\* g/- **Target Protein:** ${protein_low}-${protein_high}g/" "$PROFILE" 2>/dev/null || true
fi

# Fill in goals.md
if [ -n "$target_weight" ]; then
  GOALS="$HEALTH_DIR/goals.md"
  sed -i '' "s/^- \*\*Target Weight:\*\*.*/- **Target Weight:** ${target_weight} kg/" "$GOALS" 2>/dev/null || true
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Review and edit $HEALTH_DIR/profile.md"
echo "  2. Set your goals in $HEALTH_DIR/goals.md"
echo "  3. Configure reminders in $HEALTH_DIR/reminders.md"
echo "  4. Start logging! Send meal photos and workout data to your health coach."
echo ""
echo "💪 Let's go!"
