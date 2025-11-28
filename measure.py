"""
Floor Plan Measurement Module
Provides automated measurement capabilities for floor plans including:
- Room area calculation
- Room dimensions (width, length, perimeter)
- Pixel-to-real-world unit conversion
- Measurement visualization and reporting
"""

import cv2
import numpy as np
from scipy import ndimage
import json


# Room type labels for reference
ROOM_LABELS = {
    0: "Background",
    1: "Closet",
    2: "Bathroom/Washroom",
    3: "Living Room/Kitchen/Dining Room",
    4: "Bedroom",
    5: "Hall",
    6: "Balcony",
    7: "Not Used",
    8: "Not Used",
    9: "Door & Window",
    10: "Wall"
}


class FloorPlanMeasurement:
    """
    Main class for floor plan measurements
    """

    def __init__(self, pixels_per_meter=20.0):
        """
        Initialize measurement system

        Args:
            pixels_per_meter: Conversion factor from pixels to meters
                            Default assumes ~20 pixels per meter (adjust based on your floor plan scale)
        """
        self.pixels_per_meter = pixels_per_meter
        self.measurements = {}

    def set_scale(self, pixels_per_meter):
        """Update the pixel-to-meter conversion scale"""
        self.pixels_per_meter = pixels_per_meter

    def pixels_to_meters(self, pixels):
        """Convert pixel measurement to meters"""
        return pixels / self.pixels_per_meter

    def pixels_to_sqmeters(self, pixel_area):
        """Convert pixel area to square meters"""
        return pixel_area / (self.pixels_per_meter ** 2)

    def measure_room_areas(self, room_segmentation):
        """
        Calculate area for each room in the floor plan

        Args:
            room_segmentation: 2D numpy array with room labels (0-10)

        Returns:
            Dictionary with room measurements
        """
        measurements = {}

        # Get unique room types (excluding background, doors, and walls)
        unique_rooms = np.unique(room_segmentation)

        # Label connected components for each room type
        labeled_rooms, num_rooms = ndimage.label(room_segmentation > 0)

        for room_id in range(1, num_rooms + 1):
            # Get mask for this specific room
            room_mask = (labeled_rooms == room_id).astype(np.uint8)

            # Calculate area in pixels
            area_pixels = np.sum(room_mask)

            # Skip very small regions (likely noise)
            if area_pixels < 100:
                continue

            # Get room type
            room_type_values = room_segmentation[room_mask == 1]
            if len(room_type_values) == 0:
                continue

            # Most common room type in this region
            room_type = int(np.bincount(room_type_values).argmax())

            # Skip walls, doors, and background
            if room_type in [0, 9, 10]:
                continue

            # Get room dimensions
            y_coords, x_coords = np.where(room_mask == 1)

            if len(y_coords) == 0 or len(x_coords) == 0:
                continue

            # Bounding box
            min_x, max_x = np.min(x_coords), np.max(x_coords)
            min_y, max_y = np.min(y_coords), np.max(y_coords)

            width_pixels = max_x - min_x + 1
            height_pixels = max_y - min_y + 1

            # Calculate perimeter using contours
            contours, _ = cv2.findContours(room_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            perimeter_pixels = 0
            if contours:
                perimeter_pixels = cv2.arcLength(contours[0], True)

            # Convert to real-world measurements
            area_m2 = self.pixels_to_sqmeters(area_pixels)
            width_m = self.pixels_to_meters(width_pixels)
            height_m = self.pixels_to_meters(height_pixels)
            perimeter_m = self.pixels_to_meters(perimeter_pixels)

            # Store measurements
            room_key = f"room_{room_id}"
            measurements[room_key] = {
                'room_id': room_id,
                'room_type': ROOM_LABELS.get(room_type, "Unknown"),
                'room_type_id': room_type,
                'area_m2': round(area_m2, 2),
                'area_sqft': round(area_m2 * 10.764, 2),  # Convert to square feet
                'width_m': round(width_m, 2),
                'height_m': round(height_m, 2),
                'perimeter_m': round(perimeter_m, 2),
                'bbox': {
                    'min_x': int(min_x),
                    'min_y': int(min_y),
                    'max_x': int(max_x),
                    'max_y': int(max_y)
                },
                'centroid': {
                    'x': int(np.mean(x_coords)),
                    'y': int(np.mean(y_coords))
                }
            }

        self.measurements = measurements
        return measurements

    def get_total_area(self):
        """Calculate total floor area"""
        total_m2 = sum(room['area_m2'] for room in self.measurements.values())
        return {
            'total_area_m2': round(total_m2, 2),
            'total_area_sqft': round(total_m2 * 10.764, 2)
        }

    def get_summary_by_room_type(self):
        """Get area summary grouped by room type"""
        summary = {}

        for room_data in self.measurements.values():
            room_type = room_data['room_type']
            area_m2 = room_data['area_m2']

            if room_type not in summary:
                summary[room_type] = {
                    'count': 0,
                    'total_area_m2': 0,
                    'total_area_sqft': 0
                }

            summary[room_type]['count'] += 1
            summary[room_type]['total_area_m2'] += area_m2
            summary[room_type]['total_area_sqft'] += area_m2 * 10.764

        # Round values
        for room_type in summary:
            summary[room_type]['total_area_m2'] = round(summary[room_type]['total_area_m2'], 2)
            summary[room_type]['total_area_sqft'] = round(summary[room_type]['total_area_sqft'], 2)

        return summary

    def generate_report(self, output_path=None):
        """
        Generate a comprehensive measurement report

        Args:
            output_path: Optional path to save JSON report

        Returns:
            Dictionary containing full measurement report
        """
        report = {
            'scale': {
                'pixels_per_meter': self.pixels_per_meter,
                'description': f'1 meter = {self.pixels_per_meter} pixels'
            },
            'rooms': self.measurements,
            'summary': {
                'total_rooms': len(self.measurements),
                'total_area': self.get_total_area(),
                'by_room_type': self.get_summary_by_room_type()
            }
        }

        if output_path:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)

        return report

    def visualize_measurements(self, image, room_segmentation, show_labels=True,
                              show_dimensions=True, show_areas=True):
        """
        Create visualization with measurement annotations

        Args:
            image: Original RGB floor plan image
            room_segmentation: 2D array with room labels
            show_labels: Show room type labels
            show_dimensions: Show width x height dimensions
            show_areas: Show area values

        Returns:
            Annotated image
        """
        # Create a copy of the image
        annotated = image.copy()
        if len(annotated.shape) == 2:
            annotated = cv2.cvtColor(annotated, cv2.COLOR_GRAY2BGR)

        # Ensure image is in uint8 format
        if annotated.dtype != np.uint8:
            annotated = (annotated * 255).astype(np.uint8) if annotated.max() <= 1.0 else annotated.astype(np.uint8)

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4
        thickness = 1

        for room_key, room_data in self.measurements.items():
            # Get room bounding box and centroid
            bbox = room_data['bbox']
            centroid = room_data['centroid']

            # Draw bounding box
            cv2.rectangle(annotated,
                         (bbox['min_x'], bbox['min_y']),
                         (bbox['max_x'], bbox['max_y']),
                         (0, 255, 0), 1)

            # Prepare text annotations
            texts = []

            if show_labels:
                texts.append(f"{room_data['room_type']}")

            if show_areas:
                texts.append(f"Area: {room_data['area_m2']} m²")

            if show_dimensions:
                texts.append(f"{room_data['width_m']}m x {room_data['height_m']}m")

            # Draw text annotations
            y_offset = centroid['y']
            for i, text in enumerate(texts):
                # Calculate text size for background
                (text_width, text_height), baseline = cv2.getTextSize(
                    text, font, font_scale, thickness)

                # Draw background rectangle for better readability
                bg_y1 = y_offset - text_height - 2
                bg_y2 = y_offset + baseline + 2
                cv2.rectangle(annotated,
                            (centroid['x'] - text_width // 2 - 2, bg_y1),
                            (centroid['x'] + text_width // 2 + 2, bg_y2),
                            (255, 255, 255), -1)

                # Draw text
                cv2.putText(annotated, text,
                          (centroid['x'] - text_width // 2, y_offset),
                          font, font_scale, (0, 0, 0), thickness, cv2.LINE_AA)

                y_offset += text_height + baseline + 5

        return annotated

    def print_report(self):
        """Print a formatted text report to console"""
        if not self.measurements:
            print("No measurements available. Run measure_room_areas() first.")
            return

        print("\n" + "="*80)
        print("FLOOR PLAN MEASUREMENT REPORT")
        print("="*80)
        print(f"\nScale: {self.pixels_per_meter} pixels per meter\n")

        print(f"{'Room':<30} {'Type':<25} {'Area (m²)':<12} {'Area (sqft)':<12} {'Dimensions (m)':<20}")
        print("-"*80)

        for room_key, room_data in sorted(self.measurements.items()):
            room_label = f"Room {room_data['room_id']}"
            room_type = room_data['room_type']
            area_m2 = room_data['area_m2']
            area_sqft = room_data['area_sqft']
            dimensions = f"{room_data['width_m']} x {room_data['height_m']}"

            print(f"{room_label:<30} {room_type:<25} {area_m2:<12.2f} {area_sqft:<12.2f} {dimensions:<20}")

        print("-"*80)

        # Print summary by room type
        print("\nSUMMARY BY ROOM TYPE:")
        print("-"*80)
        summary = self.get_summary_by_room_type()

        for room_type, data in sorted(summary.items()):
            print(f"{room_type:<30} Count: {data['count']:<3} Total Area: {data['total_area_m2']:.2f} m² ({data['total_area_sqft']:.2f} sqft)")

        # Print total
        total = self.get_total_area()
        print("-"*80)
        print(f"{'TOTAL FLOOR AREA:':<30} {total['total_area_m2']:.2f} m² ({total['total_area_sqft']:.2f} sqft)")
        print("="*80 + "\n")


def calibrate_scale_from_reference(reference_length_pixels, reference_length_meters):
    """
    Calculate pixels_per_meter from a known reference measurement

    Args:
        reference_length_pixels: Known length in pixels
        reference_length_meters: Actual length in meters

    Returns:
        pixels_per_meter conversion factor
    """
    return reference_length_pixels / reference_length_meters
