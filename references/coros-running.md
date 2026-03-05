# Coros / FIT Running Data Reference

Interpretation guide for running data from Coros watches (and compatible FIT files from Garmin, Polar, etc.).

## Data Source

- **Export:** Coros app or website → export FIT/GPX
- **Parse:** `python3 scripts/coros_fit.py yourfile.fit --output health/`
- **Output:** `health/coros-import.md` (session summary + lap breakdown)

## Key Metrics

### Pace (min/km)

| Pace | Intensity | Typical Use |
|------|-----------|-------------|
| >6:00/km | Easy / Zone 2 | Recovery, long runs |
| 5:00–6:00/km | Moderate | Base building |
| 4:00–5:00/km | Tempo / Threshold | Lactate threshold work |
| 3:30–4:00/km | Hard | Interval, race pace |
| <3:30/km | Very hard | Sprint, 5K effort |

### Heart Rate Zones (Running)

| Zone | % HRmax | RPE | Purpose |
|------|---------|-----|---------|
| 1 (Recovery) | 50–60% | Very easy | Active recovery |
| 2 (Endurance) | 60–70% | Easy conversation | Fat oxidation, base |
| 3 (Tempo) | 70–80% | Uncomfortable | Aerobic capacity |
| 4 (Threshold) | 80–90% | Hard | Lactate threshold |
| 5 (Max) | 90–100% | All-out | VO2max |

**HRmax estimate:** 220 − age (rough) or 207 − 0.7 × age (more accurate)

### Cadence (steps/min)

Running cadence = steps per minute (both feet). Coros/Garmin FIT stores as strides/min (one foot); the parser converts to spm.

| Cadence | Notes |
|---------|-------|
| 160–180 spm | Efficient range; 170–180 often cited as optimal |
| <160 | May indicate overstriding |
| >190 | May indicate shuffling |

### Running Dynamics (Coros / Garmin)

#### Stance Time (ms)

Time foot spends on ground per step.

| Value | Interpretation |
|-------|----------------|
| 200–300 ms | Typical range |
| >300 ms | May indicate overstriding or fatigue |
| Decreasing over run | Often a sign of fatigue |

#### Vertical Oscillation (mm)

Up-down movement of torso per step.

| Value | Interpretation |
|-------|----------------|
| 70–100 mm | Typical |
| >100 mm | "Bouncing" — may waste energy |
| <70 mm | Very efficient (elite runners often 60–80) |

#### Vertical Ratio (%)

Vertical oscillation / step length. Lower = more efficient.

| Value | Notes |
|-------|-------|
| 6–8% | Typical recreational |
| <6% | Efficient |
| >8% | May indicate excessive bounce |

#### Power (W)

Running power from watch (estimated, not direct measurement).

- Useful for comparing efforts on hills vs flat
- Track trends rather than absolute values
- Coros uses Form Power, Air Power; different brands use different algorithms

### Coros-Specific Metrics (when available)

| Metric | Description | Notes |
|--------|-------------|-------|
| Form Power | Composite running efficiency | Higher = more efficient |
| Impact Loading Rate | Force absorption rate | High values may indicate injury risk |
| Leg Spring Stiffness | Elastic energy return | Higher = stiffer, more rebound |

## Lap Analysis

- **Consistent lap times** → Good pacing
- **Positive split** (slower later) → Common in long runs; may indicate fatigue or heat
- **Negative split** (faster later) → Often ideal for races
- **Large lap-to-lap variance** → Check for stops, terrain changes, or pacing issues

## Injury Correlation

| Metric | Potential Concern |
|--------|-------------------|
| High impact loading rate | Consider softer surfaces, reduce intensity |
| Increasing stance time during run | Fatigue; consider shortening run or adding walk breaks |
| Asymmetric stance balance | May indicate imbalance; cross-train, strengthen |
| Sudden drop in cadence | Fatigue or pain; stop if persistent |

## Integration with health/profile.md

When interpreting runs:

1. Check **Injuries & Limitations** — avoid recommending intensity that conflicts
2. Cross-reference **Resting Heart Rate** — low RHR + high run HR = good fitness
3. Use **Target Daily Calories** — running burns ~60–80 cal/km depending on weight
4. Consider **Activity Level** — adjust weekly volume recommendations

## References

- `references/exercise.md` — Heart rate zones, training principles, injury considerations
- `references/apple-health.md` — Cross-reference with Apple Health workout data
