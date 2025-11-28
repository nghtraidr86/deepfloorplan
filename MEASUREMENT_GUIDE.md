# Floor Plan Measurement Guide

This guide explains how to use the automated floor plan measurement capabilities.

## Features

The automated measurement system provides:

- **Room Area Calculation**: Accurate area measurements in both square meters and square feet
- **Room Dimensions**: Width, length, and perimeter for each room
- **Room Type Detection**: Identifies bedrooms, bathrooms, living rooms, etc.
- **Pixel-to-Real-World Conversion**: Converts pixel measurements to meters/feet
- **Visualization**: Annotated floor plans with measurement overlays
- **Batch Processing**: Process multiple floor plans at once
- **Export Options**: JSON reports and CSV summaries

## Quick Start

### 1. Measure a Single Floor Plan

```bash
python demo_measure.py --im_path=./demo/45765448.jpg --scale=20.0
```

**Parameters:**
- `--im_path`: Path to floor plan image
- `--scale`: Pixels per meter conversion (default: 20.0)
- `--output_dir`: Where to save results (default: ./measurements)
- `--save_json`: Save JSON measurement report
- `--save_viz`: Save visualization images

**Output:**
- Console report with all measurements
- Annotated floor plan image
- JSON measurement data (if `--save_json` used)

### 2. Batch Process Multiple Floor Plans

```bash
python batch_measure.py --input_dir=./demo --output_dir=./batch_measurements --scale=20.0
```

**Parameters:**
- `--input_dir`: Directory containing floor plan images
- `--output_dir`: Where to save results
- `--scale`: Pixels per meter conversion
- `--pattern`: File pattern to match (default: *.jpg)

**Output:**
- Individual JSON reports for each floor plan
- Annotated images for each floor plan
- Combined CSV summary
- Combined JSON report

## Scale Calibration

**IMPORTANT**: The accuracy of measurements depends on the correct scale factor.

### Method 1: Calculate from Known Dimensions

If you know a real-world dimension from the floor plan:

```python
from measure import calibrate_scale_from_reference

# Example: A wall that is 150 pixels long is actually 5 meters
pixels_per_meter = calibrate_scale_from_reference(
    reference_length_pixels=150,
    reference_length_meters=5.0
)

print(f"Use scale: {pixels_per_meter}")
# Output: Use scale: 30.0
```

Then use this scale in your measurements:

```bash
python demo_measure.py --im_path=./demo/myplan.jpg --scale=30.0
```

### Method 2: Common Floor Plan Scales

Typical architectural floor plan scales:

| Scale Ratio | Pixels per Meter (at 300 DPI) | Pixels per Meter (at 150 DPI) |
|-------------|-------------------------------|-------------------------------|
| 1:50        | 236.2                         | 118.1                         |
| 1:100       | 118.1                         | 59.1                          |
| 1:200       | 59.1                          | 29.5                          |

### Method 3: Interactive Calibration

Create a calibration script:

```python
from measure import FloorPlanMeasurement
import cv2
import numpy as np

# Load your floor plan
image = cv2.imread('myfloorplan.jpg')

# Manually measure a known feature in the image (use image viewer or cv2)
# Example: A 5-meter wall appears as 100 pixels
known_pixels = 100
known_meters = 5.0

scale = known_pixels / known_meters
print(f"Calibrated scale: {scale} pixels per meter")

# Use this scale
measurer = FloorPlanMeasurement(pixels_per_meter=scale)
```

## Understanding the Output

### Console Report

```
================================================================================
FLOOR PLAN MEASUREMENT REPORT
================================================================================

Scale: 20.0 pixels per meter

Room                           Type                      Area (m²)    Area (sqft)  Dimensions (m)
--------------------------------------------------------------------------------
Room 1                         Bedroom                   12.50        134.55       3.5 x 4.0
Room 2                         Bathroom/Washroom         6.25         67.28        2.5 x 2.5
Room 3                         Living Room/Kitchen       25.00        269.10       5.0 x 5.0
--------------------------------------------------------------------------------

SUMMARY BY ROOM TYPE:
--------------------------------------------------------------------------------
Bathroom/Washroom              Count: 1   Total Area: 6.25 m² (67.28 sqft)
Bedroom                        Count: 1   Total Area: 12.50 m² (134.55 sqft)
Living Room/Kitchen            Count: 1   Total Area: 25.00 m² (269.10 sqft)
--------------------------------------------------------------------------------
TOTAL FLOOR AREA:              43.75 m² (470.93 sqft)
================================================================================
```

### JSON Report Structure

```json
{
  "scale": {
    "pixels_per_meter": 20.0,
    "description": "1 meter = 20.0 pixels"
  },
  "rooms": {
    "room_1": {
      "room_id": 1,
      "room_type": "Bedroom",
      "room_type_id": 4,
      "area_m2": 12.50,
      "area_sqft": 134.55,
      "width_m": 3.5,
      "height_m": 4.0,
      "perimeter_m": 15.0,
      "bbox": {
        "min_x": 100,
        "min_y": 50,
        "max_x": 170,
        "max_y": 130
      },
      "centroid": {
        "x": 135,
        "y": 90
      }
    }
  },
  "summary": {
    "total_rooms": 3,
    "total_area": {
      "total_area_m2": 43.75,
      "total_area_sqft": 470.93
    },
    "by_room_type": {
      "Bedroom": {
        "count": 1,
        "total_area_m2": 12.50,
        "total_area_sqft": 134.55
      }
    }
  }
}
```

## Improving Measurement Accuracy

### 1. Use High-Quality Images
- Use high-resolution floor plans (minimum 512x512 pixels)
- Ensure images are clear and not blurry
- Avoid compressed or low-quality JPEGs

### 2. Calibrate Scale Properly
- Always calibrate using a known reference dimension
- Use the largest reference dimension available for better accuracy
- Verify the scale with multiple reference points if possible

### 3. Clean Floor Plans Work Best
- Floor plans with clear room boundaries
- Minimal text and annotations overlaying the plan
- High contrast between rooms, walls, and background

### 4. Post-Process Results
- Run post-processing before measurement for better accuracy:

```bash
# First, run the model to get predictions
python main.py --phase=Test

# Post-process the results
python postprocess.py --result_dir=./out

# Then measure the post-processed results
python demo_measure.py --im_path=./out/post/myfloorplan.png --scale=20.0
```

## Programming API

### Basic Usage

```python
from measure import FloorPlanMeasurement
import numpy as np

# Create measurer with scale
measurer = FloorPlanMeasurement(pixels_per_meter=20.0)

# Assuming you have a segmented floor plan (from the neural network)
# where each pixel has a room type label (0-10)
floorplan_segmentation = np.array(...)  # Your segmented floor plan

# Measure all rooms
measurements = measurer.measure_room_areas(floorplan_segmentation)

# Print report
measurer.print_report()

# Get total area
total = measurer.get_total_area()
print(f"Total area: {total['total_area_m2']} m²")

# Get summary by room type
summary = measurer.get_summary_by_room_type()

# Generate JSON report
report = measurer.generate_report(output_path='measurements.json')

# Create visualization
import cv2
image = cv2.imread('floorplan.jpg')
annotated = measurer.visualize_measurements(
    image,
    floorplan_segmentation,
    show_labels=True,
    show_dimensions=True,
    show_areas=True
)
cv2.imwrite('annotated.png', annotated)
```

### Advanced Usage

```python
# Change scale after initialization
measurer.set_scale(30.0)

# Manual conversion utilities
meters = measurer.pixels_to_meters(100)  # Convert 100 pixels to meters
sqm = measurer.pixels_to_sqmeters(1000)  # Convert 1000 pixel² to m²

# Access individual room measurements
for room_id, room_data in measurer.measurements.items():
    print(f"{room_id}: {room_data['room_type']}")
    print(f"  Area: {room_data['area_m2']} m²")
    print(f"  Dimensions: {room_data['width_m']}m x {room_data['height_m']}m")
    print(f"  Perimeter: {room_data['perimeter_m']}m")
```

## Troubleshooting

### Problem: Measurements seem too large/small
**Solution**: Calibrate your scale properly. The default 20.0 pixels/meter is just an estimate.

### Problem: Rooms are not detected
**Solution**:
- Ensure the floor plan image is clear
- Run post-processing first
- Check if the neural network is detecting rooms properly

### Problem: Room boundaries are inaccurate
**Solution**:
- Use post-processing: `python postprocess.py`
- Ensure floor plan has clear wall boundaries
- Use higher quality input images

### Problem: Multiple rooms merged into one
**Solution**:
- Run post-processing which refines room regions
- Ensure walls are clearly visible in the original floor plan

## Room Type Labels

The system recognizes these room types:

| ID | Type |
|----|------|
| 0  | Background |
| 1  | Closet |
| 2  | Bathroom/Washroom |
| 3  | Living Room/Kitchen/Dining Room |
| 4  | Bedroom |
| 5  | Hall |
| 6  | Balcony |
| 9  | Door & Window |
| 10 | Wall |

## Examples

### Example 1: Measure Demo Floor Plan

```bash
python demo_measure.py \
    --im_path=./demo/45765448.jpg \
    --scale=20.0 \
    --output_dir=./my_measurements \
    --save_json
```

### Example 2: Batch Process with Custom Scale

```bash
python batch_measure.py \
    --input_dir=./my_floorplans \
    --output_dir=./results \
    --scale=25.5 \
    --pattern="*.png"
```

### Example 3: Custom Python Script

```python
import cv2
import numpy as np
from measure import FloorPlanMeasurement, calibrate_scale_from_reference

# Calibrate scale
scale = calibrate_scale_from_reference(
    reference_length_pixels=200,
    reference_length_meters=10.0
)

# Initialize
measurer = FloorPlanMeasurement(pixels_per_meter=scale)

# Load your segmented floor plan
floorplan = np.load('segmented_floorplan.npy')

# Measure
measurements = measurer.measure_room_areas(floorplan)

# Export
measurer.generate_report('output.json')
measurer.print_report()
```

## Integration with Existing Workflow

The measurement module integrates seamlessly with the existing DeepFloorPlan workflow:

1. **Train/Test**: Use existing `main.py` to train or test the model
2. **Post-process**: Use `postprocess.py` to refine predictions
3. **Measure**: Use `demo_measure.py` or `batch_measure.py` to add measurements

This allows you to leverage the existing neural network for floor plan recognition and add automated measurements on top.
