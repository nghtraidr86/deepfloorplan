# Quick Start: Measuring Floor Plans from Scaled PDFs

**Perfect for PDFs with scale markings!** 🎯

Since your PDFs have the scale marked on them, you can achieve **±5% accuracy** automatically.

## One-Time Setup (5 minutes)

### 1. Install Python packages:
```bash
pip install pdf2image pytesseract opencv-python numpy scipy matplotlib
```

### 2. Install system dependencies:

**Mac:**
```bash
brew install poppler tesseract
```

**Ubuntu/Linux:**
```bash
sudo apt-get install poppler-utils tesseract-ocr
```

**Windows:**
- Download Poppler: https://github.com/oschwartz10612/poppler-windows/releases/
- Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki

### 3. Download pretrained model:
- Open `pretrained/download_links.txt`
- Download and extract to `pretrained/` folder

## Measure a Single PDF (30 seconds)

### Method 1: Automatic (Easiest)

```bash
# Extract scale and convert PDF
python pdf_scale_extractor.py --pdf_path=your_plan.pdf --mode=auto --output_image=plan.png

# The tool will tell you the scale, for example: "Use: --scale=118.11"
# Copy that number and use it:

python demo_measure.py --im_path=plan.png --scale=118.11 --save_json
```

**Done!** Check the `measurements/` folder for:
- `plan_measured.png` - Annotated floor plan with measurements
- `plan_measurements.json` - All measurement data
- Console shows measurement report

### Method 2: Interactive (Most Accurate)

If your PDF has a **scale bar** (a line showing distance):

```bash
# Convert PDF and measure the scale bar
# Replace "10.0" with the length shown on your scale bar (in meters)
python pdf_scale_extractor.py \
    --pdf_path=your_plan.pdf \
    --mode=interactive \
    --scale_bar_length=10.0 \
    --output_image=plan.png

# Click start and end of the scale bar
# Tool will calculate exact scale

# Then measure
python demo_measure.py --im_path=plan.png --scale=<calculated_scale> --save_json
```

## Measure Many PDFs (Batch Processing)

If all your PDFs have the **same scale** (e.g., all are 1:100):

### Step 1: Find the scale from one PDF
```bash
python pdf_scale_extractor.py --pdf_path=sample.pdf --mode=auto
# Note the scale, e.g., 118.11 for 1:100 at 300 DPI
```

### Step 2: Convert all PDFs to images
```bash
# Create a folder for images
mkdir floor_plans_images

# Convert each PDF (replace with your PDF names or use a loop)
for pdf in *.pdf; do
    python pdf_scale_extractor.py \
        --pdf_path="$pdf" \
        --dpi=300 \
        --mode=auto \
        --output_image="floor_plans_images/$(basename $pdf .pdf).png"
done
```

### Step 3: Batch measure all images
```bash
python batch_measure.py \
    --input_dir=./floor_plans_images \
    --output_dir=./batch_results \
    --scale=118.11 \
    --pattern="*.png"
```

**Results:**
- Individual JSON files for each plan
- `summary.csv` - Spreadsheet with all measurements
- Annotated images showing measurements

## Understanding Your Results

### Console Output
```
Room                           Type                      Area (m²)    Area (sqft)
--------------------------------------------------------------------------------
Room 1                         Bedroom                   15.25        164.13
Room 2                         Bathroom/Washroom         4.50         48.44
Room 3                         Living Room/Kitchen       28.75        309.42
--------------------------------------------------------------------------------
TOTAL FLOOR AREA:              48.50 m² (522.00 sqft)
```

### JSON Output (`measurements.json`)
```json
{
  "scale": {"pixels_per_meter": 118.11},
  "rooms": {
    "room_1": {
      "room_type": "Bedroom",
      "area_m2": 15.25,
      "area_sqft": 164.13,
      "width_m": 3.8,
      "height_m": 4.2
    }
  },
  "summary": {
    "total_area": {
      "total_area_m2": 48.50,
      "total_area_sqft": 522.00
    }
  }
}
```

## Common Scales Reference

| Scale Notation | Pixels/Meter @ 300 DPI | Use Case |
|---------------|------------------------|----------|
| 1:50 | 236.22 | Detailed plans |
| 1:100 | 118.11 | Common residential |
| 1:200 | 59.06 | Larger buildings |
| 1:250 | 47.24 | Site plans |
| 1:500 | 23.62 | Large developments |

## Troubleshooting

**"No scale found"**
- Use interactive mode to measure the scale bar manually
- Or use: `python calibrate_scale.py --im_path=plan.png --method=manual --reference_meters=5.0`

**"Measurements seem off"**
- Verify the DPI matches your PDF conversion (default: 300)
- Double-check the scale notation on your PDF
- Try interactive mode for precise calibration

**"Some rooms missing"**
- Run post-processing first: `python postprocess.py --result_dir=./out`
- Small rooms (<100 pixels) are filtered as noise
- Check if image quality is good enough

**"Need help with installation"**
- See `SETUP_AND_TEST.md` for detailed setup instructions
- See `WORKING_WITH_SCALED_PDFS.md` for comprehensive PDF guide

## Next Steps

1. ✅ Try on one PDF to verify it works
2. ✅ Check accuracy by comparing 1-2 known rooms
3. ✅ Process all your PDFs
4. ✅ Export results to CSV for analysis

## Example Complete Workflow

```bash
# 1. Extract scale from PDF
python pdf_scale_extractor.py \
    --pdf_path=apartment_101.pdf \
    --mode=auto \
    --output_image=apartment_101.png

# Output shows: "Use: --scale=118.11"

# 2. Measure floor plan
python demo_measure.py \
    --im_path=apartment_101.png \
    --scale=118.11 \
    --output_dir=./measurements/apt_101 \
    --save_json

# 3. Check results
cat ./measurements/apt_101/apartment_101_measurements.json

# 4. View annotated image
open ./measurements/apt_101/apartment_101_measured.png
```

## Expected Accuracy

With properly scaled PDFs:
- ✅ **±5-8%** with automatic scale extraction
- ✅ **±3-5%** with interactive scale bar measurement
- ✅ Much better than manual estimation (±30-50%)
- ✅ Comparable to commercial software

---

**You're ready to go! Start with one PDF to test, then batch process the rest.** 🚀

For more details, see:
- `WORKING_WITH_SCALED_PDFS.md` - Complete PDF workflow guide
- `MEASUREMENT_GUIDE.md` - Full measurement documentation
- `ACCURACY_ANALYSIS.md` - Detailed accuracy information
