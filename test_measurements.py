"""
Unit tests and validation for measurement accuracy
"""

import unittest
import numpy as np
from measure import FloorPlanMeasurement, calibrate_scale_from_reference


class TestScaleCalibration(unittest.TestCase):
    """Test scale calibration functions"""

    def test_calibrate_scale_basic(self):
        """Test basic scale calibration"""
        scale = calibrate_scale_from_reference(
            reference_length_pixels=100,
            reference_length_meters=5.0
        )
        self.assertEqual(scale, 20.0)

    def test_calibrate_scale_different_values(self):
        """Test scale calibration with different values"""
        scale = calibrate_scale_from_reference(
            reference_length_pixels=250,
            reference_length_meters=10.0
        )
        self.assertEqual(scale, 25.0)


class TestUnitConversions(unittest.TestCase):
    """Test pixel to meter conversions"""

    def setUp(self):
        self.measurer = FloorPlanMeasurement(pixels_per_meter=20.0)

    def test_pixels_to_meters(self):
        """Test pixel to meter conversion"""
        meters = self.measurer.pixels_to_meters(100)
        self.assertAlmostEqual(meters, 5.0, places=2)

        meters = self.measurer.pixels_to_meters(40)
        self.assertAlmostEqual(meters, 2.0, places=2)

    def test_pixels_to_square_meters(self):
        """Test pixel area to square meter conversion"""
        sqm = self.measurer.pixels_to_sqmeters(400)
        self.assertAlmostEqual(sqm, 1.0, places=2)

        sqm = self.measurer.pixels_to_sqmeters(10000)
        self.assertAlmostEqual(sqm, 25.0, places=2)

    def test_set_scale(self):
        """Test changing scale after initialization"""
        self.measurer.set_scale(10.0)
        meters = self.measurer.pixels_to_meters(100)
        self.assertAlmostEqual(meters, 10.0, places=2)


class TestRoomMeasurements(unittest.TestCase):
    """Test room area and dimension measurements"""

    def setUp(self):
        self.measurer = FloorPlanMeasurement(pixels_per_meter=10.0)

    def test_single_square_room(self):
        """Test measuring a single square room"""
        # Create 200x200 pixel floor plan with 100x100 pixel room
        # At 10 pixels/meter, this is 10x10 meters = 100 m²
        floorplan = np.zeros((200, 200), dtype=np.uint8)
        floorplan[50:150, 50:150] = 4  # Bedroom (label 4)

        measurements = self.measurer.measure_room_areas(floorplan)

        self.assertEqual(len(measurements), 1)

        room = list(measurements.values())[0]

        # Check room type
        self.assertEqual(room['room_type'], 'Bedroom')
        self.assertEqual(room['room_type_id'], 4)

        # Check area (allowing small tolerance for boundary effects)
        self.assertAlmostEqual(room['area_m2'], 100.0, delta=2.0)

        # Check dimensions
        self.assertAlmostEqual(room['width_m'], 10.0, delta=0.5)
        self.assertAlmostEqual(room['height_m'], 10.0, delta=0.5)

    def test_rectangular_room(self):
        """Test measuring a rectangular room"""
        # Create 200x300 pixel floor plan with 100x200 pixel room
        # At 10 pixels/meter: 10x20 meters = 200 m²
        floorplan = np.zeros((300, 300), dtype=np.uint8)
        floorplan[50:150, 50:250] = 3  # Living room (label 3)

        measurements = self.measurer.measure_room_areas(floorplan)

        self.assertEqual(len(measurements), 1)

        room = list(measurements.values())[0]

        # Check room type
        self.assertEqual(room['room_type'], 'Living Room/Kitchen/Dining Room')

        # Check area
        self.assertAlmostEqual(room['area_m2'], 200.0, delta=2.0)

        # Check dimensions
        self.assertAlmostEqual(room['width_m'], 20.0, delta=0.5)
        self.assertAlmostEqual(room['height_m'], 10.0, delta=0.5)

    def test_multiple_rooms(self):
        """Test measuring multiple rooms"""
        floorplan = np.zeros((300, 300), dtype=np.uint8)

        # Room 1: Bedroom (50x50 pixels = 5x5 m = 25 m²)
        floorplan[50:100, 50:100] = 4

        # Room 2: Bathroom (40x40 pixels = 4x4 m = 16 m²)
        floorplan[150:190, 150:190] = 2

        # Room 3: Living room (60x80 pixels = 6x8 m = 48 m²)
        floorplan[50:110, 150:230] = 3

        measurements = self.measurer.measure_room_areas(floorplan)

        # Should detect 3 rooms
        self.assertEqual(len(measurements), 3)

        # Check total area
        total = self.measurer.get_total_area()
        expected_total = 25 + 16 + 48
        self.assertAlmostEqual(total['total_area_m2'], expected_total, delta=5.0)

    def test_room_with_walls(self):
        """Test measuring rooms with wall boundaries"""
        floorplan = np.zeros((200, 200), dtype=np.uint8)

        # Create room with walls
        floorplan[50:150, 50:150] = 4  # Bedroom
        floorplan[49:51, 50:150] = 10  # Top wall
        floorplan[149:151, 50:150] = 10  # Bottom wall
        floorplan[50:150, 49:51] = 10  # Left wall
        floorplan[50:150, 149:151] = 10  # Right wall

        measurements = self.measurer.measure_room_areas(floorplan)

        # Should still detect the room (walls excluded)
        self.assertEqual(len(measurements), 1)

        room = list(measurements.values())[0]
        self.assertEqual(room['room_type'], 'Bedroom')

    def test_small_noise_filtered(self):
        """Test that small noise regions are filtered out"""
        floorplan = np.zeros((200, 200), dtype=np.uint8)

        # Large room
        floorplan[50:150, 50:150] = 4

        # Small noise (< 100 pixels should be filtered)
        floorplan[10:15, 10:15] = 2  # Only 25 pixels

        measurements = self.measurer.measure_room_areas(floorplan)

        # Should only detect the large room, not noise
        self.assertEqual(len(measurements), 1)


class TestSummaryFunctions(unittest.TestCase):
    """Test summary and reporting functions"""

    def setUp(self):
        self.measurer = FloorPlanMeasurement(pixels_per_meter=10.0)

        # Create test floor plan with multiple rooms
        floorplan = np.zeros((300, 300), dtype=np.uint8)
        floorplan[50:100, 50:100] = 4  # Bedroom 1
        floorplan[120:170, 50:100] = 4  # Bedroom 2
        floorplan[50:120, 120:200] = 2  # Bathroom
        floorplan[140:240, 120:240] = 3  # Living room

        self.measurer.measure_room_areas(floorplan)

    def test_get_total_area(self):
        """Test total area calculation"""
        total = self.measurer.get_total_area()

        self.assertIn('total_area_m2', total)
        self.assertIn('total_area_sqft', total)
        self.assertGreater(total['total_area_m2'], 0)

    def test_get_summary_by_room_type(self):
        """Test summary grouped by room type"""
        summary = self.measurer.get_summary_by_room_type()

        # Should have Bedroom, Bathroom, Living Room
        self.assertIn('Bedroom', summary)
        self.assertIn('Bathroom/Washroom', summary)
        self.assertIn('Living Room/Kitchen/Dining Room', summary)

        # Bedroom count should be 2
        self.assertEqual(summary['Bedroom']['count'], 2)

        # Each summary should have required fields
        for room_type, data in summary.items():
            self.assertIn('count', data)
            self.assertIn('total_area_m2', data)
            self.assertIn('total_area_sqft', data)

    def test_generate_report(self):
        """Test report generation"""
        report = self.measurer.generate_report()

        # Check report structure
        self.assertIn('scale', report)
        self.assertIn('rooms', report)
        self.assertIn('summary', report)

        # Check scale info
        self.assertEqual(report['scale']['pixels_per_meter'], 10.0)

        # Check summary
        self.assertIn('total_rooms', report['summary'])
        self.assertIn('total_area', report['summary'])
        self.assertIn('by_room_type', report['summary'])


class TestAccuracy(unittest.TestCase):
    """Test measurement accuracy with known ground truth"""

    def test_known_dimensions_accuracy(self):
        """Test accuracy with precise known dimensions"""
        # Create exact 100x100 pixel room at 20 pixels/meter
        # Expected: 5x5 meters = 25 m²
        measurer = FloorPlanMeasurement(pixels_per_meter=20.0)

        floorplan = np.zeros((200, 200), dtype=np.uint8)
        floorplan[50:150, 50:150] = 4  # Exactly 100x100 pixels

        measurements = measurer.measure_room_areas(floorplan)
        room = list(measurements.values())[0]

        ground_truth_area = 25.0
        measured_area = room['area_m2']
        error_percent = abs(measured_area - ground_truth_area) / ground_truth_area * 100

        # Error should be less than 5%
        self.assertLess(error_percent, 5.0,
                       f"Measurement error {error_percent:.2f}% exceeds 5% threshold")

    def test_multiple_scales(self):
        """Test that different scales give proportional results"""
        floorplan = np.zeros((200, 200), dtype=np.uint8)
        floorplan[50:150, 50:150] = 4

        # Measure with scale 10
        measurer1 = FloorPlanMeasurement(pixels_per_meter=10.0)
        measurements1 = measurer1.measure_room_areas(floorplan)
        area1 = list(measurements1.values())[0]['area_m2']

        # Measure with scale 20
        measurer2 = FloorPlanMeasurement(pixels_per_meter=20.0)
        measurements2 = measurer2.measure_room_areas(floorplan)
        area2 = list(measurements2.values())[0]['area_m2']

        # area1 should be 4x area2 (because scale doubled)
        ratio = area1 / area2
        self.assertAlmostEqual(ratio, 4.0, delta=0.2)


def run_validation_tests():
    """Run all tests and print results"""
    print("\n" + "="*80)
    print("RUNNING MEASUREMENT VALIDATION TESTS")
    print("="*80 + "\n")

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestScaleCalibration))
    suite.addTests(loader.loadTestsFromTestCase(TestUnitConversions))
    suite.addTests(loader.loadTestsFromTestCase(TestRoomMeasurements))
    suite.addTests(loader.loadTestsFromTestCase(TestSummaryFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestAccuracy))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✓ ALL TESTS PASSED! Measurement system is working correctly.")
    else:
        print("\n✗ SOME TESTS FAILED! Please review the errors above.")

    print("="*80 + "\n")

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_validation_tests()
    exit(0 if success else 1)
