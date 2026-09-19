# Workover Rig Scheduling Problem

## Background

You manage workover operations for a West Texas oil field in the Permian Basin near Midland, TX. Twenty wells need workover service. You have three workover rigs available. Each well is losing production every day it waits for service, and each rig must travel between wells (travel time depends on distance). Your goal is to schedule the rigs to minimize total production loss.

**Total production loss** = for each well, (daily production loss) x (number of days from now until that well's workover is complete).

## Rigs

All three rigs are currently at the field yard near Midland (31.9500, -102.1000). Each rig can service one well at a time. Once a rig finishes a well, it travels to the next well on its schedule.

| Rig | Starting Location | Daily Operating Cost |
|-----|-------------------|---------------------|
| Rig A | Field Yard (31.9500, -102.1000) | $15,000 |
| Rig B | Field Yard (31.9500, -102.1000) | $15,000 |
| Rig C | Field Yard (31.9500, -102.1000) | $15,000 |

## Wells Needing Service

Each well has a location (latitude, longitude), an estimated service duration (days), and a daily production loss (barrels/day lost while waiting AND during service).

| Well | Location (lat, lon) | Service Duration (days) | Daily Production Loss (bbl/day) | Oil Price: $70/bbl |
|------|---------------------|------------------------|---------------------------------|---------------------|
| W01 | (32.0659, -101.8950) | 3 | 120 | $8,400/day |
| W02 | (32.2688, -102.0146) | 2 | 85 | $5,950/day |
| W03 | (32.1674, -101.5876) | 4 | 200 | $14,000/day |
| W04 | (31.9935, -101.7926) | 1 | 45 | $3,150/day |
| W05 | (32.3558, -101.6730) | 5 | 310 | $21,700/day |
| W06 | (32.1529, -101.9634) | 2 | 95 | $6,650/day |
| W07 | (32.0514, -101.5022) | 3 | 150 | $10,500/day |
| W08 | (32.3848, -101.8609) | 2 | 70 | $4,900/day |
| W09 | (32.2399, -101.4168) | 4 | 260 | $18,200/day |
| W10 | (32.0949, -102.0488) | 1 | 55 | $3,850/day |
| W11 | (32.2109, -101.7242) | 3 | 175 | $12,250/day |
| W12 | (32.0225, -101.6218) | 2 | 110 | $7,700/day |
| W13 | (32.3123, -101.9292) | 3 | 130 | $9,100/day |
| W14 | (32.1239, -101.4510) | 2 | 190 | $13,300/day |
| W15 | (32.2399, -101.8438) | 4 | 220 | $15,400/day |
| W16 | (32.3123, -101.5364) | 1 | 80 | $5,600/day |
| W17 | (32.0225, -101.9975) | 2 | 65 | $4,550/day |
| W18 | (32.4138, -101.7584) | 3 | 145 | $10,150/day |
| W19 | (32.3558, -101.3826) | 5 | 280 | $19,600/day |
| W20 | (32.1529, -101.6388) | 2 | 135 | $9,450/day |

## Travel Times

Travel time between any two locations = (straight-line distance) / 30 mph, rounded up to the nearest half day. Rigs travel on existing lease roads, but straight-line distance is a reasonable approximation.

Use haversine distance between (lat, lon) pairs to compute miles. Rigs drive 30 mph for 8 hours per day.

**Formula:** Travel time (days) = ceiling( haversine_miles(loc1, loc2) / 30 / 8 * 2 ) / 2

## Assumptions

- A well continues to lose production from Day 0 until the workover is **completed** (arrival + service duration).
- All 20 wells need service starting now (Day 0). There is no option to skip a well.
- Rigs work every day (no days off).
- A rig cannot start a new well until the current well is fully serviced.
- Rigs are identical in capability.

## Your Task

Determine which wells each rig should service and in what order, to **minimize the total production lost** (in barrels) across all 20 wells.

Report:
1. The schedule for each rig (sequence of wells with arrival and completion times)
2. The total production loss in barrels
3. The total production loss in dollars (at $70/bbl)

## Data in CSV Format

```csv
well_id,lat,lon,service_days,daily_loss_bbl
W01,32.0659,-101.8950,3,120
W02,32.2688,-102.0146,2,85
W03,32.1674,-101.5876,4,200
W04,31.9935,-101.7926,1,45
W05,32.3558,-101.6730,5,310
W06,32.1529,-101.9634,2,95
W07,32.0514,-101.5022,3,150
W08,32.3848,-101.8609,2,70
W09,32.2399,-101.4168,4,260
W10,32.0949,-102.0488,1,55
W11,32.2109,-101.7242,3,175
W12,32.0225,-101.6218,2,110
W13,32.3123,-101.9292,3,130
W14,32.1239,-101.4510,2,190
W15,32.2399,-101.8438,4,220
W16,32.3123,-101.5364,1,80
W17,32.0225,-101.9975,2,65
W18,32.4138,-101.7584,3,145
W19,32.3558,-101.3826,5,280
W20,32.1529,-101.6388,2,135
```
