# Industrial HMI Mockup Set

## Sources

### Editable Figma Templates Used as Base Layouts

1. **Themesberg Figma Admin Dashboard Template** — grid-based dashboard with cards and charts
2. **Sneat Free Figma Admin Dashboard UI Kit** — modular components and dark theme variant

### Industrial Visual References

1. **Siemens HMI Template Suite** — standard industrial operator panel layouts
2. **Ignition SCADA Public Demo** — real-world SCADA dashboard with live data widgets
3. **FUXA Open-Source SCADA** — SVG-based synoptic screens with gauges and valves
4. **JointJS SCADA/HMI Demo** — interactive pipeline and tank level diagrams

## Mockup Set (8 screens)


| #   | Screen Name                 | File                                     | Industrial Use Case                                                                                                           | Complexity  | Rationale                                                                                                                                    |
| --- | --------------------------- | ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Equipment Status Dashboard  | `mockups/png/01-equipment-status.png`    | Displays the operational state of key machines on a production line — running, idle, faulted, maintenance                     | Simple      | Covers the most common HMI view: a grid of status cards with color-coded indicators. Good for testing basic card layout generation.          |
| 2   | Alarm & Event Screen        | `mockups/png/02-alarm-event.png`         | Lists active alarms and recent events with severity levels, timestamps, and acknowledgment buttons                            | Simple      | Tabular layout with colored severity badges. Tests table rendering accuracy, row styling, and action buttons.                                |
| 3   | Real-Time Trend Monitor     | `mockups/png/03-trend-monitor.png`       | Shows time-series plots for temperature, pressure, and flow rate sensors over a configurable time window                      | Medium      | Contains line chart placeholders, axis labels, legend, and time-range selector. Tests chart area reproduction and legend alignment.          |
| 4   | Operator Control Panel      | `mockups/png/04-operator-panel.png`      | Manual control interface for a mixing unit — start/stop buttons, setpoint inputs, mode selector, and live readouts            | Medium      | Mix of buttons, numeric inputs, dropdown selectors, and live value displays. Good for testing interactive element generation.                |
| 5   | Production Line Overview    | `mockups/png/05-production-overview.png` | Bird's-eye view of a bottling line showing conveyor segments, machine states, throughput counters, and OEE metrics            | Medium      | Complex multi-section layout with a horizontal process flow diagram, KPI cards, and a progress bar. Tests spatial arrangement.               |
| 6   | Tank Farm Synoptic          | `mockups/png/06-tank-synoptic.png`       | Graphic depiction of four storage tanks with level indicators, valves, pipe connections, and pump states                      | Medium–Hard | SVG-style graphic elements (tank shapes, pipe lines, valve symbols). A challenging test for reproducing non-rectangular visual primitives.   |
| 7   | Energy Monitoring Dashboard | `mockups/png/07-energy-dashboard.png`    | Power consumption breakdown by facility zone with gauge charts, bar charts, and daily/weekly comparison cards                 | Medium–Hard | Dense layout with multiple chart types, KPI summary row, and sub-navigation tabs. Tests multi-chart composition.                             |
| 8   | Batch Recipe Management     | `mockups/png/08-batch-recipe.png`        | Step-sequence display for a pharmaceutical batch process — recipe steps, parameter table, status timeline, and phase controls | Hard        | Combines a vertical step-list, parameter data table, horizontal timeline, and modal-like detail panel. The most structurally complex screen. |


## Design Conventions Applied

All mockups follow common industrial HMI conventions:

- **Dark background** (#1E1E2E or similar) to reduce eye fatigue in control rooms
- **Color coding:** green = normal/running, yellow = warning, red = alarm/fault, blue = maintenance/info, gray = inactive/off
- **High contrast text** on dark backgrounds (white or light gray)
- **Monospace or tabular numerals** for live data values
- **Consistent card-based layout** with 8px / 16px spacing grid
- **Status indicators** using filled circles, badges, or colored borders
- **Minimal decorative elements** — function over aesthetics, following ISA-101 HMI design principles

