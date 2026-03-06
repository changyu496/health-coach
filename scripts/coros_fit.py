#!/usr/bin/env python3
"""
health-coach Coros FIT file parser

Usage:
  python3 coros_fit.py file1.fit [file2.fit ...] [--output health/] [--no-laps]
  python3 coros_fit.py *.fit --output health/

Parses Coros (and standard FIT) running data. Extracts:
- Session summary: distance, duration, pace, heart rate, calories, cadence
- Lap breakdown: per-lap splits with pace and HR
- Running dynamics: stance time, vertical oscillation, power (when available)

Output: health/coros-import.md (appends new sessions, deduplicates by start_time)
"""

import os
import sys
import re
from datetime import datetime, timezone, timedelta
from argparse import ArgumentParser

try:
    from fitparse import FitFile
except ImportError:
    print("❌ python-fitparse is required. Install with: pip install -r requirements.txt")
    sys.exit(1)


def safe_get(values, key, default=None):
    """Safely get value from dict, handling None."""
    v = values.get(key)
    return default if v is None else v


def or_dash(v):
    """Return value or '—' for None (0 is preserved)."""
    return v if v is not None else "—"


def cadence_to_spm(raw):
    """
    Convert FIT cadence to steps per minute (spm).
    Coros/Garmin store running_cadence as strides/min (one foot) in FIT.
    Steps/min = strides/min × 2. E.g. 94 strides → 188 spm.
    """
    if raw is None:
        return None
    raw = int(raw)
    if raw < 120:  # Likely strides/min (one foot)
        return raw * 2
    return raw


def speed_to_pace_minkm(speed_ms):
    """Convert speed (m/s) to pace (min/km). Returns '—' if invalid."""
    if speed_ms is None or speed_ms <= 0:
        return "—"
    sec_per_km = 1000 / speed_ms
    minutes = int(sec_per_km // 60)
    seconds = int(sec_per_km % 60)
    return f"{minutes}:{seconds:02d}"


def utc_to_local(dt, utc_offset_hours=8):
    """
    Convert UTC datetime to local time.
    FIT timestamps are stored in UTC. Default +8 for East Asia (China).
    """
    if dt is None or not hasattr(dt, "strftime"):
        return dt
    if getattr(dt, "tzinfo", None) is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local_tz = timezone(timedelta(hours=utc_offset_hours))
    return dt.astimezone(local_tz)


def format_duration(seconds):
    """Format seconds as M:SS or H:MM:SS."""
    if seconds is None or seconds < 0:
        return "—"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def parse_session(session_msg, utc_offset_hours=8):
    """Extract session data from FIT session message."""
    v = session_msg.get_values()
    start_time = safe_get(v, "start_time")
    if start_time is None:
        return None

    # FIT timestamps are UTC; convert to local
    start_time = utc_to_local(start_time, utc_offset_hours)

    # Handle datetime objects
    if hasattr(start_time, "strftime"):
        start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        date_str = start_time.strftime("%Y-%m-%d")
        time_str = start_time.strftime("%H:%M:%S")
    else:
        start_str = str(start_time)
        date_str = start_str[:10] if len(start_str) >= 10 else "—"
        time_str = start_str[11:16] if len(start_str) >= 16 else "—"

    sport = safe_get(v, "sport", "unknown")
    sub_sport = safe_get(v, "sub_sport", "")
    sport_label = str(sport).replace("_", " ").title()
    if sub_sport:
        sport_label += f" ({str(sub_sport).replace('_', ' ')})"

    total_dist = safe_get(v, "total_distance", 0) or 0
    dist_km = round(total_dist / 1000, 2) if total_dist else 0

    elapsed = safe_get(v, "total_elapsed_time") or safe_get(v, "total_timer_time")
    avg_speed = safe_get(v, "enhanced_avg_speed") or safe_get(v, "avg_speed")
    pace = speed_to_pace_minkm(avg_speed)

    return {
        "start_time": start_str,
        "date": date_str,
        "time": time_str,
        "sport": sport_label,
        "distance_km": dist_km,
        "duration_sec": elapsed,
        "duration_str": format_duration(elapsed),
        "pace": pace,
        "calories": safe_get(v, "total_calories"),
        "avg_hr": safe_get(v, "avg_heart_rate"),
        "max_hr": safe_get(v, "max_heart_rate"),
        "min_hr": safe_get(v, "min_heart_rate"),
        "total_ascent": safe_get(v, "total_ascent"),
        "total_descent": safe_get(v, "total_descent"),
        "total_strides": safe_get(v, "total_strides"),
        "avg_cadence": cadence_to_spm(safe_get(v, "avg_running_cadence")),
        "max_cadence": cadence_to_spm(safe_get(v, "max_running_cadence")),
        "avg_step_length_mm": safe_get(v, "avg_step_length"),
        "avg_power": safe_get(v, "avg_power"),
        "avg_stance_time_ms": safe_get(v, "avg_stance_time"),
        "avg_vertical_oscillation_mm": safe_get(v, "avg_vertical_oscillation"),
        "avg_vertical_ratio_pct": safe_get(v, "avg_vertical_ratio"),
        "avg_temperature": safe_get(v, "avg_temperature"),
    }


def parse_lap(lap_msg):
    """Extract lap data from FIT lap message."""
    v = lap_msg.get_values()
    start_time = safe_get(v, "start_time")
    if start_time is None:
        return None

    total_dist = safe_get(v, "total_distance", 0) or 0
    dist_km = round(total_dist / 1000, 2) if total_dist else 0
    elapsed = safe_get(v, "total_elapsed_time") or safe_get(v, "total_timer_time")
    avg_speed = safe_get(v, "enhanced_avg_speed") or safe_get(v, "avg_speed")

    return {
        "distance_km": dist_km,
        "duration_sec": elapsed,
        "duration_str": format_duration(elapsed),
        "pace": speed_to_pace_minkm(avg_speed),
        "avg_hr": safe_get(v, "avg_heart_rate"),
        "calories": safe_get(v, "total_calories"),
        "avg_cadence": cadence_to_spm(safe_get(v, "avg_running_cadence")),
    }


def parse_fit_file(path, utc_offset_hours=8):
    """Parse a single FIT file, return list of (session, laps) tuples."""
    results = []
    try:
        fit = FitFile(path)
    except Exception as e:
        print(f"   ⚠️  Failed to parse {path}: {e}")
        return results

    sessions = list(fit.get_messages("session"))
    if not sessions:
        print(f"   ⚠️  No session in {path}")
        return results

    all_laps = []
    for lap in fit.get_messages("lap"):
        lap_data = parse_lap(lap)
        if lap_data:
            all_laps.append(lap_data)

    # Typically 1 session per file; all laps belong to it
    for sess in sessions:
        session_data = parse_session(sess, utc_offset_hours)
        if session_data:
            results.append((session_data, all_laps))

    return results


def parse_existing_sessions(md_path):
    """Parse existing coros-import.md to extract start_time for deduplication."""
    if not os.path.exists(md_path):
        return set()
    seen = set()
    with open(md_path, "r") as f:
        for line in f:
            # Match table data rows: | 2026-03-04 | 12:17:15 | Running | ...
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                date_part = parts[1]
                time_part = parts[2]
                if re.match(r"\d{4}-\d{2}-\d{2}", date_part) and ":" in time_part:
                    # Normalize to YYYY-MM-DD HH:MM:SS (pad time if HH:MM)
                    if time_part.count(":") == 1:
                        time_part += ":00"
                    seen.add(f"{date_part} {time_part}"[:19])
    return seen


def session_to_dedup_key(s):
    """Key for deduplication."""
    return s.get("start_time", "")[:19]


def write_session_md(session, laps, f, include_laps=True):
    """Write one session block to file."""
    s = session
    f.write(f"| {s['date']} | {s['time']} | {s['sport']} | ")
    f.write(f"{s['distance_km']} km | {s['duration_str']} | {s['pace']}/km | ")
    f.write(f"{s['calories'] or '—'} | ")
    f.write(f"{s['avg_hr'] or '—'} | {s['max_hr'] or '—'} | ")
    f.write(f"{s['avg_cadence'] or '—'} | ")
    f.write(f"{s['total_strides'] or '—'} | ")
    f.write(f"{s['avg_step_length_mm'] or '—'} | ")
    f.write(f"{s['avg_stance_time_ms'] or '—'} | ")
    f.write(f"{s['avg_vertical_oscillation_mm'] or '—'} | ")
    f.write(f"{s['avg_power'] or '—'} | ")
    f.write(f"{or_dash(s['total_ascent'])}/{or_dash(s['total_descent'])} |\n")

    if include_laps and laps:
        f.write("\n**Laps:**\n")
        f.write("| Lap | Distance | Duration | Pace | Avg HR | Cadence |\n")
        f.write("|-----|----------|----------|------|--------|--------|\n")
        for i, lap in enumerate(laps, 1):
            f.write(f"| {i} | {lap['distance_km']} km | {lap['duration_str']} | ")
            f.write(f"{lap['pace']}/km | {lap['avg_hr'] or '—'} | {lap['avg_cadence'] or '—'} |\n")
        f.write("\n")


def generate_markdown(all_sessions, output_path, existing_path, include_laps, append):
    """Generate or append to coros-import.md."""
    seen = parse_existing_sessions(existing_path) if append else set()
    new_sessions = []
    for sess, laps in all_sessions:
        key = session_to_dedup_key(sess)
        if key in seen:
            continue
        seen.add(key)
        new_sessions.append((sess, laps))

    if not new_sessions:
        return output_path, 0

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    file_exists = os.path.exists(output_path)

    with open(output_path, "a" if append and file_exists else "w") as f:
        if not (append and file_exists):
            f.write(f"# Coros Import — {datetime.now().strftime('%Y-%m-%d')}\n\n")
            f.write("Parsed from FIT files. Reference `references/coros-running.md` for metric interpretation.\n\n")
            f.write("## Sessions\n\n")
            f.write("| Date | Time | Sport | Distance | Duration | Pace | Cal | Avg HR | Max HR | Cadence | Strides | Step Len | Stance | Vert Osc | Power | ↑/↓ |\n")
            f.write("|------|------|-------|----------|----------|------|-----|--------|--------|---------|---------|----------|--------|----------|-------|-----|\n")

        for sess, laps in sorted(new_sessions, key=lambda x: x[0]["start_time"]):
            write_session_md(sess, laps, f, include_laps)

    return output_path, len(new_sessions)


def main():
    parser = ArgumentParser(
        description="Parse Coros/Garmin FIT running files",
        epilog="Example: python3 coros_fit.py run1.fit run2.fit --output health/",
    )
    parser.add_argument(
        "fit_files",
        nargs="+",
        help="One or more .fit files to parse",
    )
    parser.add_argument(
        "--output", "-o",
        default="health/",
        help="Output directory (default: health/)",
    )
    parser.add_argument(
        "--no-laps",
        action="store_true",
        help="Omit lap breakdown from output",
    )
    parser.add_argument(
        "--no-append",
        action="store_true",
        help="Overwrite output file instead of appending",
    )
    parser.add_argument(
        "--timezone", "-z",
        type=int,
        default=8,
        help="UTC offset in hours for local time (default: 8 for East Asia)",
    )

    args = parser.parse_args()

    output_dir = args.output.rstrip("/")
    output_path = os.path.join(output_dir, "coros-import.md")
    existing_path = output_path if not args.no_append else None

    all_sessions = []
    for path in args.fit_files:
        if not os.path.exists(path):
            print(f"❌ File not found: {path}")
            continue
        print(f"📱 Parsing: {path}")
        for sess, laps in parse_fit_file(path, utc_offset_hours=args.timezone):
            all_sessions.append((sess, laps))
            print(f"   Found: {sess['date']} {sess['time']} — {sess['distance_km']} km {sess['sport']}")

    if not all_sessions:
        print("❌ No sessions found in any file")
        sys.exit(1)

    _, n_new = generate_markdown(
        all_sessions,
        output_path,
        existing_path,
        include_laps=not args.no_laps,
        append=not args.no_append,
    )

    if n_new > 0:
        print(f"\n✅ Summary written to: {output_path} ({n_new} new session(s))")
        print("   Review and share with your health coach.")
    else:
        print("\n   No new sessions (all already imported).")


if __name__ == "__main__":
    main()
