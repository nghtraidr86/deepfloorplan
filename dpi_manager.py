"""
DPI Management for Floor Plan Measurements
Tracks and manages DPI information to ensure accurate measurements
"""

import os
import json
import cv2
from PIL import Image


class DPIManager:
    """Manages DPI information for floor plan images"""

    def __init__(self, database_file='.dpi_database.json'):
        """
        Initialize DPI manager

        Args:
            database_file: Path to JSON file storing DPI mappings
        """
        self.database_file = database_file
        self.dpi_map = self.load_database()

    def load_database(self):
        """Load DPI database from file"""
        if os.path.exists(self.database_file):
            try:
                with open(self.database_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_database(self):
        """Save DPI database to file"""
        with open(self.database_file, 'w') as f:
            json.dump(self.dpi_map, f, indent=2)

    def register_image(self, image_path, dpi, source_pdf=None, scale_info=None):
        """
        Register an image with its DPI

        Args:
            image_path: Path to the image
            dpi: DPI value used
            source_pdf: Optional source PDF path
            scale_info: Optional scale information dict
        """
        abs_path = os.path.abspath(image_path)

        self.dpi_map[abs_path] = {
            'dpi': dpi,
            'source_pdf': source_pdf,
            'scale_info': scale_info,
            'registered_at': os.path.getmtime(image_path)
        }

        self.save_database()

    def get_dpi(self, image_path):
        """
        Get DPI for an image, trying multiple methods

        Args:
            image_path: Path to image

        Returns:
            DPI value or None
        """
        abs_path = os.path.abspath(image_path)

        # Method 1: Check database
        if abs_path in self.dpi_map:
            # Verify file hasn't changed
            if os.path.getmtime(image_path) == self.dpi_map[abs_path]['registered_at']:
                return self.dpi_map[abs_path]['dpi']

        # Method 2: Try to read from image metadata
        dpi_from_metadata = self.read_dpi_from_image(image_path)
        if dpi_from_metadata:
            return dpi_from_metadata

        # Method 3: Check filename for DPI tag
        dpi_from_filename = self.extract_dpi_from_filename(image_path)
        if dpi_from_filename:
            return dpi_from_filename

        return None

    def read_dpi_from_image(self, image_path):
        """
        Read DPI from image metadata

        Args:
            image_path: Path to image

        Returns:
            DPI value or None
        """
        try:
            with Image.open(image_path) as img:
                dpi = img.info.get('dpi')
                if dpi:
                    # DPI is typically a tuple (x_dpi, y_dpi)
                    if isinstance(dpi, (tuple, list)):
                        return int(dpi[0])
                    return int(dpi)
        except:
            pass

        return None

    def extract_dpi_from_filename(self, image_path):
        """
        Extract DPI from filename if it contains DPI tag

        Supports patterns like:
        - floorplan_300dpi.png
        - floorplan_dpi300.png
        - floorplan@300.png

        Args:
            image_path: Path to image

        Returns:
            DPI value or None
        """
        import re

        filename = os.path.basename(image_path)

        patterns = [
            r'_(\d+)dpi',
            r'dpi(\d+)',
            r'@(\d+)',
            r'-(\d+)dpi',
        ]

        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                dpi = int(match.group(1))
                if 50 <= dpi <= 1200:  # Reasonable DPI range
                    return dpi

        return None

    def get_scale_info(self, image_path):
        """
        Get full scale information for an image

        Args:
            image_path: Path to image

        Returns:
            Dict with DPI and scale info, or None
        """
        abs_path = os.path.abspath(image_path)

        if abs_path in self.dpi_map:
            return self.dpi_map[abs_path]

        return None

    def suggest_filename(self, base_name, dpi, extension='png'):
        """
        Suggest a filename that includes DPI

        Args:
            base_name: Base filename without extension
            dpi: DPI value
            extension: File extension (default: png)

        Returns:
            Suggested filename
        """
        return f"{base_name}_dpi{dpi}.{extension}"

    def validate_consistency(self, image_dir, expected_dpi=None):
        """
        Validate DPI consistency across images in a directory

        Args:
            image_dir: Directory containing images
            expected_dpi: Optional expected DPI value

        Returns:
            Dict with validation results
        """
        import glob

        results = {
            'consistent': True,
            'images_checked': 0,
            'dpis_found': {},
            'warnings': [],
            'errors': []
        }

        image_files = glob.glob(os.path.join(image_dir, '*.png'))
        image_files.extend(glob.glob(os.path.join(image_dir, '*.jpg')))

        for img_path in image_files:
            dpi = self.get_dpi(img_path)

            if dpi is None:
                results['warnings'].append(f"No DPI found for {os.path.basename(img_path)}")
                results['consistent'] = False
            else:
                results['dpis_found'][dpi] = results['dpis_found'].get(dpi, 0) + 1

                if expected_dpi and dpi != expected_dpi:
                    results['errors'].append(
                        f"{os.path.basename(img_path)}: Expected {expected_dpi} DPI, found {dpi}"
                    )
                    results['consistent'] = False

            results['images_checked'] += 1

        # Check if multiple DPIs found
        if len(results['dpis_found']) > 1:
            results['consistent'] = False
            results['warnings'].append(
                f"Multiple DPIs found: {list(results['dpis_found'].keys())}"
            )

        return results

    def clean_database(self):
        """Remove entries for images that no longer exist"""
        cleaned = {}
        removed_count = 0

        for img_path, info in self.dpi_map.items():
            if os.path.exists(img_path):
                cleaned[img_path] = info
            else:
                removed_count += 1

        self.dpi_map = cleaned
        self.save_database()

        return removed_count


def save_image_with_dpi(image_array, output_path, dpi=300):
    """
    Save image with DPI metadata embedded

    Args:
        image_array: Numpy array (OpenCV format)
        output_path: Path to save image
        dpi: DPI value to embed
    """
    # Convert OpenCV (BGR) to PIL (RGB)
    import cv2
    from PIL import Image

    if len(image_array.shape) == 3:
        rgb_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
    else:
        rgb_image = image_array

    pil_image = Image.fromarray(rgb_image)

    # Save with DPI metadata
    pil_image.save(output_path, dpi=(dpi, dpi))

    print(f"Saved image with DPI={dpi} metadata: {output_path}")


def main():
    """Command-line interface for DPI manager"""
    import argparse

    parser = argparse.ArgumentParser(description='Manage DPI information for floor plan images')

    parser.add_argument('--register', type=str, help='Register an image with DPI')
    parser.add_argument('--dpi', type=int, help='DPI value')
    parser.add_argument('--get-dpi', type=str, help='Get DPI for an image')
    parser.add_argument('--validate', type=str, help='Validate DPI consistency in directory')
    parser.add_argument('--expected-dpi', type=int, help='Expected DPI for validation')
    parser.add_argument('--clean', action='store_true', help='Clean database of non-existent files')
    parser.add_argument('--list', action='store_true', help='List all registered images')

    args = parser.parse_args()

    manager = DPIManager()

    if args.register and args.dpi:
        manager.register_image(args.register, args.dpi)
        print(f"Registered {args.register} with DPI={args.dpi}")

    elif args.get_dpi:
        dpi = manager.get_dpi(args.get_dpi)
        if dpi:
            print(f"DPI: {dpi}")
            scale_info = manager.get_scale_info(args.get_dpi)
            if scale_info and scale_info.get('scale_info'):
                print(f"Scale info: {scale_info['scale_info']}")
        else:
            print("DPI not found")

    elif args.validate:
        results = manager.validate_consistency(args.validate, args.expected_dpi)

        print("\nDPI Validation Results")
        print("=" * 60)
        print(f"Images checked: {results['images_checked']}")
        print(f"Consistent: {'✅ Yes' if results['consistent'] else '❌ No'}")

        if results['dpis_found']:
            print(f"\nDPIs found:")
            for dpi, count in results['dpis_found'].items():
                print(f"  {dpi} DPI: {count} images")

        if results['warnings']:
            print(f"\nWarnings:")
            for warning in results['warnings']:
                print(f"  ⚠️  {warning}")

        if results['errors']:
            print(f"\nErrors:")
            for error in results['errors']:
                print(f"  ❌ {error}")

    elif args.clean:
        removed = manager.clean_database()
        print(f"Cleaned database: removed {removed} entries")

    elif args.list:
        print("\nRegistered Images")
        print("=" * 60)
        for img_path, info in manager.dpi_map.items():
            print(f"\n{os.path.basename(img_path)}")
            print(f"  DPI: {info['dpi']}")
            if info.get('source_pdf'):
                print(f"  Source: {os.path.basename(info['source_pdf'])}")
            if info.get('scale_info'):
                print(f"  Scale: {info['scale_info']}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
