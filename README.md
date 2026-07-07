# ARC STUDIO ENGINE – AEC/MEP SYNTHESIS

A single‑click building generator that creates multi‑disciplinary architectural designs with coordinated MEP (Mechanical, Electrical, Plumbing, Fire Protection, Lighting/Data) systems. Visualise floor plans in 2D SVG and explore interactive 3D models – all inside a Streamlit web app.

![AEC/MEP Studio Screenshot](https://via.placeholder.com/800x400?text=ARC+Studio+Screenshot)

## Features

- **Multiple building typologies**  
  Residential (Apartment, Villa, Townhouse), Commercial (Office, Retail), Industrial (Factory, Warehouse), Healthcare (Hospital, Clinic), Education (School, University), and Hospitality (Hotel, Restaurant).

- **Full MEP coordination**  
  Five integrated systems visualised with distinct colours and line styles:
  - HVAC (solid gold)
  - Electrical (dashed blue)
  - Plumbing (dotted green)
  - Fire Protection (dash‑dot red)
  - Lighting/Data (dashed purple)

- **Smart floor plan generation**  
  Automatic central corridor and stair/elevator cores for multi‑storey buildings. Room areas are calculated and displayed on plans.

- **Interactive 3D model**  
  Rotate, zoom, and pan the extruded 3D view with floor slabs, columns, and MEP risers.

- **Design comparison**  
  Generate a second variant and compare areas, column counts, costs, and room totals side‑by‑side.

- **Rough cost estimation**  
  Based on building category, total area, and HVAC system.

- **Extensible configuration**  
  Adjust floors, area, room count, and HVAC type from the sidebar. MEP layers can be toggled on/off.

## Installation

1. **Clone this repository** (or download the files).
2. Install the required dependencies:

```bash
pip install streamlit plotly
