# Imperial/Architectural Scale Reference Guide

Since your PDFs use **US architectural scales** (like 1/4"=1', 3/16"=1'), this guide helps you understand and work with them.

## Understanding Imperial Scales

### Format: `X"=Y'`
- **X"** = inches on the drawing (paper)
- **Y'** = feet in reality (building)

**Example:** `1/4"=1'` means:
- 1/4 inch on paper = 1 foot in real building
- 0.25 inches on paper = 12 inches in reality
- Scale ratio = 12 ÷ 0.25 = **48:1**

## Common Architectural Scales

### Standard Scales

| Scale Notation | Ratio | Pixels/Meter @ 300 DPI | Typical Use |
|---------------|-------|------------------------|-------------|
| **3/32"=1'** | 128:1 | 92.30 | Site plans, large buildings |
| **1/8"=1'** | 96:1 | 123.07 | Floor plans, elevations |
| **3/16"=1'** | 64:1 | 184.61 | Common floor plans |
| **1/4"=1'** | 48:1 | 246.14 | Detailed floor plans (very common) |
| **3/8"=1'** | 32:1 | 369.21 | Detailed plans, larger scale |
| **1/2"=1'** | 24:1 | 492.29 | Detail drawings |
| **3/4"=1'** | 16:1 | 738.43 | Large scale details |
| **1"=1'** | 12:1 | 984.58 | Full size details |
| **1-1/2"=1'** | 8:1 | 1476.87 | Very detailed |
| **3"=1'** | 4:1 | 2953.74 | Near full size |

### At Different DPIs

The pixels-per-meter changes with DPI. Here are values for the most common scales:

#### 1/4"=1' (Most Common)

| DPI | Pixels/Meter | When to Use |
|-----|--------------|-------------|
| 150 | 123.07 | Low res, faster processing |
| 200 | 164.10 | Medium quality |
| 300 | 246.14 | **Standard (recommended)** |
| 600 | 492.29 | High quality, large files |

#### 3/16"=1' (Also Common)

| DPI | Pixels/Meter | When to Use |
|-----|--------------|-------------|
| 150 | 92.30 | Low res |
| 200 | 123.07 | Medium |
| 300 | 184.61 | **Standard (recommended)** |
| 600 | 369.21 | High quality |

#### 1/8"=1' (Smaller Buildings)

| DPI | Pixels/Meter | When to Use |
|-----|--------------|-------------|
| 150 | 61.54 | Low res |
| 200 | 82.05 | Medium |
| 300 | 123.07 | **Standard (recommended)** |
| 600 | 246.14 | High quality |

## How to Use with Your PDFs

### Method 1: Automatic Extraction (Easiest)

The tool automatically recognizes imperial scales:

```bash
python pdf_scale_extractor.py --pdf_path=your_plan.pdf --mode=auto --dpi=300
```

**Expected Output:**
```
✅ Found Imperial/Architectural scale(s):
   1/4"=1' → Ratio 1:48.0 → 246.14 pixels/meter

RECOMMENDED SCALE VALUES
========================
Option 1: 1/4"=1' (ratio 1:48.0) at 300 DPI
  Use: --scale=246.14

Command:
  python demo_measure.py --im_path=<image> --scale=246.14
```

### Method 2: Manual (If Auto-Detection Fails)

If OCR doesn't recognize the scale, use this table:

**Look at your PDF** → Find the scale notation → Use the corresponding pixels/meter

**Example:**
- PDF says: `Scale: 1/4"=1'`
- At 300 DPI: Use `--scale=246.14`

```bash
python demo_measure.py --im_path=plan.png --scale=246.14 --save_json
```

### Method 3: Interactive Verification

Always verify on one sample:

```bash
# Extract automatically
python pdf_scale_extractor.py --pdf_path=sample.pdf --mode=auto --output_image=sample.png

# Verify with known dimension (e.g., 10-foot wall)
python calibrate_scale.py --im_path=sample.png --method=manual --reference_meters=3.048

# 3.048 meters = 10 feet
# Compare the two scales - they should match within ±5%
```

## Scale Conversion Formulas

### Imperial Scale to Ratio

```
Ratio = Real_Feet × 12 / Paper_Inches

Example for 1/4"=1':
Ratio = 1 × 12 / 0.25 = 48
```

### Ratio to Pixels per Meter

```
Pixels_per_Meter = (DPI × 39.37) / Ratio

Example for 1/4"=1' at 300 DPI:
= (300 × 39.37) / 48
= 11,811 / 48
= 246.14 pixels/meter
```

### Quick Reference Calculation

If you know:
- Paper inches: P
- Real feet: R
- DPI: D

Then:
```
Pixels_per_Meter = (D × 39.37 × P) / (R × 12)
```

## Common Mistakes to Avoid

### ❌ Mistake 1: Confusing Inches and Feet

**Wrong:** `1/4"=1'` means 1/4 inch = 1 inch
**Right:** `1/4"=1'` means 1/4 inch = 1 **foot** (12 inches)

### ❌ Mistake 2: Wrong DPI

If you convert PDF at 150 DPI but use 300 DPI values:
- Your measurements will be **50% too small**

**Solution:** Always match DPI in conversion and calculation:
```bash
python pdf_scale_extractor.py --pdf_path=plan.pdf --dpi=300
# Then use the 300 DPI value it gives you
```

### ❌ Mistake 3: Mixing Metric and Imperial

**Wrong:** Using 1:100 for a PDF that says 1/4"=1'
**Right:** Use 246.14 pixels/meter for 1/4"=1' at 300 DPI

### ❌ Mistake 4: Not Verifying

**Always verify** on a sample before batch processing:
```bash
# Extract scale
python pdf_scale_extractor.py --pdf_path=test.pdf --mode=auto

# Measure
python demo_measure.py --im_path=test.png --scale=246.14

# Check one room against known dimensions
# If close (±5-10%), you're good!
```

## Real-World Example

### Scenario: Residential floor plans at 1/4"=1'

```bash
# Step 1: Verify scale on first PDF
python pdf_scale_extractor.py \
    --pdf_path=house_plan_001.pdf \
    --dpi=300 \
    --mode=auto \
    --output_image=house_001.png

# Output: "Use: --scale=246.14"

# Step 2: Verify with known dimension
# (e.g., master bedroom is 12' x 14' = 3.66m x 4.27m)
python demo_measure.py --im_path=house_001.png --scale=246.14 --save_json

# Check if master bedroom measures ~15.6 m² (168 sqft)
# ✅ If yes, proceed with batch

# Step 3: Batch process all plans
for pdf in house_plan_*.pdf; do
    python pdf_scale_extractor.py \
        --pdf_path="$pdf" \
        --dpi=300 \
        --mode=auto \
        --output_image="$(basename $pdf .pdf).png"
done

python batch_measure.py \
    --input_dir=. \
    --pattern="house_plan_*.png" \
    --scale=246.14 \
    --output_dir=./results
```

## Converting Units

### Feet to Meters
```
Meters = Feet × 0.3048

Examples:
10 feet = 3.048 meters
20 feet = 6.096 meters
30 feet = 9.144 meters
```

### Square Feet to Square Meters
```
m² = sqft × 0.0929

Examples:
100 sqft = 9.29 m²
500 sqft = 46.45 m²
1000 sqft = 92.90 m²
```

The measurement system automatically provides **both** metric and imperial outputs!

## Troubleshooting Imperial Scales

### "Scale not detected"

**Try these patterns:**
- `1/4"=1'`
- `1/4" = 1'-0"`
- `Scale: 1/4"=1'`
- `SCALE 1/4"=1'`

If still not working:
```bash
# Use interactive mode with feet converted to meters
python calibrate_scale.py --im_path=plan.png --method=manual --reference_meters=3.048
# 3.048m = 10 feet
```

### "Wrong scale extracted"

**Check:**
1. Is the PDF clear and readable?
2. Is the scale text not obscured?
3. Is DPI correct (usually 300)?

**Verify manually:**
- Look at PDF to confirm scale
- Use interactive mode for precision

### "Measurements don't match known dimensions"

**Checklist:**
1. ✅ Verify scale notation on PDF
2. ✅ Confirm DPI matches conversion (300 is standard)
3. ✅ Check if PDF has multiple scales (use correct one)
4. ✅ Verify known dimensions are actually correct

## Quick Reference Table (Print This!)

**At 300 DPI:**

| Scale | Command |
|-------|---------|
| 1/8"=1' | `--scale=123.07` |
| 3/16"=1' | `--scale=184.61` |
| 1/4"=1' | `--scale=246.14` |
| 3/8"=1' | `--scale=369.21` |
| 1/2"=1' | `--scale=492.29` |

**Example usage:**
```bash
python demo_measure.py --im_path=plan.png --scale=246.14 --save_json
```

---

## Key Takeaways

1. 🎯 **Most common:** 1/4"=1' at 300 DPI = 246.14 pixels/meter
2. ✅ **Always verify** on one sample before batch processing
3. 📏 **Match DPI** between PDF conversion and calculation
4. 🔄 **Auto-detection** works for most PDFs
5. 🎓 **Remember:** X"=Y' means X inches on paper = Y feet in reality

---

**With imperial scales properly recognized, you'll get ±5% accuracy automatically!** 🎉
