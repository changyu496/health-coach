# Reminder Configuration

## Schedule
Configure active reminders by uncommenting and adjusting times.

### Morning Routine
- wake_up: "07:00"          # Adjust to sleep cycle
- morning_weight: "07:05"   # Weigh before eating
- breakfast: "07:30"

### Work Day Breaks
- movement_1: "10:00"       # 5-min movement break
- movement_2: "15:00"       # 5-min movement break
- eye_break: "hourly"       # 20-20-20 rule (optional)

### Meals
- pre_lunch_supplement: "11:30"   # e.g., fiber supplement
- lunch: "12:00"
- pre_dinner_supplement: "17:30"
- dinner: "18:00"

### Exercise
- workout_reminder: "18:30"  # Or preferred workout time
- workout_days: ["Mon", "Wed", "Fri"]  # Active days

### Evening
- last_meal_cutoff: "20:00"  # Stop eating reminder
- supplement_evening: "21:00" # e.g., magnesium, melatonin
- wind_down: "22:00"         # Screen time, prep for sleep
- sleep: "22:30"

### Weekly
- weigh_in: "Sun 07:05"
- weekly_review: "Sun 20:00"
- meal_prep: "Sun 14:00"     # Optional meal prep reminder

## Reminder Style
- **tone:** encouraging       # encouraging / neutral / drill-sergeant
- **length:** brief           # brief / detailed
- **include_tip:** true       # Add a quick health tip

## Notification Preferences
- **quiet_hours:** "22:30-07:00"
- **skip_if_acknowledged:** true
