"""
Interactive scale calibration tool for floor plan measurements
Helps determine the correct pixels-per-meter scale factor
"""

import cv2
import numpy as np
import argparse
from matplotlib import pyplot as plt

from measure import calibrate_scale_from_reference


class ScaleCalibrator:
    """Interactive tool for calibrating floor plan scale"""

    def __init__(self, image_path):
        self.image_path = image_path
        self.image = cv2.imread(image_path)

        if self.image is None:
            raise ValueError(f"Could not load image: {image_path}")

        self.image_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.points = []
        self.scale = None

    def manual_measurement(self, actual_length_meters):
        """
        Interactive point selection to measure a reference length

        Args:
            actual_length_meters: The actual length in meters of the reference
        """
        print("\n" + "="*80)
        print("INTERACTIVE SCALE CALIBRATION")
        print("="*80)
        print("\nInstructions:")
        print("1. Click on TWO points that represent a known distance")
        print("2. For best accuracy, choose points that are far apart")
        print("3. Press 'q' to quit, 'r' to reset points")
        print("\nExample: Click start and end of a wall that you know is 5 meters long")
        print("="*80 + "\n")

        self.points = []
        clone = self.image.copy()

        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                if len(self.points) < 2:
                    self.points.append((x, y))
                    cv2.circle(clone, (x, y), 5, (0, 255, 0), -1)

                    if len(self.points) == 2:
                        cv2.line(clone, self.points[0], self.points[1],
                                (0, 255, 0), 2)

                    cv2.imshow("Calibration", clone)

        cv2.namedWindow("Calibration")
        cv2.setMouseCallback("Calibration", mouse_callback)
        cv2.imshow("Calibration", clone)

        while True:
            key = cv2.waitKey(1) & 0xFF

            if key == ord('r'):  # Reset
                self.points = []
                clone = self.image.copy()
                cv2.imshow("Calibration", clone)
                print("Points reset. Select 2 new points.")

            elif key == ord('q') or len(self.points) == 2:  # Quit or done
                break

        cv2.destroyAllWindows()

        if len(self.points) != 2:
            print("Calibration cancelled. No scale calculated.")
            return None

        # Calculate pixel distance
        p1, p2 = self.points
        pixel_distance = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

        print(f"\nMeasured distance: {pixel_distance:.2f} pixels")
        print(f"Actual distance: {actual_length_meters} meters")

        # Calculate scale
        self.scale = calibrate_scale_from_reference(
            pixel_distance,
            actual_length_meters
        )

        print(f"\nCalculated scale: {self.scale:.2f} pixels per meter")
        print(f"\nUse this scale in your measurements:")
        print(f"  python demo_measure.py --im_path=<image> --scale={self.scale:.2f}")

        return self.scale

    def auto_detect_scale_from_text(self):
        """
        Attempt to automatically detect scale from text in the image
        (e.g., scale bar, scale text like "1:100")

        Note: This is a basic implementation and may not work for all floor plans
        """
        print("\n" + "="*80)
        print("AUTOMATIC SCALE DETECTION")
        print("="*80)
        print("\nAttempting to detect scale from image text...")
        print("Note: This feature requires OCR (pytesseract)")
        print("For manual calibration, use --method=manual instead")
        print("="*80 + "\n")

        try:
            import pytesseract
        except ImportError:
            print("Error: pytesseract not installed.")
            print("Install with: pip install pytesseract")
            print("Also requires tesseract-ocr system package")
            return None

        # OCR to find scale text
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray)

        print(f"Detected text:\n{text}\n")

        # Look for common scale patterns
        import re

        # Pattern 1: "1:XXX" format
        scale_pattern = r'1\s*:\s*(\d+)'
        matches = re.findall(scale_pattern, text)

        if matches:
            scale_ratio = int(matches[0])
            print(f"Found scale ratio: 1:{scale_ratio}")

            # Assume 300 DPI standard for printed floor plans
            # At 300 DPI: 1 meter = 11811 pixels at 1:1 scale
            dpi = 300
            meters_to_pixels_at_scale_1 = (dpi / 0.0254) / 100  # pixels per cm * 100
            pixels_per_meter = meters_to_pixels_at_scale_1 / scale_ratio

            print(f"Calculated pixels per meter: {pixels_per_meter:.2f}")
            print(f"(Assuming {dpi} DPI)")

            self.scale = pixels_per_meter
            return self.scale
        else:
            print("Could not find scale ratio in text.")
            print("Try manual calibration instead.")
            return None

    def detect_scale_bar(self):
        """
        Attempt to detect a graphical scale bar in the image

        Note: This is a basic implementation
        """
        print("\n" + "="*80)
        print("SCALE BAR DETECTION")
        print("="*80)
        print("\nAttempting to detect graphical scale bar...")
        print("This feature is experimental.")
        print("="*80 + "\n")

        # Convert to grayscale
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

        # Detect horizontal lines (potential scale bars)
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100,
                               minLineLength=50, maxLineGap=10)

        if lines is None:
            print("No scale bar detected.")
            return None

        # Find the longest horizontal line (likely scale bar)
        longest_line = None
        max_length = 0

        for line in lines:
            x1, y1, x2, y2 = line[0]
            length = np.sqrt((x2-x1)**2 + (y2-y1)**2)

            # Check if mostly horizontal
            if abs(y2-y1) < 10 and length > max_length:
                max_length = length
                longest_line = line[0]

        if longest_line is None:
            print("No suitable scale bar found.")
            return None

        print(f"Detected potential scale bar: {max_length:.2f} pixels long")
        print("\nYou need to specify what this scale bar represents.")
        print("For example, if the scale bar represents 5 meters:")
        print(f"  python calibrate_scale.py --im_path={self.image_path} --method=manual")

        return None


def main():
    parser = argparse.ArgumentParser(
        description='Calibrate scale for floor plan measurements'
    )

    parser.add_argument('--im_path', type=str, required=True,
                       help='Path to floor plan image')

    parser.add_argument('--method', type=str, default='manual',
                       choices=['manual', 'auto', 'scalebar'],
                       help='Calibration method (manual, auto, scalebar)')

    parser.add_argument('--reference_meters', type=float, default=5.0,
                       help='Actual length in meters for manual calibration')

    parser.add_argument('--reference_pixels', type=float,
                       help='Pixel length for non-interactive manual calibration')

    args = parser.parse_args()

    # Initialize calibrator
    calibrator = ScaleCalibrator(args.im_path)

    if args.method == 'manual':
        if args.reference_pixels:
            # Non-interactive mode
            scale = calibrate_scale_from_reference(
                args.reference_pixels,
                args.reference_meters
            )
            print(f"\nCalculated scale: {scale:.2f} pixels per meter")
            print(f"\nUse this scale in your measurements:")
            print(f"  python demo_measure.py --im_path=<image> --scale={scale:.2f}")
        else:
            # Interactive mode
            scale = calibrator.manual_measurement(args.reference_meters)

    elif args.method == 'auto':
        scale = calibrator.auto_detect_scale_from_text()

    elif args.method == 'scalebar':
        scale = calibrator.detect_scale_bar()

    if scale:
        print("\n" + "="*80)
        print("CALIBRATION SUCCESSFUL!")
        print("="*80)
        print(f"\nYour scale factor: {scale:.2f} pixels per meter")
        print(f"\nNext steps:")
        print(f"1. Use this scale in demo_measure.py:")
        print(f"   python demo_measure.py --im_path=<your_image> --scale={scale:.2f}")
        print(f"\n2. Or in batch_measure.py:")
        print(f"   python batch_measure.py --input_dir=<dir> --scale={scale:.2f}")
        print("="*80 + "\n")
    else:
        print("\nCalibration failed or cancelled.")
        print("Try manual calibration with:")
        print(f"  python calibrate_scale.py --im_path={args.im_path} --method=manual")


if __name__ == '__main__':
    main()
