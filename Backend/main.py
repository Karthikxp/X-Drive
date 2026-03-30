import json
import os
import shutil
import argparse
from PIL import Image, ImageOps
import pillow_avif  # For AVIF support
import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Preset definitions — each preset tunes every layer of the pipeline:
#
#   Strategy: foreground-lossless compression.
#     Foreground pixels (U2Net + YOLOv8 + spectral saliency) → original pixels,
#     zero compression loss.  Background → heavily pre-processed base layer.
#     final[px] = (1 - w) * base[px] + w * original[px]
#
#   avif_quality        : final AVIF encoder quality.  Must be HIGH (85-95) so
#                         the encoder does not re-introduce artefacts on the
#                         already-lossless foreground pixels.  File-size savings
#                         come from the pre-degraded background, not from lossy
#                         AVIF encoding.
#   base_quality        : how aggressively the background layer is pre-degraded [0–1]
#   enhancement_quality : legacy parameter, no longer used (kept for CLI compat)
#   saliency_threshold  : pixels below this score are treated as pure background
#   gamma               : reshapes ACRD curve (>1 = harder fg/bg split)
#   weight_floor        : minimum weight for all pixels (0 = pure base for bg)
#   weight_ceiling      : MUST be 1.0 to allow truly lossless foreground pixels
#   downsample_factor   : spatial downsampling factor for base (background) layer
#   base_blur_multiplier: blur multiplier for base (background) layer
# ---------------------------------------------------------------------------
PRESETS = {
    'storage': {
        'avif_quality':          85,   # high — compression comes from bg preprocessing
        'base_quality':          0.04,
        'enhancement_quality':   0.82, # legacy, unused
        'saliency_threshold':    0.20,
        'gamma':                 1.8,  # hard binary fg/bg split
        'weight_floor':          0.0,
        'weight_ceiling':        1.0,  # must be 1.0 for lossless foreground
        'downsample_factor':     9,
        'base_blur_multiplier':  4.0,
    },
    'balanced': {
        'avif_quality':          90,
        'base_quality':          0.10,
        'enhancement_quality':   0.90, # legacy, unused
        'saliency_threshold':    0.15,
        'gamma':                 1.2,
        'weight_floor':          0.0,
        'weight_ceiling':        1.0,
        'downsample_factor':     6,
        'base_blur_multiplier':  2.8,
    },
    'quality': {
        'avif_quality':          95,
        'base_quality':          0.18,
        'enhancement_quality':   0.95, # legacy, unused
        'saliency_threshold':    0.08,
        'gamma':                 0.8,
        'weight_floor':          0.08,
        'weight_ceiling':        1.0,
        'downsample_factor':     4,
        'base_blur_multiplier':  1.8,
    },
}

# Import custom modules
from modules.saliency import get_saliency_map, download_weights
from modules.object_detection import get_object_segmentation_map
from modules.saliency_spectral import detect_spectral_residual
from modules.bit_allocation import allocate_bits
from modules.compression import layered_compression


def main():
    parser = argparse.ArgumentParser(description="Saliency Segmentation Oriented Deep Image Compression")
    parser.add_argument("--input", type=str, required=True, help="Path to input image")
    parser.add_argument("--output_dir", type=str, default="output", help="Directory for outputs")
    parser.add_argument("--base_quality", type=float, default=0.1, help="Quality for base layer (0.0-1.0)")
    parser.add_argument("--enhancement_quality", type=float, default=0.9, help="Quality for enhancement layer (0.0-1.0)")
    parser.add_argument("--avif_quality", type=int, default=28, help="AVIF export quality (1-100)")
    parser.add_argument("--saliency_threshold", type=float, default=0.15, help="Threshold for saliency enhancement")
    parser.add_argument("--use_yolo", action="store_true", default=True, help="Use YOLO segmentation to enhance saliency")
    parser.add_argument("--use_spectral", action="store_true", default=True, help="Use Spectral Residual saliency to enhance")
    parser.add_argument("--storage_dir", type=str, default=None, help="Directory to save the final compressed AVIF (overrides default storage/ folder)")
    parser.add_argument("--originals_dir", type=str, default=None, help="Directory to move the original input file after compression")
    parser.add_argument("--preset", type=str, default="balanced", choices=["storage", "balanced", "quality"],
                        help="Compression preset: storage (max compression), balanced (default), quality (best fidelity)")

    args = parser.parse_args()

    # Resolve preset — individual flags override preset values if explicitly passed
    p = PRESETS[args.preset]
    avif_quality        = p['avif_quality']
    base_quality        = p['base_quality']
    enhancement_quality = p['enhancement_quality']
    saliency_threshold  = p['saliency_threshold']
    gamma               = p['gamma']
    weight_floor        = p['weight_floor']
    weight_ceiling      = p['weight_ceiling']
    downsample_factor   = p['downsample_factor']
    base_blur_multiplier = p['base_blur_multiplier']

    print(f"[preset={args.preset}] avif_quality={avif_quality}, saliency_threshold={saliency_threshold}, gamma={gamma}, weight_floor={weight_floor}, ceiling={weight_ceiling}, downsample={downsample_factor}x, blur_mult={base_blur_multiplier}")

    # 1. Create output directory and get input filename prefix
    os.makedirs(args.output_dir, exist_ok=True)
    input_filename = os.path.basename(args.input).split('.')[0]

    print(f"--- Starting Compression Pipeline for: {args.input} ---")

    # 2. Saliency Detection (U2NetP)
    print("Step 1a: Running Saliency Detection (U2NetP)...")
    weight_path = download_weights("models")
    saliency_map = get_saliency_map(args.input, weight_path)

    # 3. Object Detection (YOLOv8 Nano Seg)
    object_map = None
    if args.use_yolo:
        print("Step 1b: Running Object Segmentation (YOLOv8n-seg)...")
        object_map = get_object_segmentation_map(args.input)

        # # Save Object Map
        # obj_img = Image.fromarray((object_map * 255).astype(np.uint8))
        # obj_path = os.path.join(args.output_dir, f"{input_filename}_step1b_object_map.png")
        # obj_img.save(obj_path)
        # print(f"Saved object map to {obj_path}")

    # 4. Spectral Saliency
    spectral_map = None
    if args.use_spectral:
        print("Step 1c: Running Spectral Residual Saliency...")
        spectral_map = detect_spectral_residual(args.input)

        # # Save Spectral Map
        # spec_img = Image.fromarray((spectral_map * 255).astype(np.uint8))
        # spec_path = os.path.join(args.output_dir, f"{input_filename}_step1c_spectral_map.png")
        # spec_img.save(spec_path)
        # print(f"Saved spectral map to {spec_path}")

    # # Save Saliency Map
    # sal_img = Image.fromarray((saliency_map * 255).astype(np.uint8))
    # sal_path = os.path.join(args.output_dir, f"{input_filename}_step1a_saliency_map.png")
    # sal_img.save(sal_path)
    # print(f"Saved saliency map to {sal_path}")

    # 5. Bit Allocation (ACRD Function)
    print(f"Step 2: Calculating Combined Bit Allocation (ACRD, threshold={saliency_threshold}, gamma={gamma}, floor={weight_floor}, ceiling={weight_ceiling})...")
    bit_weights = allocate_bits(
        saliency_map,
        object_map=object_map,
        spectral_map=spectral_map,
        threshold=saliency_threshold,
        gamma=gamma,
        weight_floor=weight_floor,
        weight_ceiling=weight_ceiling,
    )

    # # Save Bit Weight Map (Visual Representation)
    # bw_img = Image.fromarray((bit_weights * 255).astype(np.uint8))
    # bw_path = os.path.join(args.output_dir, f"{input_filename}_step2_bit_weights.png")
    # bw_img.save(bw_path)
    # print(f"Saved bit weight map to {bw_path}")

    # 4. Layered Compression (Base + Enhancement)
    print("Step 3: Performing Layered Compression...")
    final_img, base_img, _original_ref = layered_compression(
        args.input,
        bit_weights,
        base_quality=base_quality,
        enhancement_quality=enhancement_quality,
        downsample_factor=downsample_factor,
        base_blur_multiplier=base_blur_multiplier,
    )

    # # Save Intermediate and Final Results
    # base_path = os.path.join(args.output_dir, f"{input_filename}_step3_base_layer.png")
    # base_img.save(base_path)

    if args.storage_dir:
        storage_dir = args.storage_dir
    else:
        storage_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")
    os.makedirs(storage_dir, exist_ok=True)
    final_path = os.path.join(storage_dir, f"{input_filename}_step4_final_compressed.avif")
    final_img.save(final_path, format="AVIF", quality=avif_quality, subsampling='4:2:0')  # Optimized AVIF
    print(f"Saved final compressed image to {final_path}")

    # Copy original NOW so it's available for comparison as soon as the AVIF is detected
    if args.originals_dir:
        os.makedirs(args.originals_dir, exist_ok=True)
        orig_dest = os.path.join(args.originals_dir, os.path.basename(args.input))
        shutil.copy2(args.input, orig_dest)
        print(f"Copied original to {orig_dest}")

    # 5. Compression Metrics
    print("\n--- Compression Metrics ---")
    orig_size = os.path.getsize(args.input)
    comp_size = os.path.getsize(final_path)
    ratio = orig_size / comp_size if comp_size > 0 else 0

    print(f"Original Image Size: {orig_size / 1024:.2f} KB")
    print(f"Compressed Image Size: {comp_size / 1024:.2f} KB")
    print(f"Compression Ratio: {ratio:.2f}x")
    print("--------------------------\n")

    # Save compression stats as a sidecar JSON next to the compressed file
    stats = {"originalSize": orig_size, "compressedSize": comp_size, "ratio": round(ratio, 2)}
    stats_path = os.path.join(storage_dir, f"{input_filename}_stats.json")
    with open(stats_path, 'w') as f:
        json.dump(stats, f)

    # 7. Visual Summary (Optional)
    print("Generating visual summary...")
    num_plots = 4 + args.use_yolo + args.use_spectral
    fig, axes = plt.subplots(1, num_plots, figsize=(5 * num_plots, 5))
    orig_img = ImageOps.exif_transpose(Image.open(args.input))

    idx = 0
    axes[idx].imshow(orig_img)
    axes[idx].set_title("Original Image")
    idx += 1

    axes[idx].imshow(saliency_map, cmap='gray')
    axes[idx].set_title("Saliency (U2NetP)")
    idx += 1

    if args.use_yolo:
        axes[idx].imshow(object_map, cmap='gray')
        axes[idx].set_title("Objects (YOLOv8n)")
        idx += 1

    if args.use_spectral:
        axes[idx].imshow(spectral_map, cmap='gray')
        axes[idx].set_title("Saliency (Spectral)")
        idx += 1

    axes[idx].imshow(base_img)
    axes[idx].set_title(f"Background (compressed, Q={base_quality})")
    idx += 1

    axes[idx].imshow(final_img)
    axes[idx].set_title(f"Final [{args.preset}] — fg lossless (Ratio: {ratio:.2f}x)")

    for ax in axes:
        ax.axis('off')

    summary_path = os.path.join(args.output_dir, f"{input_filename}_compression_summary.png")
    plt.savefig(summary_path)
    print(f"Saved visual summary to {summary_path}")

    print("\n--- Pipeline Completed Successfully ---")

    # Remove the original from user_photos (already copied to originals/ above)
    try:
        os.remove(args.input)
        print(f"Cleaned up input file: {args.input}")
    except OSError as e:
        print(f"Warning: could not remove input file {args.input}: {e}")


if __name__ == "__main__":
    main()
