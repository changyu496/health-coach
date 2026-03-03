# health-coach 💪

A comprehensive, open-source personal health management skill for AI agents.

Clinical-grade nutritional analysis, medical marker interpretation, exercise programming, and longitudinal health tracking — all running locally with zero data leakage.

## Features

- 🍽️ **Meal Analysis** — Photo or text → calories, macros, nutritional assessment
- 🏥 **Lab Interpretation** — Blood panels, FeNO, thyroid, lipids, urinalysis
- 💪 **Exercise Programming** — Injury-aware training plans, heart rate zones
- 📊 **Body Tracking** — Weight, body fat, waist trends over time
- 💊 **Supplement Guidance** — Evidence-based, interaction-aware
- 📱 **Apple Health Import** — Parse full XML export (weight, workouts, steps, HR, sleep)
- 📈 **Progress Reports** — Daily logs, weekly & monthly summaries

## Quick Start

### Install as a Skill

```bash
npx skills add H1an1/health-coach -g -y
```

### Initialize Your Profile

```bash
cd your-workspace
bash ~/.agents/skills/health-coach/scripts/init.sh .
```

This creates a `health/` directory with your personal profile, goals, and reminder config.

### Import Apple Health Data

1. iPhone → Health → Profile → Export All Health Data
2. Transfer `export.zip` to your computer
3. Unzip and run:

```bash
python3 ~/.agents/skills/health-coach/scripts/apple_health.py export/apple_health_export/export.xml --output health/ --days 30
```

### Generate Reports

```bash
bash ~/.agents/skills/health-coach/scripts/report.sh . --weekly
bash ~/.agents/skills/health-coach/scripts/report.sh . --monthly
```

## Knowledge Base

The `references/` directory contains clinical-grade knowledge:

| File | Contents |
|------|----------|
| `nutrition.md` | BMR/TDEE formulas, macro targets, Chinese food calorie database, portion estimation |
| `medical-markers.md` | CBC, metabolic panel, lipids, thyroid, FeNO, hormones, vitamins, urinalysis |
| `exercise.md` | Training principles, exercise database with injury notes, HR zones, programming templates |
| `supplements.md` | 3-tier evidence classification, interactions, special populations |
| `apple-health.md` | HealthKit data types, interpretation guidelines |

## Privacy

All health data stays 100% local in your workspace. Nothing is uploaded, shared, or transmitted. The skill operates entirely through local files and your AI agent's context.

## Structure

```
health-coach/
├── SKILL.md                    # Skill entry point
├── config/                     # User config templates
│   ├── profile.template.md
│   ├── goals.template.md
│   └── reminders.template.md
├── references/                 # Clinical knowledge base
│   ├── nutrition.md
│   ├── medical-markers.md
│   ├── exercise.md
│   ├── supplements.md
│   └── apple-health.md
├── templates/                  # Report templates
│   ├── daily-log.md
│   ├── weekly-report.md
│   └── monthly-report.md
└── scripts/
    ├── init.sh                 # First-time setup
    ├── report.sh               # Generate reports
    └── apple_health.py         # Apple Health XML parser
```

## Contributing

PRs welcome! Areas that need help:

- More cuisine databases (Japanese, Korean, Indian, etc.)
- Garmin/Fitbit data import
- Workout plan generators
- Localization (currently Chinese + English)

## License

MIT
