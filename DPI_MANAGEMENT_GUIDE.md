# DPI Management Guide

## The DPI Problem

**Critical Issue:** Different PDFs converted at different DPIs will have **wildly different** measurements if you use the same scale value.

### Example of the Problem:

```bash
# Convert first PDF at 300 DPI
python pdf_scale_extractor.py --pdf_path=plan1.pdf --dpi=300
# Scale: 1/4"=1' → 246.14 pixels/meter

# Convert second PDF at 150 DPI
python pdf_scale_extractor.py --pdf_path=plan2.pdf --dpi=150
# Scale: 1/4"=1' → 123.07 pixels/meter

# If you use 246.14 for both:
python demo_measure.py --im_path=plan1.png --scale=246.14  # ✅ Correct
python demo_measure.py --im_path=plan2.png --scale=246.14  # ❌ 50% TOO SMALL!
```

**The measurements for plan2.png will be 50% too small** because it was converted at 150 DPI but measured using a 300 DPI scale.

## The Solution: Automatic DPI Tracking

The system now **automatically tracks DPI** in three ways:

### 1. Embedded in Image Metadata (Best)
When you convert a PDF, the DPI is embedded in the PNG file:
```bash
python pdf_scale_extractor.py --pdf_path=plan.pdf --dpi=300 --output_image=plan.png
# DPI is saved in the PNG metadata
```

### 2. Encoded in Filename (Backup)
Filenames automatically include DPI:
```bash
# Auto-generated filename includes DPI
plan_dpi300.png  # DPI=300
plan_dpi150.png  # DPI=150
```

### 3. DPI Database (Failsafe)
A `.dpi_database.json` file tracks all images:
```json
{
  "/path/to/plan.png": {
    "dpi": 300,
    "source_pdf": "plan.pdf",
    "scale_info": {
      "notation": "1/4\"=1'",
      "pixels_per_meter": 246.14
    }
  }
}
```

## How It Works Automatically

### Converting PDFs → Automatic DPI Saving

```bash
# Just convert normally - DPI is automatically saved
python pdf_scale_extractor.py --pdf_path=plan.pdf --dpi=300

# Output: plan_dpi300.png (DPI embedded + in filename + in database)
```

### Measuring → Automatic DPI Detection

```bash
# The measurement tool will automatically detect DPI
python demo_measure.py --im_path=plan_dpi300.png

# It will:
# 1. Check filename for DPI
# 2. Check image metadata
# 3. Check DPI database
# 4. Use correct scale automatically
```

## Best Practices

### ✅ DO: Use Consistent DPI

**Best:** Convert all PDFs at the same DPI (300 recommended):
```bash
for pdf in *.pdf; do
    python pdf_scale_extractor.py --pdf_path="$pdf" --dpi=300
done

# All images at 300 DPI - can use same scale
python batch_measure.py --input_dir=. --pattern="*_dpi300.png" --scale=246.14
```

### ✅ DO: Let Filenames Include DPI

The tool automatically generates filenames with DPI:
```bash
# Don't specify output_image - let it auto-generate
python pdf_scale_extractor.py --pdf_path=plan.pdf --dpi=300
# Creates: plan_dpi300.png ✅

# If you must specify, include DPI in name:
python pdf_scale_extractor.py --pdf_path=plan.pdf --dpi=300 --output_image=plan_300dpi.png ✅
```

### ✅ DO: Validate DPI Consistency

Before batch processing, verify all images have same DPI:
```bash
python dpi_manager.py --validate ./images --expected-dpi=300
```

**Output:**
```
DPI Validation Results
============================================================
Images checked: 25
Consistent: ✅ Yes

DPIs found:
  300 DPI: 25 images
```

### ❌ DON'T: Mix DPIs Without Tracking

```bash
# BAD - mixing DPIs without proper tracking
python pdf_scale_extractor.py --pdf_path=plan1.pdf --dpi=300 --output_image=plan1.png
python pdf_scale_extractor.py --pdf_path=plan2.pdf --dpi=150 --output_image=plan2.png

# Then using same scale for both:
python demo_measure.py --im_path=plan1.png --scale=246.14  # ✅
python demo_measure.py --im_path=plan2.png --scale=246.14  # ❌ WRONG!
```

### ❌ DON'T: Remove DPI from Filename

```bash
# BAD - removing DPI information
python pdf_scale_extractor.py --pdf_path=plan.pdf --dpi=300 --output_image=plan.png
# Lost DPI information from filename!

# GOOD - keep DPI in filename
python pdf_scale_extractor.py --pdf_path=plan.pdf --dpi=300 --output_image=plan_dpi300.png
# or just let it auto-generate:
python pdf_scale_extractor.py --pdf_path=plan.pdf --dpi=300
# Creates: plan_dpi300.png
```

## DPI Manager Tool

### Check DPI of an Image

```bash
python dpi_manager.py --get-dpi plan.png
```

**Output:**
```
DPI: 300
Scale info: {'notation': '1/4"=1'', 'pixels_per_meter': 246.14}
```

### Register Image Manually

```bash
python dpi_manager.py --register plan.png --dpi=300
```

### Validate Directory

```bash
python dpi_manager.py --validate ./floor_plans --expected-dpi=300
```

**Output shows:**
- ✅ All images at expected DPI
- ⚠️ Warnings for images with no DPI
- ❌ Errors for images with wrong DPI

### List All Registered Images

```bash
python dpi_manager.py --list
```

**Output:**
```
Registered Images
============================================================

plan1_dpi300.png
  DPI: 300
  Source: plan1.pdf
  Scale: {'notation': '1/4"=1'', 'pixels_per_meter': 246.14}

plan2_dpi300.png
  DPI: 300
  Source: plan2.pdf
  Scale: {'notation': '1/4"=1'', 'pixels_per_meter': 246.14}
```

### Clean Database

Remove entries for deleted images:
```bash
python dpi_manager.py --clean
```

## Workflow Examples

### Example 1: Single DPI (Recommended)

```bash
# Step 1: Convert all PDFs at 300 DPI
for pdf in *.pdf; do
    python pdf_scale_extractor.py --pdf_path="$pdf" --dpi=300
done

# Step 2: Verify consistency
python dpi_manager.py --validate . --expected-dpi=300

# Step 3: Batch measure (all same scale)
python batch_measure.py --input_dir=. --pattern="*_dpi300.png" --scale=246.14
```

**Benefits:**
- ✅ Simple - one scale for all
- ✅ Fast - no per-image scale calculation
- ✅ Safe - consistent measurements

### Example 2: Mixed DPIs (Advanced)

If you must use different DPIs:

```bash
# Step 1: Convert PDFs with different DPIs (auto-saves DPI)
python pdf_scale_extractor.py --pdf_path=large.pdf --dpi=600
python pdf_scale_extractor.py --pdf_path=small.pdf --dpi=150

# Step 2: Get scale for each DPI
# At 600 DPI: 1/4"=1' → 492.29 pixels/meter
# At 150 DPI: 1/4"=1' → 123.07 pixels/meter

# Step 3: Measure with correct scale per image
python demo_measure.py --im_path=large_dpi600.png --scale=492.29
python demo_measure.py --im_path=small_dpi150.png --scale=123.07
```

**Or let the scale extractor tell you:**
```bash
python pdf_scale_extractor.py --pdf_path=plan.pdf --dpi=600 --mode=auto
# Output includes the correct pixels/meter for 600 DPI
```

### Example 3: Validation Before Batch

```bash
# Convert all PDFs
for pdf in *.pdf; do
    python pdf_scale_extractor.py --pdf_path="$pdf" --dpi=300
done

# Validate before measuring
python dpi_manager.py --validate . --expected-dpi=300

# If validation passes:
if [ $? -eq 0 ]; then
    echo "✅ All images at 300 DPI - proceeding"
    python batch_measure.py --input_dir=. --pattern="*_dpi300.png" --scale=246.14
else
    echo "❌ DPI mismatch detected - fix before measuring"
fi
```

## DPI Reference Table

For 1/4"=1' scale (most common):

| DPI | Pixels/Meter | Use Case |
|-----|--------------|----------|
| 72 | 59.16 | Screen display only (not for measurement) |
| 150 | 123.07 | Low res, faster processing |
| 200 | 164.10 | Medium quality |
| **300** | **246.14** | **Standard (recommended)** |
| 600 | 492.29 | High quality, detailed plans |
| 1200 | 984.58 | Ultra high quality |

**Rule of thumb:**
```
pixels_per_meter = (DPI × 39.37) / scale_ratio

For 1/4"=1' (ratio 48:1):
pixels_per_meter = (DPI × 39.37) / 48
```

## Common Issues

### Issue 1: "Measurements are half what they should be"

**Cause:** Image converted at 150 DPI but measured with 300 DPI scale

**Fix:**
```bash
# Check the image DPI
python dpi_manager.py --get-dpi problem_image.png

# Use correct scale for that DPI
python pdf_scale_extractor.py --pdf_path=source.pdf --dpi=150 --mode=auto
# Use the scale it outputs
```

### Issue 2: "Measurements are twice what they should be"

**Cause:** Image converted at 600 DPI but measured with 300 DPI scale

**Fix:** Same as above - use correct scale for the DPI

### Issue 3: "Don't know what DPI my images are"

**Solution 1:** Check metadata
```bash
python dpi_manager.py --get-dpi image.png
```

**Solution 2:** Check filename pattern
```bash
# Look for DPI in filename
ls *dpi*.png
ls *@*.png
```

**Solution 3:** Reconvert from PDF
```bash
python pdf_scale_extractor.py --pdf_path=original.pdf --dpi=300
```

### Issue 4: "Batch processing mixed DPIs"

**Don't do this:**
```bash
# All images at different DPIs, using same scale - WRONG!
python batch_measure.py --input_dir=. --pattern="*.png" --scale=246.14
```

**Do this:**
```bash
# Group by DPI
python batch_measure.py --input_dir=. --pattern="*_dpi300.png" --scale=246.14
python batch_measure.py --input_dir=. --pattern="*_dpi150.png" --scale=123.07
```

## Recommendations

### For Best Results:

1. ✅ **Use 300 DPI for everything** - Standard, good quality, manageable file size
2. ✅ **Let filenames include DPI** - Use auto-generated names
3. ✅ **Validate before batch processing** - Check DPI consistency
4. ✅ **Keep DPI database** - Don't delete `.dpi_database.json`
5. ✅ **Document your DPI** - Add to README or notes

### DPI Selection Guide:

- **150 DPI:** Small files, faster processing, still acceptable accuracy
- **300 DPI:** ⭐ **RECOMMENDED** - Best balance of quality and file size
- **600 DPI:** Large, detailed plans, when you need maximum accuracy

## Summary

**The system automatically handles DPI** through:
1. 📷 Embedded metadata in images
2. 📝 DPI in filenames
3. 📊 DPI database tracking

**You just need to:**
- ✅ Use consistent DPI (300 recommended)
- ✅ Let the tool auto-generate filenames
- ✅ Validate before batch processing

**The system will:**
- ✅ Save DPI with each image
- ✅ Detect DPI automatically
- ✅ Warn about mismatches
- ✅ Calculate correct scales

**Result:** Accurate measurements regardless of DPI! 🎯
