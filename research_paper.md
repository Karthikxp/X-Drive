# Saliency-Guided Bit Allocation for Context-Aware Image Compression

**Kailash S · Karthik M**  
Department of Computer Science and Engineering  
CS22811 – Project Work · Batch 23  
Guide: Dr. N. Revathi

---

## Abstract

We present a context-aware image compression framework that allocates encoding resources non-uniformly across an image by estimating perceptual importance at the pixel level. The system fuses three complementary saliency signals — a deep salient-object detector (U²-NetP, `saliency.py`), a semantic instance segmenter (YOLOv8n-seg, `object_detection.py`), and a multi-scale frequency-domain analyser (Spectral Residual, `saliency_spectral.py`) — into a unified importance map through element-wise maximum fusion (`bit_allocation.py`). That map is then transformed into per-pixel compression weights using the Ascending Cosine Roll-down (ACRD) function, shaped further by gamma correction and floor/ceiling constraints. A two-layer blending pipeline (`compression.py`) applies aggressive background suppression to low-importance regions while preserving foreground fidelity at the pixel level, with a dedicated lossless foreground mode that writes exact original pixels for detected subjects. The framework requires no manual annotation and no end-to-end codec training.

---

## 1. Introduction

Standard image compression codecs apply a spatially uniform quality parameter: every pixel is encoded with equal fidelity regardless of whether it depicts a human face or empty sky. This uniformity is perceptually wasteful. The human visual system is highly sensitive to distortions in salient regions — faces, objects, foreground subjects — and largely tolerant of artefacts in backgrounds and smooth areas.

Non-uniform compression requires answering one question: *which pixels matter?* Answering that question reliably is difficult with any single detector. Deep salient-object detectors produce holistic prominence scores but smooth over fine structural boundaries. Semantic instance segmenters identify category-labelled objects precisely but miss visually prominent elements outside their training vocabulary. Frequency-domain methods capture statistical novelty — edges, fine textures, repeating patterns — but are agnostic to semantic content. All three signals are useful; none is sufficient alone.

This work presents a pipeline that:

1. Runs all three detectors independently on the input image.
2. Fuses their outputs into a single combined map using element-wise maximum (OR-style fusion).
3. Converts the fused map to per-pixel bit-allocation weights via the ACRD transfer function with gamma shaping.
4. Uses those weights to drive a two-layer spatial blending pipeline that produces a pre-processed image in which unimportant regions have been aggressively degraded while important regions are preserved.

---

## 2. System Architecture

The five modules form a strict feed-forward pipeline:

```
Input Image
    │
    ├──[saliency.py]──────────────► S_deep  ∈ [0,1]^(H×W)   (U²-NetP)
    ├──[object_detection.py]──────► S_obj   ∈ [0,1]^(H×W)   (YOLOv8n-seg union mask)
    └──[saliency_spectral.py]─────► S_spec  ∈ [0,1]^(H×W)   (multi-scale spectral residual)
              │
              ▼
    [bit_allocation.py]
        Max-fusion → threshold → ACRD → gamma → floor/ceiling
              │
              ▼  W ∈ [weight_floor, weight_ceiling]^(H×W)
              │
    [compression.py]
        Base layer  (aggressive downsample + blur + noise)
        Fore layer  (high-quality or exact original)
        Final = (1 − W)·Base + W·Fore
              │
              ▼
        Pre-processed output image
```

No module communicates with any other except through the numpy arrays shown above. The design makes each stage independently testable and replaceable.

---

## 3. Module 1 — Deep Saliency Detection (`saliency.py`)

### 3.1 Architecture: U²-NetP

`saliency.py` implements the U²-NetP architecture (the lightweight pooling variant of U²-Net) entirely in PyTorch. The architecture is built from three classes.

**`REBNCONV`** is the atomic building block. It wraps a single dilated convolution, batch normalisation, and ReLU:

```
Conv2d(in_ch, out_ch, kernel=3, padding=dirate, dilation=dirate)
→ BatchNorm2d(out_ch)
→ ReLU(inplace=True)
```

**`RSU-n`** (Residual U-block of depth *n*) is a mini U-Net that captures multi-scale context at a single encoder stage. Five variants are implemented — RSU7, RSU6, RSU5, RSU4, and RSU4F — differing in their depth:

| Block  | Pooling levels | Dilated conv at bottom | Note |
|--------|---------------|------------------------|------|
| RSU7   | 5 × MaxPool2d | dirate=2               | Deepest; captures coarse context |
| RSU6   | 4 × MaxPool2d | dirate=2               | |
| RSU5   | 3 × MaxPool2d | dirate=2               | |
| RSU4   | 2 × MaxPool2d | dirate=2               | |
| RSU4F  | None          | dilations 2, 4, 8      | Dilation-only; used at deepest stages where spatial resolution is already low |

Each RSU block:
1. Projects the input to `out_ch` channels via a single `REBNCONV` (`rebnconvin`).
2. Passes through *n* encoder `REBNCONV` layers, each preceded by `MaxPool2d(2, stride=2, ceil_mode=True)`.
3. Applies a dilated `REBNCONV` at the bottom (or, for RSU4F, a chain of dilated convolutions at rates 2, 4, 8).
4. Reconstructs through decoder `REBNCONV` layers that take `torch.cat((upsampled, skip), dim=1)` as input, i.e. channel-wise concatenation of the upsampled deeper feature map with the encoder skip connection.
5. Adds the result to the `rebnconvin` output (residual connection): `return hx1d + hxin`.

Upsampling throughout uses `F.interpolate(..., mode='bilinear', align_corners=False)` to match the spatial size of the target feature map, implemented in `_upsample_like`.

**`U2NETP`** assembles six encoder stages and five decoder stages:

```
Encoder:
  stage1  = RSU7(3,  16, 64)   ─── pool12 (MaxPool 2×2)
  stage2  = RSU6(64, 16, 64)   ─── pool23
  stage3  = RSU5(64, 16, 64)   ─── pool34
  stage4  = RSU4(64, 16, 64)   ─── pool45
  stage5  = RSU4F(64, 16, 64)  ─── pool56
  stage6  = RSU4F(64, 16, 64)

Decoder:
  stage5d = RSU4F(128, 16, 64)   ← cat(upsample(hx6), hx5)
  stage4d = RSU4 (128, 16, 64)   ← cat(upsample(hx5d), hx4)
  stage3d = RSU5 (128, 16, 64)   ← cat(upsample(hx4d), hx3)
  stage2d = RSU6 (128, 16, 64)   ← cat(upsample(hx3d), hx2)
  stage1d = RSU7 (128, 16, 64)   ← cat(upsample(hx2d), hx1)
```

Note that all encoder stages use 64 output channels and 16 intermediate channels. All decoder stages take 128 input channels (64 skip + 64 upsampled).

**Side supervision and output fusion.** Each decoder stage, and stage6, produces a single-channel side output via `Conv2d(64, 1, 3, padding=1)`. All six side outputs are bilinearly upsampled to the spatial dimensions of `d1` (the full-resolution side output), then concatenated and fused through a 1×1 convolution `outconv = Conv2d(6, 1, 1)`. A `sigmoid` is applied to produce the final map in [0, 1].

### 3.2 Inference Pipeline (`get_saliency_map`)

```python
img resized to (320, 320)
normalised: mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)   # ImageNet stats
→ U2NETP forward pass (torch.no_grad())
→ extract channel 0 of output: pred = d1[:, 0, :, :]
→ min-max normalise: pred = (pred − pred.min()) / (pred.max() − pred.min() + 1e-8)
→ convert to uint8, resize back to original (W, H) via bilinear
→ divide by 255.0  →  S_deep ∈ [0,1]^(H×W)
```

EXIF orientation is corrected via `ImageOps.exif_transpose` before all processing to ensure the spatial saliency map aligns with the image as it would be displayed.

---

## 4. Module 2 — Semantic Object Segmentation (`object_detection.py`)

`object_detection.py` provides `get_object_segmentation_map`, which runs **YOLOv8 Nano Segmentation** (`yolov8n-seg.pt`) on the input image and produces a per-pixel union mask of all detected instances.

```python
model = YOLO("yolov8n-seg.pt")
results = model(image_path, verbose=False, device='cpu')
```

Inference is forced to CPU to avoid CUDA/torchvision version conflicts with the non-maximum suppression stage.

For each detection result, `result.masks.data` contains a tensor of shape `(num_objects, mask_h, mask_w)`. Each binary mask is extracted as a numpy array. If the mask dimensions differ from the original image dimensions, bilinear resize is applied:

```python
mask_img = Image.fromarray(mask).resize((w, h), resample=Image.BILINEAR)
mask = np.array(mask_img)
```

All per-instance masks are folded into a single combined mask via element-wise maximum:

```python
combined_mask = np.maximum(combined_mask, mask)
```

The result `S_obj ∈ [0,1]^(H×W)` is a soft union mask: a pixel takes the value of the highest-confidence instance mask covering it. Images with no detected objects return an all-zero mask, which is harmless because the fusion step in `bit_allocation.py` treats a zero object map as a no-op.

---

## 5. Module 3 — Multi-Scale Spectral Residual Saliency (`saliency_spectral.py`)

`saliency_spectral.py` implements a two-function spectral saliency pipeline based on the log-spectrum residual principle.

### 5.1 Single-Scale Spectral Residual (`_compute_spectral_residual`)

Given a 2D grayscale image array `gray_img`:

1. **DFT:** Compute the 2D Fast Fourier Transform.
   ```python
   dft = np.fft.fft2(gray_img.astype(np.float32))
   magnitude = np.abs(dft)
   phase = np.angle(dft)
   ```

2. **Log-magnitude and spectral residual:** The logarithm of the magnitude spectrum is computed. A 3×3 Gaussian blur is applied to obtain the locally smoothed log-spectrum, which represents the *expected* (average) spectral envelope of the image. The residual is the per-frequency deviation from this average:
   ```python
   log_magnitude = np.log(magnitude + 1e-8)
   smoothed = cv2.GaussianBlur(log_magnitude, (3, 3), 0)
   residual = log_magnitude - smoothed
   ```
   Frequencies where `residual` is large are statistically unusual — they correspond to image regions that contain structures not represented by the global spectral average, which empirically coincides with visually salient locations.

3. **Inverse DFT back to spatial domain:** The residual is recombined with the original phase and inverted:
   ```python
   saliency_fft = np.exp(residual) * np.exp(1j * phase)
   saliency = np.abs(np.fft.ifft2(saliency_fft))
   ```
   The magnitude of the result is the raw single-scale saliency map.

### 5.2 Multi-Scale Fusion (`detect_spectral_residual`)

The image is processed at three scales: **0.5×, 1.0×, and 1.5×** the original resolution. At each scale:

```python
scaled_gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
sal = _compute_spectral_residual(scaled_gray)
sal_resized = cv2.resize(sal, (w, h), interpolation=cv2.INTER_LINEAR)
```

A scale floor of 10 pixels in each dimension prevents meaningless DFT on trivially small arrays.

The three scale-specific maps are averaged (mean fusion):

```python
fused_saliency = np.mean(saliency_maps, axis=0)
```

Mean fusion is used here rather than maximum to suppress noise: spurious high-frequency artefacts that appear at only one scale are attenuated, while genuine salient structures that appear consistently across scales are reinforced.

**Post-processing:** A 9×9 Gaussian blur smooths the fused map (suppressing high-frequency ringing from the DFT), followed by min-max normalisation to [0,1]:

```python
fused_saliency = cv2.GaussianBlur(fused_saliency.astype(np.float32), (9, 9), 0)
fused_saliency = (fused_saliency - f_min) / (f_max - f_min + 1e-8)
```

The result `S_spec ∈ [0,1]^(H×W)` is particularly responsive to edges, fine textures, and regions with high structural complexity.

---

## 6. Module 4 — Bit Allocation (`bit_allocation.py`)

`bit_allocation.py` contains two functions: `acrd_function` and `allocate_bits`.

### 6.1 ACRD Function

The Ascending Cosine Roll-down (ACRD) function maps a normalised saliency score x ∈ [0,1] to a bit-allocation weight:

```python
def acrd_function(x):
    return 0.5 * (1 - np.cos(np.pi * x))
```

This is the normalised raised-cosine (Hann window) function shifted to the [0,1] input and [0,1] output domain:

| Input x | ACRD(x) | Interpretation |
|---------|---------|----------------|
| 0.0     | 0.0     | Pure background — zero quality budget |
| 0.25    | 0.146   | Low saliency — minimal budget |
| 0.5     | 0.5     | Mid saliency — half budget |
| 0.75    | 0.854   | High saliency — substantial budget |
| 1.0     | 1.0     | Peak saliency — full budget |

Three properties of this curve are intentional:

- **Zero derivative at both endpoints.** The gradient dACRD/dx = (π/2)·sin(πx) is zero at x=0 and x=1. This means small changes in saliency near the extremes do not cause large changes in allocated weight, avoiding perceptually abrupt quality transitions at region boundaries.
- **Monotonic.** The ordering of saliency scores is preserved: a more salient pixel always receives at least as much quality budget.
- **S-shaped.** The function is concave for x < 0.5 and convex for x > 0.5. This accelerates weight growth for moderately salient pixels compared to a linear mapping, providing a perceptual boost to mid-importance regions.

### 6.2 `allocate_bits` — Full Pipeline

`allocate_bits` executes the following five steps in order:

**Step 1 — OR-style map fusion.**

```python
combined_map = saliency_map.copy()                                      # start with S_deep

if object_map is not None:
    # resize if shapes differ (bilinear)
    combined_map = np.maximum(combined_map, object_map)                 # OR with S_obj

if spectral_map is not None:
    # resize if shapes differ (bilinear)
    spectral_boosted = np.clip(spectral_map * spectral_boost, 0.0, 1.0)
    combined_map = np.maximum(combined_map, spectral_boosted)           # OR with boosted S_spec
```

Each map is resized to match `combined_map` before fusion when shapes differ, using `Image.fromarray(...).resize(..., resample=Image.BILINEAR)`. `spectral_boost ≥ 1.0` amplifies the spectral map before the maximum operation, allowing fine edge signals to "punch through" the combined map more strongly even when the deep saliency score at that location is moderate.

**Step 2 — Hard threshold.**

```python
combined_map_thresholded = np.where(combined_map < threshold, 0.0, combined_map)
```

Pixels whose combined saliency score falls below `threshold` are clamped exactly to zero. This creates a clean background region that receives no quality budget whatsoever, rather than a very small budget that still inflates compressed file size.

**Step 3 — ACRD transfer.**

```python
bit_weights = acrd_function(combined_map_thresholded)
```

The thresholded combined map is passed element-wise through the ACRD function. Since the ACRD at zero is zero, thresholded background pixels remain zero after this step.

**Step 4 — Gamma correction.**

```python
if gamma != 1.0:
    bit_weights = np.power(np.clip(bit_weights, 0.0, 1.0), gamma)
```

A power `γ` reshapes the ACRD output curve:

- **γ > 1** (e.g., 1.6): raises the curve to a higher power, compressing all weight values toward zero. Mid-saliency regions receive disproportionately less budget, enforcing a harder foreground/background separation.
- **γ < 1** (e.g., 0.7): takes the root of the weights, expanding mid-range values upward. Mid-saliency regions receive more budget, producing a smoother quality gradient across the image.
- **γ = 1**: identity — standard ACRD curve unchanged.

**Step 5 — Floor and ceiling clipping.**

```python
bit_weights = np.clip(bit_weights, weight_floor, weight_ceiling)
```

- `weight_floor ≥ 0`: ensures that every pixel — including hard background pixels forced to zero by thresholding — still receives a minimum quality allocation. A positive floor prevents visible posterisation in gradual backgrounds.
- `weight_ceiling ≤ 1`: caps the maximum weight, preventing the most salient pixels from monopolising the entire quality budget. Lowering the ceiling distributes a baseline level of quality more broadly.

The function returns `W ∈ [weight_floor, weight_ceiling]^(H×W)`.

**Complete algorithm:**

```
Algorithm 1: ACRD-Based Bit Allocation
────────────────────────────────────────────────────────────────────
Input:  S_deep ∈ [0,1]^(H×W)
        S_obj  ∈ [0,1]^(H×W)  (optional)
        S_spec ∈ [0,1]^(H×W)  (optional)
        τ (threshold), γ (gamma), weight_floor, weight_ceiling, spectral_boost

Output: W ∈ [weight_floor, weight_ceiling]^(H×W)

1.  C ← S_deep
2.  if S_obj provided:
        resize S_obj to shape(C) if needed
        C ← element-wise max(C, S_obj)
3.  if S_spec provided:
        resize S_spec to shape(C) if needed
        C ← element-wise max(C, clip(S_spec · spectral_boost, 0, 1))
4.  C_τ ← where(C < τ, 0, C)                  // hard threshold
5.  B ← 0.5 · (1 − cos(π · C_τ))              // ACRD
6.  if γ ≠ 1.0:  B ← clip(B, 0, 1)^γ         // gamma correction
7.  W ← clip(B, weight_floor, weight_ceiling)   // floor + ceiling
8.  return W
────────────────────────────────────────────────────────────────────
```

---

## 7. Module 5 — Layered Compression (`compression.py`)

`compression.py` contains two core components: `compress_image_pytorch`, which simulates compression degradation on a single layer, and `layered_compression`, which orchestrates the two-layer blend.

### 7.1 `SimpleCompressionNet` (Architectural Definition)

The file defines a convolutional autoencoder `SimpleCompressionNet` that encodes the conceptual intent of the system — a deep image compression model that learns a latent representation and reconstructs the image. Its architecture is:

```
Encoder:
  Conv2d(3,   32, 3, stride=2, padding=1)  → ReLU   # 1/2 resolution
  Conv2d(32,  64, 3, stride=2, padding=1)  → ReLU   # 1/4 resolution
  Conv2d(64, 128, 3, stride=2, padding=1)  → ReLU   # 1/8 resolution

Decoder:
  ConvTranspose2d(128, 64, 3, stride=2, padding=1, output_padding=1)  → ReLU
  ConvTranspose2d(64,  32, 3, stride=2, padding=1, output_padding=1)  → ReLU
  ConvTranspose2d(32,   3, 3, stride=2, padding=1, output_padding=1)  → Sigmoid
```

The encoder progressively halves spatial resolution through stride-2 convolutions, building a latent tensor of shape `(128, H/8, W/8)`. The decoder exactly mirrors this through stride-2 transposed convolutions with output padding to match dimensions. The `Sigmoid` final activation constrains reconstructed pixel values to [0,1].

### 7.2 `compress_image_pytorch` — Layer Generation

This function produces a single layer of the blending pipeline by applying two calibrated signal-degradation strategies to the input image. `quality_factor ∈ [0,1]` controls overall fidelity; `is_base=True` activates the aggressive background-suppression strategies used for the base (background) layer.

**Strategy 1 — Bilinear downsampling round-trip (base layer only):**

```python
small_size = (max(16, orig_size[0] // downsample_factor),
              max(16, orig_size[1] // downsample_factor))
img = img.resize(small_size, resample=Image.BILINEAR)
img = img.resize(orig_size,  resample=Image.BILINEAR)
```

Downsampling to `1/D` of the original size via bilinear interpolation acts as an ideal low-pass filter: all spatial frequencies above the Nyquist limit `f_N = 1/(2D)` relative to the original resolution are aliased away. The subsequent upscaling back to original size restores the pixel grid but cannot recover the destroyed high-frequency information — the result is a smooth, texture-free image that is far more compressible by any codec. The minimum dimension of 16 prevents degenerate DFT or resize operations on very small images.

**Strategy 2 — Box filter blur:**

```python
blur_sigma = 1.0 * (1.0 - quality_factor)
if is_base:
    blur_sigma *= base_blur_multiplier

ksize = int(blur_sigma * 3) | 1   # nearest odd integer
if ksize > 1:
    compressed_np = cv2.boxFilter(compressed_np, -1, (ksize, ksize))
```

The box filter kernel size is `ksize = (int(blur_sigma × 3)) | 1`. The bitwise OR with 1 guarantees the kernel size is odd (required by OpenCV). For the base layer with `base_blur_multiplier = 2.5` and `quality_factor = 0.1`, `blur_sigma = 0.9 × 2.5 = 2.25`, giving `ksize = 7`. This further attenuates any edge energy that survived the downsampling round-trip, maximising spatial homogeneity in the background layer.

**Noise injection:**

```python
noise_sigma = 0.05 * (1.0 - quality_factor)
if is_base:
    noise_sigma *= 2.0
noise = np.random.normal(0, noise_sigma, orig_np.shape)
compressed_np = np.clip(orig_np + noise, 0, 1)
```

Additive Gaussian noise scaled by `(1 − quality_factor)` is injected to simulate codec quantisation artefacts. The base layer receives twice the noise to represent the higher degradation commensurate with its aggressive compression. This prevents the pre-processed image from being unrealistically clean compared to what a real codec would produce.

### 7.3 `layered_compression` — Two-Mode Blend

`layered_compression` generates the final output image by blending two layers per pixel according to the bit-weight map `W` produced by `bit_allocation.py`.

**Common preamble (both modes):**

The base layer is always generated first with `is_base=True`:

```python
base_img = compress_image_pytorch(image_path, quality_factor=base_quality, is_base=True, ...)
base_np  = np.array(base_img).astype(float) / 255.0
```

The 2D bit-weight map is broadcast to all three colour channels:

```python
weights_3d = np.stack([bit_weights] * 3, axis=-1)   # shape: (H, W, 3)
```

**Mode A — Classic lossy blend (`lossless_foreground=False`):**

An enhancement layer is generated from the same image with `is_base=False` and a high `enhancement_quality` value. This applies mild noise and blur without any downsampling, producing a higher-fidelity version of the image:

```python
enhanced_img = compress_image_pytorch(image_path, quality_factor=enhancement_quality, is_base=False, ...)
enhanced_np  = np.array(enhanced_img).astype(float) / 255.0
final_np = (1.0 - weights_3d) * base_np + weights_3d * enhanced_np
```

- Pixels where `W ≈ 0` (background, below threshold): output drawn entirely from `base_np` — aggressively degraded.
- Pixels where `W ≈ 1` (salient foreground): output drawn from `enhanced_np` — high quality but still lossy.
- Intermediate weights: smooth linear interpolation between the two layers, producing a soft transition at saliency boundaries.

**Mode B — Foreground-lossless blend (`lossless_foreground=True`):**

Instead of the enhancement layer, the exact original pixels are used as the foreground source:

```python
original_img = ImageOps.exif_transpose(Image.open(image_path)).convert('RGB')
original_np  = np.array(original_img).astype(float) / 255.0
final_np = (1.0 - weights_3d) * base_np + weights_3d * original_np
```

When `W[i,j] = 1.0`, `final_np[i,j] = original_np[i,j]` exactly — the pixel value is mathematically identical to the input. This is a **lossless preservation guarantee** for detected foreground pixels. Background pixels (W = 0) still receive the aggressively pre-processed base layer. This mode is particularly valuable for archival or identity-sensitive applications where subject degradation is unacceptable.

**Output:**

```python
final_img = Image.fromarray((final_np * 255).astype(np.uint8))
return final_img, base_img, third_img
```

The function returns the final blended image, the base layer, and the third layer (enhanced or original, depending on mode) for downstream inspection or encoding.

---

## 8. Novelty and Contributions

### 8.1 Triple-Source OR-Fusion Saliency

Each of the three detectors captures a fundamentally different signal:

| Detector | Signal type | Strengths | Weaknesses |
|----------|-------------|-----------|------------|
| U²-NetP (`saliency.py`) | Learned holistic prominence | Handles complex natural scenes; produces soft spatial maps | Blobs out fine boundaries; slow on CPU |
| YOLOv8n-seg (`object_detection.py`) | Semantic category membership | Crisp instance boundaries; class-aware | Misses objects outside 80 COCO classes; binary masks |
| Spectral Residual (`saliency_spectral.py`) | Frequency-domain statistical novelty | Category-agnostic; captures fine edges and textures | Context-free; activated by any unusual frequency, not just perceptually salient ones |

Element-wise maximum fusion (implemented in `allocate_bits`) acts as a logical OR: a pixel is protected if *any* detector considers it important, without requiring inter-modality agreement. Compared to weighted average fusion, maximum fusion ensures that a confident detection in one modality cannot be suppressed by near-zero scores in others. The `spectral_boost` parameter provides an additional lever: when set above 1.0, it amplifies the spectral map before the maximum operation, allowing fine-detail signals to override deep saliency scores at object boundaries.

### 8.2 ACRD as a Perceptual Bit-Allocation Transfer Function

The choice of `0.5·(1 − cos(πx))` as the mapping from saliency score to bit-allocation weight is deliberate and principled. A linear mapping would produce visible quality bands because equal saliency differences at all levels produce equal weight differences; but perception is non-linear — we are more sensitive to quality changes in salient regions than in background. The ACRD function's S-shape accelerates weight growth in the mid-saliency range, boosting the quality of moderately salient regions disproportionately. Its zero first derivative at both endpoints ensures there are no perceptible quality discontinuities at the transition from background to foreground.

### 8.3 Gamma-Parameterised Curve Deformation

Rather than designing multiple distinct transfer functions for different use cases, the system deforms the single ACRD curve continuously using a power function `B^γ`. This provides a smooth, interpretable single-knob control over the entire quality-compression tradeoff: γ > 1 creates a hard binary split (maximum compression in background), γ < 1 creates a soft gradient (maximum quality preservation), and γ = 1 is the canonical ACRD curve. All three behaviours share the same mathematical framework and the same code path.

### 8.4 Dual-Mode Layered Blending Pipeline

The separation of classic lossy mode and foreground-lossless mode within a single `layered_compression` function addresses qualitatively different requirements without duplicating pipeline logic. The single parameter `lossless_foreground` switches the foreground source from a high-quality compressed layer to exact original pixels. This makes a mathematically precise guarantee — zero degradation at `W=1` pixels — that is categorically distinct from merely "high quality." Both modes share the same base layer generation, the same weight broadcast, and the same blending formula; only the foreground source changes.

### 8.5 Box-Filter Base Layer as a Compressibility Pre-Processor

The base layer generation in `compress_image_pytorch` combines bilinear downsampling round-trip and box filter blurring to maximise the spatial homogeneity of the background region before any codec sees it. The downsampling round-trip acts as an ideal low-pass filter, eliminating all texture detail above the Nyquist limit of the reduced resolution. The subsequent box filter attenuates remaining edge energy. Together, they produce a smooth, low-entropy background that any downstream codec can encode at very low bit rate. The `downsample_factor` and `base_blur_multiplier` parameters allow continuous tuning of how destructive this pre-processing is.

---

## 9. Algorithmic Complexity

| Module | Primary operation | Complexity |
|--------|------------------|------------|
| `saliency.py` — U²-NetP | 6 RSU encoder stages, 5 decoder stages, fixed 320×320 input | O(H·W) convolutional, with constant factor from 320×320 inference |
| `object_detection.py` — YOLOv8n-seg | Single forward pass on original-resolution image | O(H·W) convolutional, with NMS post-processing |
| `saliency_spectral.py` | 2D FFT at 3 scales | O(3 · H · W · log(H·W)) |
| `bit_allocation.py` | Element-wise operations on H×W arrays | O(H·W) |
| `compression.py` — base layer | Bilinear resize × 2, box filter, noise | O(H·W) |
| `compression.py` — blending | Element-wise weighted sum per channel | O(H·W) |

The dominant cost is neural inference for U²-NetP and YOLOv8. Both operate as single forward passes with no iterative optimisation. U²-NetP operates at a fixed 320×320 regardless of input resolution; YOLOv8 scales with input dimensions.

---

## 10. Discussion

### 10.1 Why Three Detectors Rather Than One

A single state-of-the-art deep salient object detector would be sufficient for many natural images. However, it fails on three categories of content that are common in practice:

1. **Low-contrast subjects.** A person in camouflage or an object whose colour closely matches the background may receive low saliency scores from U²-NetP despite being the semantic subject. YOLOv8-seg detects it regardless of contrast because it uses category recognition.

2. **Objects outside the deep model's implicit training distribution.** U²-NetP was trained on natural salient object datasets; industrial objects, medical imagery, or unusual scenes may not activate it strongly. Spectral Residual is entirely training-free and will still flag statistically unusual regions.

3. **Fine detail at foreground edges.** Deep saliency maps are spatially smooth due to the multi-scale pooling structure of U²-NetP — boundaries between foreground and background are wide, blob-like gradients. Spectral Residual is sensitive to the exact edge frequency, producing high responses precisely where the object boundary is sharpest. With `spectral_boost > 1.0`, this tight edge response overrides the broad U²-NetP gradient, tightening the protected foreground region.

### 10.2 Complementarity of Downsampling and Blur in Base Layer

The two degradation strategies in `compress_image_pytorch` operate on different frequency bands and are therefore complementary. Bilinear downsampling to `1/D` removes all energy above `f_N = 1/(2D)` relative to the original resolution — this destroys fine texture (high spatial frequency). Box-filter blur of size `k` attenuates mid-frequency energy — this softens edges and gradients. The combination eliminates texture *and* reduces edge sharpness, maximising the spatial homogeneity of the background. A decoder (codec) receiving this pre-processed image encounters a smooth, largely uniform background that can be encoded with very few bits.

### 10.3 Lossless Mode and the Role of Weights at W=1

The foreground-lossless blend `final = (1−W)·base + W·original` achieves exact pixel preservation only when `W = 1.0`. The ACRD function produces `W = 1.0` only when the combined thresholded saliency is exactly 1.0. In practice, most foreground pixels have saliency scores slightly below 1.0, and the ACRD ceiling at 1.0 is only reached at peak-saliency pixels. The `weight_ceiling = 1.0` setting in lossless mode is therefore essential — it allows the ceiling to be reached, enabling true lossless blending at the most confident foreground pixels. The `spectral_boost = 1.45` amplification ensures that fine edge pixels, whose raw spectral scores may be 0.7–0.8, are elevated to combined scores close enough to 1.0 that they receive near-lossless treatment.

---

## 11. Conclusion

We described a five-module pipeline for context-aware image compression. `saliency.py` implements the full U²-NetP architecture in PyTorch, producing a deep holistic saliency map. `object_detection.py` uses YOLOv8n-seg to generate a semantic instance union mask. `saliency_spectral.py` computes multi-scale spectral residual saliency via DFT log-magnitude analysis at three scales with mean fusion. `bit_allocation.py` fuses all three maps via element-wise maximum with optional spectral boosting, applies a hard saliency threshold, converts the result through the ACRD raised-cosine transfer function, shapes the output with gamma correction, and clips to configurable floor and ceiling values. `compression.py` generates a heavily degraded base layer using bilinear downsampling round-trip and box-filter blurring, then blends it per pixel against a high-quality or exact-original foreground layer weighted by the bit-allocation map.

The result is a pre-processed image in which the background has been made spatially homogeneous and easy to compress while the foreground retains full detail. The framework requires no manual annotation, no codec modification, and no end-to-end training beyond the pre-trained U²-NetP and YOLOv8 models.

---

## References

1. Qin, X., Zhang, Z., Huang, C., Dehghan, M., Zaiane, O., and Jagersand, M. (2020). U2-Net: Going deeper with nested U-structure for salient object detection. *Pattern Recognition*, 106, 107404.
2. Jocher, G., Chaurasia, A., and Qiu, J. (2023). Ultralytics YOLOv8. https://github.com/ultralytics/ultralytics
3. Hou, X. and Zhang, L. (2007). Saliency detection: A spectral residual approach. *CVPR 2007*, 1–8.
4. He, K., Zhang, X., Ren, S., and Sun, J. (2016). Deep residual learning for image recognition. *CVPR 2016*.
5. Ballé, J., Laparra, V., and Simoncelli, E. P. (2017). End-to-end optimized image compression. *ICLR 2017*.
