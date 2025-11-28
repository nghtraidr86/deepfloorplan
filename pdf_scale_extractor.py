"""
PDF Scale Extraction Tool for Floor Plans
Helps extract scale information from PDF floor plans with marked scales
"""

import argparse
import cv2
import numpy as np
import re
import os

try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False

try:
    from dpi_manager import DPIManager, save_image_with_dpi
    HAS_DPI_MANAGER = True
except ImportError:
    HAS_DPI_MANAGER = False
    print("Warning: dpi_manager not available. DPI tracking will be limited.")


class PDFScaleExtractor:
    """Extract scale information from PDF floor plans"""

    def __init__(self):
        # Metric scales (ratio)
        self.common_scales = {
            '1:50': 50,
            '1:100': 100,
            '1:200': 200,
            '1:250': 250,
            '1:500': 500,
            '1/50': 50,
            '1/100': 100,
            '1/200': 200,
            '1/250': 250,
            '1/500': 500,
        }

        # Imperial/Architectural scales (inches on paper = feet in reality)
        # Format: paper_inches: real_feet
        self.imperial_scales = {
            '1/16': 1,   # 1/16" = 1'
            '1/8': 1,    # 1/8" = 1'
            '3/16': 1,   # 3/16" = 1'
            '1/4': 1,    # 1/4" = 1'
            '3/8': 1,    # 3/8" = 1'
            '1/2': 1,    # 1/2" = 1'
            '3/4': 1,    # 3/4" = 1'
            '1': 1,      # 1" = 1'
            '1-1/2': 1,  # 1-1/2" = 1'
            '3': 1,      # 3" = 1'
        }

    def convert_pdf_to_image(self, pdf_path, dpi=300):
        """Convert PDF to image"""
        if not HAS_PDF2IMAGE:
            print("Error: pdf2image not installed. Install with: pip install pdf2image")
            print("Also requires poppler: brew install poppler (Mac) or apt-get install poppler-utils (Linux)")
            return None

        print(f"Converting PDF to image at {dpi} DPI...")
        images = convert_from_path(pdf_path, dpi=dpi)

        if not images:
            print("Error: Could not convert PDF to image")
            return None

        # Use first page
        image = images[0]

        # Convert PIL to OpenCV format
        image_array = np.array(image)
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

        return image_bgr

    def extract_text_from_image(self, image):
        """Extract text from image using OCR"""
        if not HAS_OCR:
            print("Error: pytesseract not installed. Install with: pip install pytesseract")
            print("Also requires tesseract: brew install tesseract (Mac) or apt-get install tesseract-ocr (Linux)")
            return ""

        # Convert to grayscale for better OCR
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply thresholding to get better text recognition
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        # Run OCR
        text = pytesseract.image_to_string(thresh)

        return text

    def parse_imperial_fraction(self, fraction_str):
        """
        Parse imperial fraction string to decimal

        Args:
            fraction_str: String like "1/4", "3/16", "1-1/2"

        Returns:
            Decimal value or None
        """
        fraction_str = fraction_str.strip()

        # Handle mixed fractions like "1-1/2"
        if '-' in fraction_str:
            parts = fraction_str.split('-')
            if len(parts) == 2:
                whole = int(parts[0])
                frac_parts = parts[1].split('/')
                if len(frac_parts) == 2:
                    numerator = int(frac_parts[0])
                    denominator = int(frac_parts[1])
                    return whole + (numerator / denominator)

        # Handle simple fractions like "1/4"
        elif '/' in fraction_str:
            parts = fraction_str.split('/')
            if len(parts) == 2:
                numerator = int(parts[0])
                denominator = int(parts[1])
                return numerator / denominator

        # Handle whole numbers
        else:
            try:
                return float(fraction_str)
            except:
                return None

        return None

    def imperial_scale_to_ratio(self, paper_inches, real_feet):
        """
        Convert imperial scale to ratio

        Args:
            paper_inches: Inches on paper (e.g., 0.25 for 1/4")
            real_feet: Feet in reality (usually 1)

        Returns:
            Scale ratio (e.g., 48 for 1/4"=1')
        """
        # Convert feet to inches: 1 foot = 12 inches
        real_inches = real_feet * 12

        # Scale ratio = real / paper
        ratio = real_inches / paper_inches

        return ratio

    def find_scale_in_text(self, text):
        """
        Find scale in text - supports both metric and imperial formats

        Metric: 1:100, 1/200, etc.
        Imperial: 1/4"=1', 3/16"=1', etc.

        Returns:
            Dictionary with 'metric_ratios' and 'imperial_scales'
        """
        result = {
            'metric_ratios': [],
            'imperial_scales': []
        }

        # ========== IMPERIAL SCALE PATTERNS ==========
        # Pattern: 1/4"=1', 3/16"=1'-0", etc.
        # Common formats:
        # - 1/4"=1'
        # - 1/4" = 1'-0"
        # - 3/16"=1'
        # - Scale: 1/4"=1'

        imperial_patterns = [
            # Pattern 1: "1/4"=1'" or "1/4" = 1'"
            r'(\d+(?:-\d+)?/\d+|\d+)\s*["\u201d]\s*=\s*(\d+)\s*[\'\u2019]',

            # Pattern 2: "Scale: 1/4"=1'"
            r'[Ss]cale\s*[:\-]?\s*(\d+(?:-\d+)?/\d+|\d+)\s*["\u201d]\s*=\s*(\d+)\s*[\'\u2019]',

            # Pattern 3: Without quotes: "1/4=1" or "1/4 = 1"
            r'(\d+(?:-\d+)?/\d+)\s*=\s*(\d+)',
        ]

        for pattern in imperial_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) >= 2:
                    paper_str = match[0]
                    real_str = match[1]

                    # Parse fractions
                    paper_inches = self.parse_imperial_fraction(paper_str)
                    real_feet = float(real_str) if real_str.isdigit() else None

                    if paper_inches and real_feet:
                        ratio = self.imperial_scale_to_ratio(paper_inches, real_feet)
                        result['imperial_scales'].append({
                            'notation': f'{paper_str}"={real_str}\'',
                            'paper_inches': paper_inches,
                            'real_feet': real_feet,
                            'ratio': ratio
                        })

        # ========== METRIC SCALE PATTERNS ==========
        # Pattern 1: "1:XXX" or "1/XXX" format
        pattern1 = r'1\s*[:\/]\s*(\d+)'

        # Pattern 2: "Scale: 1:XXX" format
        pattern2 = r'[Ss]cale\s*[:\-]?\s*1\s*[:\/]\s*(\d+)'

        # Pattern 3: "SCALE 1:XXX" format
        pattern3 = r'SCALE\s+1\s*[:\/]\s*(\d+)'

        all_patterns = [pattern2, pattern3, pattern1]

        for pattern in all_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        scale_ratio = int(match[0]) if match[0].isdigit() else None
                    else:
                        scale_ratio = int(match) if match.isdigit() else None

                    if scale_ratio and 10 <= scale_ratio <= 1000:
                        if scale_ratio not in result['metric_ratios']:
                            result['metric_ratios'].append(scale_ratio)

        return result

    def calculate_pixels_per_meter(self, scale_ratio, dpi=300):
        """
        Calculate pixels per meter from scale ratio and DPI

        Args:
            scale_ratio: Scale ratio (e.g., 100 for 1:100)
            dpi: Dots per inch of the image

        Returns:
            pixels_per_meter
        """
        # At 1:1 scale, 1 meter on paper = 1 meter in reality
        # At 300 DPI: 1 inch = 300 pixels
        # 1 meter = 39.37 inches = 39.37 * 300 = 11,811 pixels at 1:1

        pixels_per_meter_at_1_1 = dpi * 39.37  # pixels per meter at 1:1 scale
        pixels_per_meter = pixels_per_meter_at_1_1 / scale_ratio

        return pixels_per_meter

    def detect_scale_bar(self, image):
        """
        Detect graphical scale bar in the image

        Returns:
            List of potential scale bars as (x1, y1, x2, y2, length_pixels)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect edges
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Detect lines using Hough transform
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100,
                               minLineLength=50, maxLineGap=10)

        if lines is None:
            return []

        scale_bars = []

        for line in lines:
            x1, y1, x2, y2 = line[0]

            # Check if mostly horizontal (potential scale bar)
            if abs(y2 - y1) < 10:
                length = np.sqrt((x2-x1)**2 + (y2-y1)**2)

                # Scale bars are usually in bottom portion of image
                if y1 > image.shape[0] * 0.7:
                    scale_bars.append((x1, y1, x2, y2, length))

        # Sort by length (longest likely to be scale bar)
        scale_bars.sort(key=lambda x: x[4], reverse=True)

        return scale_bars

    def interactive_scale_bar_measurement(self, image_path, known_length_meters):
        """
        Interactive tool to measure scale bar

        Args:
            image_path: Path to image
            known_length_meters: Known length the scale bar represents
        """
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not load image {image_path}")
            return None

        print("\n" + "="*80)
        print("INTERACTIVE SCALE BAR MEASUREMENT")
        print("="*80)
        print(f"\nKnown length: {known_length_meters} meters")
        print("\nInstructions:")
        print("1. Look for the scale bar on the floor plan (usually at bottom)")
        print("2. Click at the START of the scale bar (e.g., at '0')")
        print("3. Click at the END of the scale bar (e.g., at '5m' or '10m')")
        print("4. Press 'q' when done, 'r' to reset")
        print("="*80 + "\n")

        points = []
        clone = image.copy()

        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                if len(points) < 2:
                    points.append((x, y))
                    cv2.circle(clone, (x, y), 5, (0, 255, 0), -1)

                    if len(points) == 2:
                        cv2.line(clone, points[0], points[1], (0, 255, 0), 2)

                        # Calculate length
                        length_pixels = np.sqrt(
                            (points[1][0] - points[0][0])**2 +
                            (points[1][1] - points[0][1])**2
                        )

                        # Display length
                        mid_x = (points[0][0] + points[1][0]) // 2
                        mid_y = (points[0][1] + points[1][1]) // 2
                        cv2.putText(clone, f"{length_pixels:.1f} px",
                                  (mid_x, mid_y - 10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                    cv2.imshow("Measure Scale Bar", clone)

        cv2.namedWindow("Measure Scale Bar")
        cv2.setMouseCallback("Measure Scale Bar", mouse_callback)
        cv2.imshow("Measure Scale Bar", clone)

        while True:
            key = cv2.waitKey(1) & 0xFF

            if key == ord('r'):
                points = []
                clone = image.copy()
                cv2.imshow("Measure Scale Bar", clone)
                print("Points reset.")

            elif key == ord('q') or len(points) == 2:
                break

        cv2.destroyAllWindows()

        if len(points) != 2:
            print("Measurement cancelled.")
            return None

        # Calculate scale
        p1, p2 = points
        length_pixels = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        pixels_per_meter = length_pixels / known_length_meters

        print(f"\n✅ Scale Measured Successfully!")
        print(f"   Scale bar length: {length_pixels:.2f} pixels")
        print(f"   Represents: {known_length_meters} meters")
        print(f"   Scale: {pixels_per_meter:.2f} pixels per meter")

        return pixels_per_meter

    def auto_extract_scale(self, pdf_path, dpi=300, save_image_path=None):
        """
        Automatically extract scale from PDF

        Args:
            pdf_path: Path to PDF file
            dpi: DPI to use for conversion
            save_image_path: Optional path to save the converted image

        Returns:
            Dictionary with scale information and converted image
        """
        print("\n" + "="*80)
        print("AUTOMATIC SCALE EXTRACTION FROM PDF")
        print("="*80)
        print(f"\nPDF: {pdf_path}")
        print(f"DPI: {dpi}")
        print("="*80 + "\n")

        # Convert PDF to image
        image = self.convert_pdf_to_image(pdf_path, dpi)
        if image is None:
            return None

        result = {
            'pdf_path': pdf_path,
            'dpi': dpi,
            'scale_ratios_found': [],
            'pixels_per_meter_estimates': [],
            'ocr_text': '',
            'scale_bars_detected': [],
            'image': image
        }

        # Extract text using OCR
        print("Step 1: Extracting text with OCR...")
        text = self.extract_text_from_image(image)
        result['ocr_text'] = text

        if text:
            print(f"Extracted {len(text)} characters of text\n")

            # Find scale in text
            print("Step 2: Looking for scale notations in text...")
            scales = self.find_scale_in_text(text)

            # Process Imperial scales (e.g., 1/4"=1')
            if scales['imperial_scales']:
                print(f"\n✅ Found Imperial/Architectural scale(s):")
                for imp_scale in scales['imperial_scales']:
                    notation = imp_scale['notation']
                    ratio = imp_scale['ratio']
                    ppm = self.calculate_pixels_per_meter(ratio, dpi)

                    result['pixels_per_meter_estimates'].append({
                        'scale_type': 'imperial',
                        'notation': notation,
                        'scale_ratio': ratio,
                        'pixels_per_meter': ppm,
                        'description': f"{notation} (ratio 1:{ratio:.1f}) at {dpi} DPI"
                    })
                    print(f"   {notation} → Ratio 1:{ratio:.1f} → {ppm:.2f} pixels/meter")

            # Process Metric scales (e.g., 1:100)
            if scales['metric_ratios']:
                print(f"\n✅ Found Metric scale ratio(s):")
                result['scale_ratios_found'] = scales['metric_ratios']

                for ratio in scales['metric_ratios']:
                    ppm = self.calculate_pixels_per_meter(ratio, dpi)
                    result['pixels_per_meter_estimates'].append({
                        'scale_type': 'metric',
                        'scale_ratio': ratio,
                        'pixels_per_meter': ppm,
                        'description': f"1:{ratio} at {dpi} DPI"
                    })
                    print(f"   1:{ratio} → {ppm:.2f} pixels/meter")

            if not scales['imperial_scales'] and not scales['metric_ratios']:
                print("⚠️  No scale notation found in text")
        else:
            print("⚠️  No text extracted from PDF")

        # Detect scale bars
        print("\nStep 3: Looking for graphical scale bars...")
        scale_bars = self.detect_scale_bar(image)

        if scale_bars:
            result['scale_bars_detected'] = scale_bars[:5]  # Top 5
            print(f"✅ Found {len(scale_bars)} potential scale bar(s)")
            print("   Longest bar: {:.1f} pixels".format(scale_bars[0][4]))
        else:
            print("⚠️  No scale bars detected")

        # Save image with DPI metadata if path provided
        if save_image_path:
            if HAS_DPI_MANAGER:
                save_image_with_dpi(image, save_image_path, dpi)

                # Register in DPI database
                dpi_manager = DPIManager()
                scale_info = result['pixels_per_meter_estimates'][0] if result['pixels_per_meter_estimates'] else None
                dpi_manager.register_image(save_image_path, dpi, pdf_path, scale_info)
            else:
                cv2.imwrite(save_image_path, image)
                print(f"Saved image to: {save_image_path}")
                print(f"⚠️  DPI metadata not embedded (dpi_manager not available)")

        return result


def main():
    parser = argparse.ArgumentParser(
        description='Extract scale information from PDF floor plans'
    )

    parser.add_argument('--pdf_path', type=str, required=True,
                       help='Path to PDF floor plan')

    parser.add_argument('--dpi', type=int, default=300,
                       help='DPI for PDF conversion (default: 300)')

    parser.add_argument('--mode', type=str, default='auto',
                       choices=['auto', 'interactive', 'both'],
                       help='Extraction mode')

    parser.add_argument('--scale_bar_length', type=float,
                       help='Known length of scale bar in meters (for interactive mode)')

    parser.add_argument('--output_image', type=str,
                       help='Save converted image to this path')

    args = parser.parse_args()

    extractor = PDFScaleExtractor()

    if args.mode in ['auto', 'both']:
        # Determine output image path
        if args.output_image:
            output_path = args.output_image
        else:
            # Auto-generate filename with DPI
            base_name = os.path.splitext(os.path.basename(args.pdf_path))[0]
            output_path = f"{base_name}_dpi{args.dpi}.png"

        # Automatic extraction
        result = extractor.auto_extract_scale(args.pdf_path, args.dpi, output_path)

        if result and result['pixels_per_meter_estimates']:
            print("\n" + "="*80)
            print("RECOMMENDED SCALE VALUES")
            print("="*80)

            for i, estimate in enumerate(result['pixels_per_meter_estimates'], 1):
                print(f"\nOption {i}: {estimate['description']}")
                print(f"  Use: --scale={estimate['pixels_per_meter']:.2f}")
                print(f"\n  Command:")
                print(f"  python demo_measure.py --im_path={output_path} --scale={estimate['pixels_per_meter']:.2f}")

            print(f"\n💾 Image saved: {output_path}")
            print(f"📊 DPI: {args.dpi} (embedded in image metadata)")
            print("\n" + "="*80)

    if args.mode in ['interactive', 'both']:
        # Interactive measurement
        if not args.scale_bar_length:
            print("\nFor interactive mode, please provide --scale_bar_length")
            print("Example: --scale_bar_length=5.0 (if scale bar represents 5 meters)")
            return

        # First convert PDF to image and save
        image = extractor.convert_pdf_to_image(args.pdf_path, args.dpi)
        if image is None:
            return

        temp_image_path = args.output_image or f'temp_floorplan_dpi{args.dpi}.png'

        # Save with DPI metadata
        if HAS_DPI_MANAGER:
            save_image_with_dpi(image, temp_image_path, args.dpi)
        else:
            cv2.imwrite(temp_image_path, image)
            print(f"⚠️  DPI metadata not embedded")

        print(f"\nSaved image to: {temp_image_path}")

        # Interactive measurement
        pixels_per_meter = extractor.interactive_scale_bar_measurement(
            temp_image_path,
            args.scale_bar_length
        )

        if pixels_per_meter:
            # Register in DPI database
            if HAS_DPI_MANAGER:
                dpi_manager = DPIManager()
                scale_info = {
                    'pixels_per_meter': pixels_per_meter,
                    'method': 'interactive_scale_bar',
                    'scale_bar_length_m': args.scale_bar_length
                }
                dpi_manager.register_image(temp_image_path, args.dpi, args.pdf_path, scale_info)

            print("\n" + "="*80)
            print("USE THIS SCALE")
            print("="*80)
            print(f"\npython demo_measure.py --im_path={temp_image_path} --scale={pixels_per_meter:.2f}")
            print(f"\n💾 Image saved: {temp_image_path}")
            print(f"📊 DPI: {args.dpi} (embedded in metadata)")
            print("\n" + "="*80)


if __name__ == '__main__':
    main()
