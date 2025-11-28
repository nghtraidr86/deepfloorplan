# Automated Floor Plan Measurement System

**Extension to Deep Floor Plan Recognition** - Adds automated measurement capabilities to the DeepFloorPlan project.

## 🎯 Overview

This extension adds comprehensive automated measurement capabilities to the Deep Floor Plan Recognition system. It can automatically:

- **Calculate room areas** in both square meters and square feet
- **Measure room dimensions** (width, length, perimeter)
- **Identify room types** (bedroom, bathroom, living room, etc.)
- **Convert pixels to real-world units** with calibrated scale
- **Generate detailed reports** in JSON and CSV formats
- **Visualize measurements** on floor plans with annotations
- **Process batches** of floor plans efficiently

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_measurement.txt
```

### 2. Download Pretrained Model

Download the pretrained model from the link in `pretrained/download_links.txt` and extract it to the `pretrained/` directory.

### 3. Run Measurement Demo

```bash
python demo_measure.py --im_path=./demo/45765448.jpg --scale=20.0
```

This will:
- Detect floor plan elements (rooms, walls, doors)
- Calculate all room measurements
- Display annotated floor plan
- Save results to `./measurements/`

## 📊 Features

### Measurement Capabilities

| Feature | Description | Output |
|---------|-------------|--------|
| **Room Area** | Calculates area of each room | m², sqft |
| **Dimensions** | Width, length, perimeter | meters, feet |
| **Room Type** | Identifies room types | Bedroom, Bathroom, etc. |
| **Scale Calibration** | Convert pixels to real units | Customizable |
| **Batch Processing** | Process multiple floor plans | CSV + JSON reports |
| **Visualization** | Annotated floor plans | PNG images |

### Example Output

```
================================================================================
FLOOR PLAN MEASUREMENT REPORT
================================================================================

Scale: 20.0 pixels per meter

Room                           Type                      Area (m²)    Area (sqft)  Dimensions (m)
--------------------------------------------------------------------------------
Room 1                         Bedroom                   15.25        164.13       3.8 x 4.2
Room 2                         Bathroom/Washroom         4.50         48.44        2.0 x 2.3
Room 3                         Living Room/Kitchen       28.75        309.42       5.5 x 5.5
--------------------------------------------------------------------------------

TOTAL FLOOR AREA:              48.50 m² (522.00 sqft)
================================================================================
```

## 📁 New Files

| File | Purpose |
|------|---------|
| `measure.py` | Core measurement module |
| `demo_measure.py` | Single floor plan measurement demo |
| `batch_measure.py` | Batch processing script |
| `calibrate_scale.py` | Interactive scale calibration tool |
| `test_measurements.py` | Unit tests for validation |
| `MEASUREMENT_GUIDE.md` | Detailed usage documentation |
| `SETUP_AND_TEST.md` | Setup and testing guide |
| `requirements_measurement.txt` | Python dependencies |

## 🔧 Usage Examples

### Measure Single Floor Plan

```bash
python demo_measure.py \
    --im_path=./demo/45765448.jpg \
    --scale=20.0 \
    --output_dir=./results \
    --save_json
```

### Calibrate Scale

```bash
# Interactive calibration
python calibrate_scale.py \
    --im_path=./demo/45765448.jpg \
    --method=manual \
    --reference_meters=5.0
```

Click two points on a known distance (e.g., a 5-meter wall) to calibrate.

### Batch Process Multiple Floor Plans

```bash
python batch_measure.py \
    --input_dir=./my_floorplans \
    --output_dir=./batch_results \
    --scale=25.0 \
    --pattern="*.jpg"
```

### Use as Python Library

```python
from measure import FloorPlanMeasurement
import numpy as np

# Initialize with scale
measurer = FloorPlanMeasurement(pixels_per_meter=20.0)

# Measure rooms (floorplan is your segmented image)
measurements = measurer.measure_room_areas(floorplan)

# Print report
measurer.print_report()

# Get total area
total = measurer.get_total_area()
print(f"Total: {total['total_area_m2']} m²")

# Save JSON report
measurer.generate_report('measurements.json')

# Create visualization
annotated_image = measurer.visualize_measurements(
    image, floorplan,
    show_labels=True,
    show_dimensions=True,
    show_areas=True
)
```

## 🎯 Improving Accuracy

### 1. Calibrate Scale Properly

The most important factor for accuracy is correct scale calibration:

```python
from measure import calibrate_scale_from_reference

# If you know a 5-meter wall is 100 pixels:
scale = calibrate_scale_from_reference(
    reference_length_pixels=100,
    reference_length_meters=5.0
)
# Returns: 20.0 pixels per meter
```

### 2. Use High-Quality Images

- Minimum resolution: 512x512 pixels
- Prefer 1024x1024 or higher
- Clear, high-contrast floor plans work best

### 3. Run Post-Processing First

For better room boundary detection:

```bash
# 1. Generate predictions
python main.py --phase=Test

# 2. Post-process
python postprocess.py --result_dir=./out

# 3. Measure
python demo_measure.py --im_path=./out/post/myfloorplan.png
```

## 📈 Accuracy Validation

Run the test suite to validate measurement accuracy:

```bash
python test_measurements.py
```

This runs comprehensive unit tests including:
- Scale calibration accuracy
- Unit conversion validation
- Room area calculation precision
- Multi-room detection
- Known ground-truth validation

Expected accuracy: **< 5% error** with properly calibrated scale

## 🔬 Technical Details

### Measurement Algorithm

1. **Segmentation**: Neural network segments floor plan into room types
2. **Connected Components**: Identifies individual room instances
3. **Contour Analysis**: Calculates precise boundaries
4. **Area Calculation**: Counts pixels within each room
5. **Dimension Extraction**: Computes bounding box dimensions
6. **Perimeter Calculation**: Uses contour arc length
7. **Scale Conversion**: Applies calibrated scale factor

### Room Type Detection

The system recognizes:
- Bedroom (ID: 4)
- Bathroom/Washroom (ID: 2)
- Living Room/Kitchen/Dining Room (ID: 3)
- Closet (ID: 1)
- Hall (ID: 5)
- Balcony (ID: 6)
- Walls (ID: 10)
- Doors & Windows (ID: 9)

### Scale Calibration Methods

1. **Manual Interactive**: Click two points on known distance
2. **Programmatic**: Provide pixel and meter values
3. **OCR-based**: Auto-detect scale from text (experimental)
4. **Scale Bar**: Auto-detect graphical scale bars (experimental)

## 📊 Output Formats

### JSON Report

```json
{
  "scale": {
    "pixels_per_meter": 20.0
  },
  "rooms": {
    "room_1": {
      "room_type": "Bedroom",
      "area_m2": 15.25,
      "area_sqft": 164.13,
      "width_m": 3.8,
      "height_m": 4.2,
      "perimeter_m": 16.0
    }
  },
  "summary": {
    "total_rooms": 3,
    "total_area": {
      "total_area_m2": 48.50,
      "total_area_sqft": 522.00
    }
  }
}
```

### CSV Summary (Batch Processing)

| Filename | Total Rooms | Total Area (m²) | Bedrooms | Bathrooms |
|----------|-------------|-----------------|----------|-----------|
| plan_01  | 4           | 85.5            | 2        | 1         |
| plan_02  | 3           | 62.3            | 1        | 1         |

### Visualization Images

- Original floor plan
- Detected segmentation (color-coded)
- Annotated with measurements
- Side-by-side comparison

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Measurements too large/small | Calibrate scale properly |
| Rooms not detected | Run post-processing first |
| Dependencies missing | `pip install -r requirements_measurement.txt` |
| Model not found | Download from `pretrained/download_links.txt` |
| Python 3 compatibility | See `SETUP_AND_TEST.md` for migration guide |

## 📚 Documentation

- **[MEASUREMENT_GUIDE.md](MEASUREMENT_GUIDE.md)** - Comprehensive usage guide
- **[SETUP_AND_TEST.md](SETUP_AND_TEST.md)** - Setup and testing instructions
- **Original README** - See below for original DeepFloorPlan docs

## 🔗 Integration

This measurement system seamlessly integrates with the existing DeepFloorPlan workflow:

```
Input Image → Neural Network → Segmentation → Post-Process → Measurement → Report
```

You can use the existing training, testing, and post-processing scripts, then add measurement as the final step.

## 📝 Citation

If you use this measurement extension, please cite the original DeepFloorPlan paper:

```bibtex
@InProceedings{zlzeng2019deepfloor,
    author = {Zhiliang ZENG, Xianzhi LI, Ying Kin Yu, and Chi-Wing Fu},
    title = {Deep Floor Plan Recognition using a Multi-task Network with Room-boundary-Guided Attention},
    booktitle = {IEEE International Conference on Computer Vision (ICCV)},
    year = {2019}
}
```

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Better scale auto-detection
- Support for irregular room shapes
- 3D measurement integration
- Real-time measurement
- Mobile app integration

## 📄 License

This extension follows the same license as the original DeepFloorPlan project (see LICENSE file).

---

# Original DeepFloorPlan README

## Deep Floor Plan Recognition using a Multi-task Network with Room-boundary-Guided Attention
By Zhiliang ZENG, Xianzhi LI, Ying Kin Yu, and Chi-Wing Fu

[2021/07/26: updated download link]

[2019/08/28: updated train/test/score code & dataset]

[2019/07/29: updated demo code & pretrained model]

## Introduction

This repository contains the code & annotation data for our ICCV 2019 paper: ['Deep Floor Plan Recognition Using a Multi-Task Network with Room-Boundary-Guided Attention'](https://arxiv.org/abs/1908.11025). In this paper, we present a new method for recognizing floor plan elements by exploring the spatial relationship between floor plan elements, model a hierarchy of floor plan elements, and design a multi-task network to learn to recognize room-boundary and room-type elements in floor plans.

## Requirements

- Please install OpenCV
- Please install Python 2.7
- Please install tensorflow-gpu

Our code has been tested by using tensorflow-gpu==1.10.1 & OpenCV==3.1.0. We used Nvidia Titan Xp GPU with CUDA 9.0 installed.

## Python packages

- [numpy]
- [scipy]
- [Pillow]
- [matplotlib]

## Data

We share all our annotations and train-test split file [here](https://mycuhk-my.sharepoint.com/:f:/g/personal/1155052510_link_cuhk_edu_hk/EseSIeHQgPxArPlNpGdVp38BIjUg70jMiAO-w4f3s8B_dg?e=UXKbYO). Or download the annotation using the link in file "dataset/download_links.txt". The additional round plan is included in the annotations.

Our annotations are saved as png format. The name with suffixes "\_wall.png", "\_close.png" and "\_room.png" are denoted "wall", "door & window" and "room types" label, respectively. We used these labels to train our multi-task network.

The name with suffixes "\_close_wall.png" is the combination of "wall", "door & window" label. We don't use this label in our paper, but maybe useful for other tasks.

The name with suffixes "\_multi.png" is the combination of all the labels. We used this kind of label to retrain the general segmentation network.

We also provide our training data on R3D dataset in "tfrecord" format, which can improve the loading speed during training.

To create the "tfrecord" training set, please refer to the example code in "utils/create_tfrecord.py"

All the raw floor plan image please refer to the following two links:

- R2V: <https://github.com/art-programmer/FloorplanTransformation.git>
- R3D: <http://www.cs.toronto.edu/~fidler/projects/rent3D.html>

## Usage

To use our demo code, please first download the pretrained model, find the link in "pretrained/download_links.txt" file, unzip and put it into "pretrained" folder, then run

```bash
python demo.py --im_path=./demo/45719584.jpg
```

To train the network, simply run

```bash
python main.py --pharse=Train
```

Run the following command to generate network outputs, all results are saved as png format.

```bash
python main.py --pharse=Test
```

To compute the evaluation metrics, please first inference the results, then simply run

```bash
python scores.py --dataset=R3D
```

To use our post-processing method, please first inference the results, then simply run

```bash
python postprocess.py
```

or

```bash
python postprocess.py --result_dir=./[result_folder_path]
```

## Citation

If you find our work useful in your research, please consider citing:

---

```bibtex
@InProceedings{zlzeng2019deepfloor,
    author = {Zhiliang ZENG, Xianzhi LI, Ying Kin Yu, and Chi-Wing Fu},
    title = {Deep Floor Plan Recognition using a Multi-task Network with Room-boundary-Guided Attention},
    booktitle = {IEEE International Conference on Computer Vision (ICCV)},
    year = {2019}
}
```

---
