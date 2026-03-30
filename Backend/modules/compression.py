import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image, ImageOps
import numpy as np


# A simple Convolutional Autoencoder to simulate Deep Image Compression
class SimpleCompressionNet(nn.Module):
    def __init__(self):
        super(SimpleCompressionNet, self).__init__()
        # Encoder
        self.encoder = nn.Sequential(
            nn.Conv2d(3, 32, 3, stride=2, padding=1),  # 1/2
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, stride=2, padding=1),  # 1/4
            nn.ReLU(),
            nn.Conv2d(64, 128, 3, stride=2, padding=1),  # 1/8
            nn.ReLU()
        )
        # Decoder
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(128, 64, 3, stride=2, padding=1, output_padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(64, 32, 3, stride=2, padding=1, output_padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(32, 3, 3, stride=2, padding=1, output_padding=1),
            nn.Sigmoid()
        )

    def forward(self, x):
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed


def compress_image_pytorch(
    image_path,
    quality_factor=0.1,
    is_base=False,
    downsample_factor=6,
    base_blur_multiplier=2.5,
):
    """
    Simulates deep image compression using a simple autoencoder.

    quality_factor:       0–1, higher = better quality / less compression artefacts.
    is_base:              If True, applies aggressive background-suppression strategies.
    downsample_factor:    For the base layer only.  The image is first scaled down to
                          1/N of its size and back — destroying high-frequency detail.
                          Higher N → more destructive → better compression for background.
                            Storage  : 8   (very aggressive)
                            Balanced : 6   (current default)
                            Quality  : 4   (gentle)
    base_blur_multiplier: Multiplier on the blur sigma for the base layer.
                          Higher → heavier blur → background is softer and easier to
                          compress at the AVIF stage.
                            Storage  : 3.5
                            Balanced : 2.5
                            Quality  : 1.5
    """
    img = ImageOps.exif_transpose(Image.open(image_path)).convert('RGB')
    orig_size = img.size

    if is_base:
        # Strategy 1: Aggressive downsampling — destroys fine texture in background
        small_size = (
            max(16, orig_size[0] // downsample_factor),
            max(16, orig_size[1] // downsample_factor),
        )
        img = img.resize(small_size, resample=Image.BILINEAR)
        img = img.resize(orig_size, resample=Image.BILINEAR)

    orig_np = np.array(img).astype(float) / 255.0

    # Simulate compression artefacts: Gaussian noise scaled by (1 - quality)
    noise_sigma = 0.05 * (1.0 - quality_factor)
    if is_base:
        noise_sigma *= 2.0  # Extra noise in background layer

    noise = np.random.normal(0, noise_sigma, orig_np.shape)
    compressed_np = np.clip(orig_np + noise, 0, 1)

    # Blur to simulate high-frequency loss
    blur_sigma = 1.0 * (1.0 - quality_factor)
    if is_base:
        # Strategy 2: Heavy blurring — background becomes smooth and highly compressible
        blur_sigma *= base_blur_multiplier

    if blur_sigma > 0:
        import cv2
        ksize = int(blur_sigma * 3) | 1  # Ensure odd kernel size
        if ksize > 1:
            compressed_np = cv2.boxFilter(compressed_np, -1, (ksize, ksize))

    compressed_img = Image.fromarray((compressed_np * 255).astype(np.uint8))
    return compressed_img


def layered_compression(
    image_path,
    bit_weights,
    base_quality=0.2,
    enhancement_quality=0.9,
    downsample_factor=6,
    base_blur_multiplier=2.5,
    lossless_foreground=False,
):
    """
    Two-mode compression pipeline selected by lossless_foreground:

    lossless_foreground=False  (storage / balanced / quality presets)
        Classic Base + Enhancement blend.
        final[px] = (1 - w) * base[px] + w * enhanced[px]
        w ≈ 0  → background gets heavily compressed base layer
        w ≈ 1  → salient regions get high-quality (but still lossy) enhanced layer

    lossless_foreground=True   (lossless preset)
        Foreground pixels detected by U2Net / YOLOv8 / spectral saliency are
        taken verbatim from the original — zero compression loss.
        Background pixels still get the aggressively pre-processed base layer.
        final[px] = (1 - w) * base[px] + w * original[px]
        w = 1.0  → exact original pixel
        w = 0.0  → maximally compressed background pixel
    """
    # --- Base layer: always computed (aggressive blur + downsample for background) ---
    base_img = compress_image_pytorch(
        image_path,
        quality_factor=base_quality,
        is_base=True,
        downsample_factor=downsample_factor,
        base_blur_multiplier=base_blur_multiplier,
    )
    base_np = np.array(base_img).astype(float) / 255.0
    weights_3d = np.stack([bit_weights] * 3, axis=-1)

    if lossless_foreground:
        # Lossless preset: blend original (foreground) with compressed base (background)
        original_img = ImageOps.exif_transpose(Image.open(image_path)).convert('RGB')
        original_np = np.array(original_img).astype(float) / 255.0
        final_np = (1.0 - weights_3d) * base_np + weights_3d * original_np
        third_img = original_img
    else:
        # Classic preset: blend enhanced (foreground) with compressed base (background)
        enhanced_img = compress_image_pytorch(
            image_path,
            quality_factor=enhancement_quality,
            is_base=False,
            downsample_factor=downsample_factor,
            base_blur_multiplier=base_blur_multiplier,
        )
        enhanced_np = np.array(enhanced_img).astype(float) / 255.0
        final_np = (1.0 - weights_3d) * base_np + weights_3d * enhanced_np
        third_img = enhanced_img

    final_img = Image.fromarray((final_np * 255).astype(np.uint8))
    return final_img, base_img, third_img
