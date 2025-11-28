"""
Batch processing script for measuring multiple floor plans
"""

import os
import glob
import argparse
import numpy as np
import tensorflow as tf
from scipy.misc import imread, imsave, imresize
import csv
import json

from measure import FloorPlanMeasurement

os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Command line arguments
parser = argparse.ArgumentParser(description='Batch Floor Plan Measurement')

parser.add_argument('--input_dir', type=str, default='./demo',
                    help='Directory containing floor plan images')

parser.add_argument('--output_dir', type=str, default='./batch_measurements',
                    help='Directory to save measurement results')

parser.add_argument('--scale', type=float, default=20.0,
                    help='Scale factor: pixels per meter (default: 20.0)')

parser.add_argument('--model_path', type=str, default='./pretrained/pretrained_r3d',
                    help='Path to pretrained model')

parser.add_argument('--pattern', type=str, default='*.jpg',
                    help='File pattern to match (default: *.jpg)')


# Color map
floorplan_map = {
    0: [255, 255, 255], 1: [192, 192, 224], 2: [192, 255, 255],
    3: [224, 255, 192], 4: [255, 224, 128], 5: [255, 160, 96],
    6: [255, 224, 224], 7: [255, 255, 255], 8: [255, 255, 255],
    9: [255, 60, 128], 10: [0, 0, 0]
}


def ind2rgb(ind_im, color_map=floorplan_map):
    """Convert indexed image to RGB using color map"""
    rgb_im = np.zeros((ind_im.shape[0], ind_im.shape[1], 3))
    for i, rgb in color_map.items():
        rgb_im[(ind_im == i)] = rgb
    return rgb_im


def process_floor_plan(sess, graph, image_path, measurer, output_dir):
    """Process a single floor plan image"""

    base_filename = os.path.splitext(os.path.basename(image_path))[0]

    # Load and preprocess image
    im = imread(image_path, mode='RGB')
    im = im.astype(np.float32)
    im_resized = imresize(im, (512, 512, 3)) / 255.

    # Get tensors
    x = graph.get_tensor_by_name('inputs:0')
    room_type_logit = graph.get_tensor_by_name('Cast:0')
    room_boundary_logit = graph.get_tensor_by_name('Cast_1:0')

    # Run inference
    [room_type, room_boundary] = sess.run(
        [room_type_logit, room_boundary_logit],
        feed_dict={x: im_resized.reshape(1, 512, 512, 3)}
    )
    room_type = np.squeeze(room_type)
    room_boundary = np.squeeze(room_boundary)

    # Merge results
    floorplan = room_type.copy()
    floorplan[room_boundary == 1] = 9
    floorplan[room_boundary == 2] = 10

    # Measure
    measurements = measurer.measure_room_areas(floorplan)

    # Save JSON report
    json_path = os.path.join(output_dir, f"{base_filename}_measurements.json")
    report = measurer.generate_report(json_path)

    # Save visualization
    floorplan_rgb = ind2rgb(floorplan)
    annotated = measurer.visualize_measurements(
        floorplan_rgb, floorplan,
        show_labels=True, show_dimensions=True, show_areas=True
    )

    viz_path = os.path.join(output_dir, f"{base_filename}_measured.png")
    imsave(viz_path, annotated)

    return base_filename, report


def main(args):
    # Create output directory
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # Find all floor plan images
    search_pattern = os.path.join(args.input_dir, args.pattern)
    image_paths = sorted(glob.glob(search_pattern))

    if not image_paths:
        print(f"No images found matching pattern: {search_pattern}")
        return

    print("\n" + "="*80)
    print("BATCH FLOOR PLAN MEASUREMENT")
    print("="*80)
    print(f"\nFound {len(image_paths)} floor plan images")
    print(f"Scale: {args.scale} pixels per meter")
    print(f"Output directory: {args.output_dir}\n")

    # Initialize TensorFlow session
    print("Loading model...")
    with tf.Session() as sess:
        # Initialize
        sess.run(tf.group(tf.global_variables_initializer(),
                         tf.local_variables_initializer()))

        # Restore model
        saver = tf.train.import_meta_graph(args.model_path + '.meta')
        saver.restore(sess, args.model_path)
        graph = tf.get_default_graph()

        # Initialize measurer
        measurer = FloorPlanMeasurement(pixels_per_meter=args.scale)

        # Process each image
        all_results = []

        for i, image_path in enumerate(image_paths, 1):
            print(f"Processing [{i}/{len(image_paths)}]: {os.path.basename(image_path)}...")

            try:
                filename, report = process_floor_plan(
                    sess, graph, image_path, measurer, args.output_dir
                )

                all_results.append({
                    'filename': filename,
                    'report': report
                })

                # Print summary
                total_area = report['summary']['total_area']
                num_rooms = report['summary']['total_rooms']
                print(f"  ✓ {num_rooms} rooms, Total area: {total_area['total_area_m2']:.2f} m²")

            except Exception as e:
                print(f"  ✗ Error processing {image_path}: {str(e)}")
                continue

    # Create summary CSV
    print("\nGenerating summary CSV...")
    csv_path = os.path.join(args.output_dir, 'summary.csv')

    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            'Filename', 'Total Rooms', 'Total Area (m²)', 'Total Area (sqft)',
            'Bedrooms', 'Bathrooms', 'Living Rooms', 'Kitchens'
        ])

        for result in all_results:
            filename = result['filename']
            report = result['report']

            total_rooms = report['summary']['total_rooms']
            total_area_m2 = report['summary']['total_area']['total_area_m2']
            total_area_sqft = report['summary']['total_area']['total_area_sqft']

            # Count specific room types
            by_type = report['summary']['by_room_type']
            bedrooms = by_type.get('Bedroom', {}).get('count', 0)
            bathrooms = by_type.get('Bathroom/Washroom', {}).get('count', 0)
            living = by_type.get('Living Room/Kitchen/Dining Room', {}).get('count', 0)

            writer.writerow([
                filename, total_rooms, total_area_m2, total_area_sqft,
                bedrooms, bathrooms, living, 0
            ])

    print(f"Saved summary CSV to: {csv_path}")

    # Save combined JSON report
    combined_json_path = os.path.join(args.output_dir, 'all_measurements.json')
    with open(combined_json_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"Saved combined JSON report to: {combined_json_path}")

    print("\n" + "="*80)
    print(f"BATCH PROCESSING COMPLETE! Processed {len(all_results)} floor plans.")
    print("="*80 + "\n")


if __name__ == '__main__':
    FLAGS, unparsed = parser.parse_known_args()
    main(FLAGS)
