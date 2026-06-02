# Member D Summary — Q4 Network Relationships

- Nodes (employees): 35
- Edges (co-occurrence relationships): 114
- Network density: 0.1916
- Communities detected: 5
- Total co-occurrence events: 134
- After-hours events: 42
- Night events (0-5 AM): 6
- Unassigned vehicles: [np.int64(101), np.int64(104), np.int64(105), np.int64(106), np.int64(107)]
- Top betweenness employee: Isak Baza
- Q4 figures: 8

## Key Findings

1. The GPS co-occurrence network reveals clear departmental clustering at work locations during business hours.
2. After-hours gatherings at cafe/restaurant locations suggest informal social connections, potentially related to surprise party planning.
3. Executive members show low-frequency, long-duration co-occurrence patterns distinct from routine work interactions.
4. Unassigned vehicles (101/104/105/106/107) systematically co-occur with employee vehicles, especially at night — warranting further investigation as potential POK surveillance.
5. Security personnel form a dense sub-network reflecting shift handover patterns; high centrality here is expected and not inherently suspicious.

## Limitations

- Loyalty data has date-only precision; same-day same-location transaction validation provides weak evidence only.
- GPS co-occurrence (100m proximity) does not guarantee face-to-face meetings.
- Truck drivers without assigned vehicles are not directly observable via GPS co-occurrence; indirect inference needed.
- Community detection results should be interpreted as exploratory patterns, not definitive social groups.
