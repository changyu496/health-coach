#!/usr/bin/env python3
"""
health-coach Apple Health data parser
Usage: python3 apple_health.py <export.xml> [--output health/] [--days 30] [--format md|json]

Parses Apple Health XML export and extracts:
- Body measurements (weight, body fat, waist)
- Workouts (type, duration, calories, HR)
- Activity (steps, active calories, stand hours)
- Sleep analysis
- Heart rate (resting, walking avg, HRV)
"""

import xml.etree.ElementTree as ET
import json
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict
from argparse import ArgumentParser

# HealthKit type mappings
BODY_TYPES = {
    'HKQuantityTypeIdentifierBodyMass': 'weight_kg',
    'HKQuantityTypeIdentifierBodyFatPercentage': 'body_fat_pct',
    'HKQuantityTypeIdentifierHeight': 'height_cm',
    'HKQuantityTypeIdentifierWaistCircumference': 'waist_cm',
    'HKQuantityTypeIdentifierBMI': 'bmi',
}

ACTIVITY_TYPES = {
    'HKQuantityTypeIdentifierStepCount': 'steps',
    'HKQuantityTypeIdentifierActiveEnergyBurned': 'active_cal',
    'HKQuantityTypeIdentifierBasalEnergyBurned': 'resting_cal',
    'HKQuantityTypeIdentifierAppleExerciseTime': 'exercise_min',
    'HKQuantityTypeIdentifierAppleStandTime': 'stand_hours',
}

HR_TYPES = {
    'HKQuantityTypeIdentifierHeartRate': 'heart_rate',
    'HKQuantityTypeIdentifierRestingHeartRate': 'resting_hr',
    'HKQuantityTypeIdentifierWalkingHeartRateAverage': 'walking_hr',
    'HKQuantityTypeIdentifierHeartRateVariabilitySDNN': 'hrv',
}

WORKOUT_TYPE_NAMES = {
    'HKWorkoutActivityTypeRunning': 'Running',
    'HKWorkoutActivityTypeSwimming': 'Swimming',
    'HKWorkoutActivityTypeWalking': 'Walking',
    'HKWorkoutActivityTypeCycling': 'Cycling',
    'HKWorkoutActivityTypeTraditionalStrengthTraining': 'Strength',
    'HKWorkoutActivityTypeFunctionalStrengthTraining': 'Functional Strength',
    'HKWorkoutActivityTypeHIIT': 'HIIT',
    'HKWorkoutActivityTypeYoga': 'Yoga',
    'HKWorkoutActivityTypeElliptical': 'Elliptical',
    'HKWorkoutActivityTypeRowing': 'Rowing',
    'HKWorkoutActivityTypeStairClimbing': 'Stair Climbing',
    'HKWorkoutActivityTypeMixedCardio': 'Mixed Cardio',
    'HKWorkoutActivityTypeBoxing': 'Boxing',
}


def parse_date(date_str):
    """Parse Apple Health date format."""
    for fmt in ('%Y-%m-%d %H:%M:%S %z', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def parse_health_export(xml_path, days=30):
    """Parse Apple Health XML export."""
    print(f"📱 Parsing Apple Health export: {xml_path}")
    print(f"   Looking at last {days} days...")

    cutoff = datetime.now().astimezone() - timedelta(days=days)
    
    data = {
        'body': defaultdict(list),      # date -> [{type, value, date}]
        'activity': defaultdict(lambda: defaultdict(float)),  # date -> {steps, cal, ...}
        'workouts': [],                  # [{type, date, duration_min, calories, distance_km}]
        'heart_rate': defaultdict(list), # date -> [{type, value}]
        'sleep': defaultdict(list),      # date -> [{start, end, duration_h, stage}]
    }

    # Iterative parsing for large files
    # Use a custom parser that recovers from invalid tokens
    xml_parser = ET.XMLParser(encoding='utf-8')
    
    # Try lxml for recover mode, fall back to sanitized iterparse
    try:
        from lxml import etree as lxml_etree
        context = lxml_etree.iterparse(xml_path, events=('end',), recover=True, huge_tree=True)
        use_lxml = True
    except ImportError:
        # Fallback: read file, sanitize invalid XML chars, parse
        import re
        print("   (lxml not available, using sanitized parsing...)")
        
        def sanitize_xml_iter(path):
            """Read XML file line by line, removing invalid chars."""
            invalid_xml_re = re.compile(
                '[^\u0009\u000A\u000D\u0020-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]'
            )
            with open(path, 'rb') as f:
                for line_bytes in f:
                    try:
                        line = line_bytes.decode('utf-8', errors='replace')
                    except Exception:
                        continue
                    yield invalid_xml_re.sub('', line).encode('utf-8')
        
        # Write sanitized to temp file
        import tempfile
        print("   Sanitizing XML (this may take a moment for large files)...")
        tmp_path = tempfile.mktemp(suffix='.xml')
        with open(tmp_path, 'wb') as tmp_f:
            for chunk in sanitize_xml_iter(xml_path):
                tmp_f.write(chunk)
        print("   Sanitized. Parsing...")
        context = ET.iterparse(tmp_path, events=('end',))
        use_lxml = False
    
    record_count = 0

    for event, elem in context:
        if elem.tag == 'Record':
            record_count += 1
            rtype = elem.get('type', '')
            date_str = elem.get('startDate', '')
            value = elem.get('value', '')
            dt = parse_date(date_str)

            if dt is None or dt < cutoff:
                elem.clear()
                continue

            date_key = dt.strftime('%Y-%m-%d')

            # Body measurements
            if rtype in BODY_TYPES:
                data['body'][date_key].append({
                    'type': BODY_TYPES[rtype],
                    'value': float(value),
                    'time': dt.strftime('%H:%M'),
                })

            # Activity
            elif rtype in ACTIVITY_TYPES:
                key = ACTIVITY_TYPES[rtype]
                data['activity'][date_key][key] += float(value)

            # Heart rate
            elif rtype in HR_TYPES:
                data['heart_rate'][date_key].append({
                    'type': HR_TYPES[rtype],
                    'value': float(value),
                })

            # Sleep
            elif rtype == 'HKCategoryTypeIdentifierSleepAnalysis':
                end_str = elem.get('endDate', '')
                end_dt = parse_date(end_str)
                if end_dt:
                    duration_h = (end_dt - dt).total_seconds() / 3600
                    data['sleep'][date_key].append({
                        'start': dt.strftime('%H:%M'),
                        'end': end_dt.strftime('%H:%M'),
                        'duration_h': round(duration_h, 2),
                        'stage': value,
                    })

            elem.clear()

        elif elem.tag == 'Workout':
            record_count += 1
            date_str = elem.get('startDate', '')
            dt = parse_date(date_str)

            if dt is None or dt < cutoff:
                elem.clear()
                continue

            wtype = elem.get('workoutActivityType', 'Unknown')
            duration = float(elem.get('duration', 0))
            calories = float(elem.get('totalEnergyBurned', 0))
            distance = float(elem.get('totalDistance', 0))

            data['workouts'].append({
                'type': WORKOUT_TYPE_NAMES.get(wtype, wtype.replace('HKWorkoutActivityType', '')),
                'date': dt.strftime('%Y-%m-%d'),
                'time': dt.strftime('%H:%M'),
                'duration_min': round(duration, 1),
                'calories': round(calories),
                'distance_km': round(distance / 1000, 2) if distance > 0 else 0,
            })

            elem.clear()

    print(f"   Processed {record_count} records")
    return data


def generate_markdown(data, output_dir):
    """Generate markdown summary from parsed data."""
    os.makedirs(output_dir, exist_ok=True)
    summary_path = os.path.join(output_dir, 'apple-health-import.md')

    with open(summary_path, 'w') as f:
        f.write(f"# Apple Health Import — {datetime.now().strftime('%Y-%m-%d')}\n\n")

        # Body measurements
        if data['body']:
            f.write("## Body Measurements\n")
            f.write("| Date | Type | Value |\n|------|------|-------|\n")
            for date in sorted(data['body'].keys()):
                for entry in data['body'][date]:
                    unit = 'kg' if 'weight' in entry['type'] else '%' if 'pct' in entry['type'] else 'cm'
                    f.write(f"| {date} | {entry['type']} | {entry['value']} {unit} |\n")
            f.write("\n")

        # Activity summary
        if data['activity']:
            f.write("## Daily Activity\n")
            f.write("| Date | Steps | Active Cal | Exercise Min |\n|------|-------|-----------|-------------|\n")
            for date in sorted(data['activity'].keys()):
                a = data['activity'][date]
                f.write(f"| {date} | {int(a.get('steps', 0)):,} | {int(a.get('active_cal', 0))} | {int(a.get('exercise_min', 0))} |\n")
            f.write("\n")

            # Averages
            dates = list(data['activity'].keys())
            if dates:
                avg_steps = sum(data['activity'][d].get('steps', 0) for d in dates) / len(dates)
                avg_cal = sum(data['activity'][d].get('active_cal', 0) for d in dates) / len(dates)
                f.write(f"**Averages:** {int(avg_steps):,} steps/day, {int(avg_cal)} active cal/day\n\n")

        # Workouts
        if data['workouts']:
            f.write("## Workouts\n")
            f.write("| Date | Time | Type | Duration | Calories | Distance |\n")
            f.write("|------|------|------|----------|----------|----------|\n")
            for w in sorted(data['workouts'], key=lambda x: x['date']):
                dist = f"{w['distance_km']}km" if w['distance_km'] > 0 else '—'
                f.write(f"| {w['date']} | {w['time']} | {w['type']} | {w['duration_min']}min | {w['calories']}cal | {dist} |\n")
            f.write(f"\n**Total workouts:** {len(data['workouts'])}\n\n")

        # Heart rate
        if data['heart_rate']:
            f.write("## Heart Rate Summary\n")
            resting_hrs = []
            hrvs = []
            for date in sorted(data['heart_rate'].keys()):
                for entry in data['heart_rate'][date]:
                    if entry['type'] == 'resting_hr':
                        resting_hrs.append((date, entry['value']))
                    elif entry['type'] == 'hrv':
                        hrvs.append((date, entry['value']))

            if resting_hrs:
                f.write("### Resting Heart Rate\n")
                f.write("| Date | RHR (bpm) |\n|------|-----------|\n")
                for date, val in resting_hrs[-14:]:  # Last 14 entries
                    f.write(f"| {date} | {int(val)} |\n")
                avg_rhr = sum(v for _, v in resting_hrs) / len(resting_hrs)
                f.write(f"\n**Average RHR:** {int(avg_rhr)} bpm\n\n")

            if hrvs:
                f.write("### Heart Rate Variability\n")
                f.write("| Date | HRV (ms) |\n|------|----------|\n")
                for date, val in hrvs[-14:]:
                    f.write(f"| {date} | {int(val)} |\n")
                avg_hrv = sum(v for _, v in hrvs) / len(hrvs)
                f.write(f"\n**Average HRV:** {int(avg_hrv)} ms\n\n")

        # Sleep
        if data['sleep']:
            f.write("## Sleep Summary\n")
            f.write("| Date | Total Hours | Notes |\n|------|------------|-------|\n")
            for date in sorted(data['sleep'].keys()):
                entries = data['sleep'][date]
                total_h = sum(e['duration_h'] for e in entries)
                f.write(f"| {date} | {total_h:.1f}h | {len(entries)} segments |\n")
            f.write("\n")

    print(f"✅ Summary written to: {summary_path}")
    return summary_path


def generate_json(data, output_dir):
    """Export parsed data as JSON for programmatic use."""
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, 'apple-health-import.json')

    # Convert defaultdicts to regular dicts for JSON serialization
    export = {
        'exported_at': datetime.now().isoformat(),
        'body': dict(data['body']),
        'activity': {k: dict(v) for k, v in data['activity'].items()},
        'workouts': data['workouts'],
        'heart_rate': dict(data['heart_rate']),
        'sleep': dict(data['sleep']),
    }

    with open(json_path, 'w') as f:
        json.dump(export, f, indent=2, ensure_ascii=False)

    print(f"✅ JSON written to: {json_path}")
    return json_path


def main():
    parser = ArgumentParser(description='Parse Apple Health XML export')
    parser.add_argument('xml_path', help='Path to Apple Health export.xml')
    parser.add_argument('--output', '-o', default='health/', help='Output directory (default: health/)')
    parser.add_argument('--days', '-d', type=int, default=30, help='Days of history to parse (default: 30)')
    parser.add_argument('--format', '-f', choices=['md', 'json', 'both'], default='both',
                        help='Output format (default: both)')

    args = parser.parse_args()

    if not os.path.exists(args.xml_path):
        print(f"❌ File not found: {args.xml_path}")
        sys.exit(1)

    data = parse_health_export(args.xml_path, days=args.days)

    if args.format in ('md', 'both'):
        generate_markdown(data, args.output)
    if args.format in ('json', 'both'):
        generate_json(data, args.output)

    print("\n🎉 Import complete! Review the generated files and share with your health coach.")


if __name__ == '__main__':
    main()
