"""
Demo script for automated floor plan measurement
Combines floor plan recognition with automatic measurement capabilities
"""

import os
import argparse
import numpy as np
import tensorflow as tf
from scipy.misc import imread, imsave, imresize
from matplotlib import pyplot as plt
import cv2

from measure import FloorPlanMeasurement

os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Command line arguments
parser = argparse.ArgumentParser(description='Floor Plan Measurement Demo')

parser.add_argument('--im_path', type=str, default='./demo/45765448.jpg',
                    help='Input floor plan image path')

parser.add_argument('--scale', type=float, default=20.0,
                    help='Scale factor: pixels per meter (default: 20.0)')

parser.add_argument('--output_dir', type=str, default='./measurements',
                    help='Directory to save measurement results')

parser.add_argument('--save_viz', action='store_true',
                    help='Save visualization image with measurements')

parser.add_argument('--save_json', action='store_true',
                    help='Save measurement report as JSON')

parser.add_argument('--model_path', type=str, default='./pretrained/pretrained_r3d',
                    help='Path to pretrained model')


# Color map for floor plan visualization
floorplan_map = {
    0: [255, 255, 255],  # background
    1: [192, 192, 224],  # closet
    2: [192, 255, 255],  # bathroom/washroom
    3: [224, 255, 192],  # living room/kitchen/dining room
    4: [255, 224, 128],  # bedroom
    5: [255, 160, 96],   # hall
    6: [255, 224, 224],  # balcony
    7: [255, 255, 255],  # not used
    8: [255, 255, 255],  # not used
    9: [255, 60, 128],   # door & window
    10: [0, 0, 0]        # wall
}


def ind2rgb(ind_im, color_map=floorplan_map):
    """Convert indexed image to RGB using color map"""
    rgb_im = np.zeros((ind_im.shape[0], ind_im.shape[1], 3))
    for i, rgb in color_map.items():
        rgb_im[(ind_im == i)] = rgb
    return rgb_im


def main(args):
    # Create output directory
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # Extract filename for saving results
    base_filename = os.path.splitext(os.path.basename(args.im_path))[0]

    print("\n" + "="*80)
    print("AUTOMATED FLOOR PLAN MEASUREMENT")
    print("="*80)
    print(f"\nInput image: {args.im_path}")
    print(f"Scale: {args.scale} pixels per meter")
    print(f"Output directory: {args.output_dir}\n")

    # Load input image
    print("Loading floor plan image...")
    im = imread(args.im_path, mode='RGB')
    original_shape = im.shape[:2]
    im = im.astype(np.float32)
    im_resized = imresize(im, (512, 512, 3)) / 255.

    # Run floor plan recognition
    print("Running floor plan recognition...")
    with tf.Session() as sess:
        # Initialize
        sess.run(tf.group(tf.global_variables_initializer(),
                         tf.local_variables_initializer()))

        # Restore pretrained model
        saver = tf.train.import_meta_graph(args.model_path + '.meta')
        saver.restore(sess, args.model_path)

        # Get default graph
        graph = tf.get_default_graph()

        # Restore inputs & outputs tensor
        x = graph.get_tensor_by_name('inputs:0')
        room_type_logit = graph.get_tensor_by_name('Cast:0')
        room_boundary_logit = graph.get_tensor_by_name('Cast_1:0')

        # Infer results
        [room_type, room_boundary] = sess.run(
            [room_type_logit, room_boundary_logit],
            feed_dict={x: im_resized.reshape(1, 512, 512, 3)}
        )
        room_type = np.squeeze(room_type)
        room_boundary = np.squeeze(room_boundary)

    # Merge results - create floor plan with room types and boundaries
    floorplan = room_type.copy()
    floorplan[room_boundary == 1] = 9  # doors/windows
    floorplan[room_boundary == 2] = 10  # walls

    print("Floor plan recognition complete!\n")

    # Initialize measurement system
    print("Calculating measurements...")
    measurer = FloorPlanMeasurement(pixels_per_meter=args.scale)

    # Measure room areas and dimensions
    measurements = measurer.measure_room_areas(floorplan)

    print(f"Found {len(measurements)} rooms\n")

    # Print measurement report to console
    measurer.print_report()

    # Save JSON report if requested
    if args.save_json:
        json_path = os.path.join(args.output_dir, f"{base_filename}_measurements.json")
        measurer.generate_report(json_path)
        print(f"Saved measurement report to: {json_path}")

    # Create and save visualization
    if args.save_viz or True:  # Always save visualization
        print("\nGenerating visualization...")

        # Create floor plan RGB visualization
        floorplan_rgb = ind2rgb(floorplan)

        # Create annotated version with measurements
        annotated = measurer.visualize_measurements(
            floorplan_rgb,
            floorplan,
            show_labels=True,
            show_dimensions=True,
            show_areas=True
        )

        # Save visualizations
        viz_path = os.path.join(args.output_dir, f"{base_filename}_floorplan.png")
        imsave(viz_path, floorplan_rgb.astype(np.uint8))
        print(f"Saved floor plan visualization to: {viz_path}")

        annotated_path = os.path.join(args.output_dir, f"{base_filename}_measured.png")
        imsave(annotated_path, annotated)
        print(f"Saved annotated floor plan to: {annotated_path}")

        # Display results
        plt.figure(figsize=(15, 5))

        plt.subplot(131)
        plt.imshow(im_resized)
        plt.title('Original Image')
        plt.axis('off')

        plt.subplot(132)
        plt.imshow(floorplan_rgb / 255.)
        plt.title('Detected Floor Plan')
        plt.axis('off')

        plt.subplot(133)
        plt.imshow(annotated)
        plt.title('Measurements')
        plt.axis('off')

        plt.tight_layout()

        # Save comparison figure
        comparison_path = os.path.join(args.output_dir, f"{base_filename}_comparison.png")
        plt.savefig(comparison_path, dpi=150, bbox_inches='tight')
        print(f"Saved comparison figure to: {comparison_path}")

        plt.show()

    print("\n" + "="*80)
    print("MEASUREMENT COMPLETE!")
    print("="*80 + "\n")


if __name__ == '__main__':
    FLAGS, unparsed = parser.parse_known_args()
    main(FLAGS)
