import numpy as np


def acrd_function(x):
    """
    Ascending Cosine Roll-down (ACRD) function.
    As described in the paper: Saliency Segmentation Oriented Deep Image Compression.
    This function helps in allocating bits to important pixels.
    """
    # Normalized x should be in [0, 1]
    # f(x) = 0.5 * (1 + cos(pi * (1 - x))) = 0.5 * (1 - cos(pi * x))
    return 0.5 * (1 - np.cos(np.pi * x))


def allocate_bits(
    saliency_map,
    object_map=None,
    spectral_map=None,
    threshold=0.1,
    gamma=1.0,
    weight_floor=0.0,
    weight_ceiling=1.0,
):
    """
    Allocates bit weights based on the combined saliency, object, and spectral maps
    using the ACRD function.

    saliency_map:   2D numpy array [0, 1] from U2Net
    object_map:     2D binary numpy array from YOLO (optional)
    spectral_map:   2D numpy array [0, 1] from Spectral Residual (optional)
    threshold:      Pixels below this saliency score are treated as pure background.
    gamma:          Power applied after ACRD to reshape the weight distribution.
                    > 1.0 → steeper curve, weights pushed toward 0 or 1 (more binary).
                      Used for Storage preset to create a hard foreground/background split.
                    < 1.0 → softer curve, smooth gradients across the image.
                      Used for Quality preset to preserve gentle transitions.
                    = 1.0 → standard ACRD curve (Balanced preset).
    weight_floor:   Minimum bit weight for ALL pixels, including background.
                    0.0 for Storage/Balanced (background gets no enhancement).
                    > 0 for Quality (background still receives some quality budget).
    weight_ceiling: Maximum bit weight cap. Lowering it reserves bits by capping the
                    maximum quality given to any single pixel — useful for Storage.
    """
    # 1. Combine maps using element-wise maximum (OR-style fusion)
    combined_map = saliency_map.copy()

    if object_map is not None:
        if object_map.shape != combined_map.shape:
            from PIL import Image
            obj_img = Image.fromarray(object_map).resize(
                (combined_map.shape[1], combined_map.shape[0]), resample=Image.BILINEAR
            )
            object_map = np.array(obj_img)
        combined_map = np.maximum(combined_map, object_map)

    if spectral_map is not None:
        if spectral_map.shape != combined_map.shape:
            from PIL import Image
            spec_img = Image.fromarray(spectral_map).resize(
                (combined_map.shape[1], combined_map.shape[0]), resample=Image.BILINEAR
            )
            spectral_map = np.array(spec_img)
        # Boost spectral map by 1.45× before fusion so it punches through more
        # strongly and triggers foreground-lossless treatment for high-frequency
        # regions the semantic detectors might miss (fine texture, sharp edges).
        spectral_boosted = np.clip(spectral_map * 1.45, 0.0, 1.0)
        combined_map = np.maximum(combined_map, spectral_boosted)

    # 2. Hard threshold — pixels below this become exactly 0
    combined_map_thresholded = np.where(combined_map < threshold, 0.0, combined_map)

    # 3. ACRD function maps saliency scores to bit-allocation weights
    bit_weights = acrd_function(combined_map_thresholded)

    # 4. Gamma correction on the ACRD output
    #    gamma > 1: compresses weights toward 0, making the curve steeper (more aggressive
    #               background suppression — Storage preset).
    #    gamma < 1: expands mid-range weights upward, giving smoother transitions
    #               and higher quality in moderately salient regions (Quality preset).
    if gamma != 1.0:
        bit_weights = np.power(np.clip(bit_weights, 0.0, 1.0), gamma)

    # 5. Apply floor and ceiling
    #    floor ensures background pixels still receive a baseline quality level (Quality preset).
    #    ceiling reserves headroom so the most salient pixels don't monopolise the bit budget
    #    while still outcompressing the background (Storage preset).
    bit_weights = np.clip(bit_weights, weight_floor, weight_ceiling)

    return bit_weights
