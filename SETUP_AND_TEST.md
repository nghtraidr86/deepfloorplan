# Setup and Testing Guide for Floor Plan Measurement

## Prerequisites

### 1. Python Dependencies

```bash
pip install numpy scipy tensorflow-gpu opencv-python matplotlib
```

**Note**: This project was originally developed with:
- Python 2.7 (but should work with Python 3.x with minor modifications)
- TensorFlow 1.10.1
- OpenCV 3.1.0

For Python 3 compatibility, you may need to:
- Change `xrange` to `range`
- Change `.iteritems()` to `.items()`
- Update `scipy.misc.imread` and `imsave` to use `imageio` or `PIL`

### 2. Download Pretrained Model

Download the pretrained model from the link in `/pretrained/download_links.txt`:

```bash
cd pretrained
# Download and extract the model files
# The model should include:
# - pretrained_r3d.meta
# - pretrained_r3d.index
# - pretrained_r3d.data-00000-of-00001
```

### 3. GPU Setup (Optional but Recommended)

For faster processing:
- Install CUDA 9.0 or later
- Install cuDNN
- Ensure `tensorflow-gpu` is installed

## Quick Test

### Test 1: Basic Measurement Demo

```bash
python demo_measure.py --im_path=./demo/45765448.jpg --scale=20.0
```

**Expected output:**
- Console report showing room measurements
- Three visualization windows
- Files saved in `./measurements/` directory:
  - `45765448_floorplan.png` - Color-coded floor plan
  - `45765448_measured.png` - Annotated with measurements
  - `45765448_comparison.png` - Side-by-side comparison

### Test 2: Calibrate Scale

```bash
python calibrate_scale.py --im_path=./demo/45765448.jpg --method=manual --reference_meters=5.0
```

**Expected interaction:**
- Window opens showing the floor plan
- Click two points representing a known distance
- Press 'q' when done
- Console shows calculated scale factor

### Test 3: Batch Processing

```bash
python batch_measure.py --input_dir=./demo --output_dir=./batch_test --scale=20.0
```

**Expected output:**
- Processes all images in demo folder
- Creates individual reports for each floor plan
- Generates summary CSV file
- Creates combined JSON report

## Troubleshooting

### Issue: "No module named 'tensorflow'"

**Solution:**
```bash
pip install tensorflow-gpu==1.10.1
# or for CPU only:
pip install tensorflow==1.10.1
```

### Issue: scipy.misc.imread deprecated

**Solution for Python 3:**

Edit the import statements in the files:

```python
# Replace:
from scipy.misc import imread, imsave, imresize

# With:
from imageio import imread, imwrite as imsave
from scipy.ndimage import zoom

def imresize(img, size):
    if len(size) == 3:
        size = size[:2]
    h, w = size
    zoom_h = h / img.shape[0]
    zoom_w = w / img.shape[1]
    if len(img.shape) == 3:
        return zoom(img, (zoom_h, zoom_w, 1), order=1)
    return zoom(img, (zoom_h, zoom_w), order=1)
```

Then:
```bash
pip install imageio
```

### Issue: Model files not found

**Solution:**
1. Check `/pretrained/download_links.txt` for download URL
2. Download and extract the model
3. Ensure files are in the `/pretrained/` directory
4. Verify file names match: `pretrained_r3d.*`

### Issue: CUDA errors

**Solution:**
```bash
# Force CPU mode
export CUDA_VISIBLE_DEVICES=''
python demo_measure.py --im_path=./demo/45765448.jpg --scale=20.0
```

### Issue: Measurements seem inaccurate

**Solution:**
1. Calibrate the scale properly using `calibrate_scale.py`
2. Use a known reference dimension from your floor plan
3. Verify the calibration by measuring multiple known features

### Issue: "iteritems" not found (Python 3)

**Solution:**
Replace `.iteritems()` with `.items()` in the code files.

## Validating Accuracy

### Method 1: Manual Verification

1. Run measurement on a floor plan with known dimensions
2. Compare output measurements with ground truth
3. Calculate error percentage

```python
# Example validation script
from measure import FloorPlanMeasurement
import numpy as np

# Load your segmented floor plan
floorplan = np.load('test_floorplan.npy')

# Use calibrated scale
measurer = FloorPlanMeasurement(pixels_per_meter=25.0)
measurements = measurer.measure_room_areas(floorplan)

# Compare with ground truth
ground_truth_area = 20.0  # m²
measured_area = measurements['room_1']['area_m2']
error_percent = abs(measured_area - ground_truth_area) / ground_truth_area * 100

print(f"Ground truth: {ground_truth_area} m²")
print(f"Measured: {measured_area} m²")
print(f"Error: {error_percent:.2f}%")
```

### Method 2: Cross-Validation

Test on multiple floor plans with different scales and room types:

```bash
# Test on all demo images
for img in ./demo/*.jpg; do
    echo "Testing $img"
    python demo_measure.py --im_path="$img" --scale=20.0 --save_json
done
```

### Method 3: Unit Tests

Create automated tests:

```python
# test_measurements.py
import unittest
import numpy as np
from measure import FloorPlanMeasurement

class TestMeasurements(unittest.TestCase):

    def test_scale_conversion(self):
        measurer = FloorPlanMeasurement(pixels_per_meter=20.0)
        meters = measurer.pixels_to_meters(100)
        self.assertAlmostEqual(meters, 5.0, places=2)

    def test_area_conversion(self):
        measurer = FloorPlanMeasurement(pixels_per_meter=20.0)
        sqm = measurer.pixels_to_sqmeters(400)
        self.assertAlmostEqual(sqm, 1.0, places=2)

    def test_simple_room(self):
        measurer = FloorPlanMeasurement(pixels_per_meter=10.0)

        # Create simple 100x100 pixel room (should be 10x10 meters = 100 m²)
        floorplan = np.zeros((200, 200), dtype=np.uint8)
        floorplan[50:150, 50:150] = 4  # Bedroom

        measurements = measurer.measure_room_areas(floorplan)

        self.assertEqual(len(measurements), 1)
        room = list(measurements.values())[0]

        # Allow some tolerance due to boundary effects
        self.assertAlmostEqual(room['area_m2'], 100.0, delta=5.0)

if __name__ == '__main__':
    unittest.main()
```

Run tests:
```bash
python test_measurements.py
```

## Performance Benchmarks

Expected processing times (on Nvidia Titan Xp):

- Single floor plan inference: ~0.1-0.3 seconds
- Measurement calculation: ~0.01-0.05 seconds
- Visualization generation: ~0.05-0.1 seconds

**Total time per floor plan: ~0.2-0.5 seconds**

For batch processing:
- 100 floor plans: ~20-50 seconds
- 1000 floor plans: ~3-8 minutes

## Integration Examples

### Example 1: Web API

```python
from flask import Flask, request, jsonify
from measure import FloorPlanMeasurement
import numpy as np

app = Flask(__name__)

@app.route('/measure', methods=['POST'])
def measure_floorplan():
    # Receive floor plan image
    file = request.files['floorplan']

    # Run inference (your existing code)
    floorplan_segmentation = run_inference(file)

    # Measure
    measurer = FloorPlanMeasurement(pixels_per_meter=20.0)
    measurements = measurer.measure_room_areas(floorplan_segmentation)

    # Return JSON
    return jsonify(measurer.generate_report())

if __name__ == '__main__':
    app.run(port=5000)
```

### Example 2: Command Line Tool

```python
#!/usr/bin/env python
# measure_cli.py

import sys
from measure import FloorPlanMeasurement
import numpy as np

def main():
    if len(sys.argv) < 3:
        print("Usage: measure_cli.py <floorplan.npy> <scale>")
        sys.exit(1)

    floorplan_path = sys.argv[1]
    scale = float(sys.argv[2])

    floorplan = np.load(floorplan_path)
    measurer = FloorPlanMeasurement(pixels_per_meter=scale)
    measurer.measure_room_areas(floorplan)
    measurer.print_report()

if __name__ == '__main__':
    main()
```

## Best Practices

1. **Always calibrate scale** for each set of floor plans from the same source
2. **Use post-processing** before measurement for better accuracy
3. **Validate results** on a sample before batch processing
4. **Save calibration settings** for reproducibility
5. **Use high-resolution images** (minimum 512x512, prefer 1024x1024 or higher)

## Next Steps

1. Download the pretrained model
2. Run the quick tests above
3. Calibrate scale for your specific floor plans
4. Process your floor plan dataset
5. Validate and iterate

For detailed usage instructions, see `MEASUREMENT_GUIDE.md`.
