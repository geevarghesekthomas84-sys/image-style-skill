"""ComfyUI node: upload an image (or take one from the graph) and save it as SVG or another format."""
import hashlib
import os

import numpy as np
from PIL import Image, ImageOps

from . import convert

try:
    import folder_paths  # only exists inside ComfyUI
except Exception:  # plain imports (tests) run without it
    folder_paths = None

PREVIEWABLE = ("png", "jpg", "webp", "gif")
NONE = "(none)"   # picker value meaning "use the connected images input instead"


def _input_files():
    if folder_paths is None:
        return []
    d = folder_paths.get_input_directory()
    files = [f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))]
    try:
        files = folder_paths.filter_files_content_types(files, ["image"])
    except Exception:
        pass
    return sorted(files)


def _tensor_to_pils(images):
    arr = (images.cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
    return [Image.fromarray(a[..., :3]) for a in arr]


def _save_target(prefix, w, h):
    """Folder, file stem (without extension) and subfolder for the next output file."""
    if folder_paths is not None:
        folder, name, counter, subfolder, _ = folder_paths.get_save_image_path(
            prefix, folder_paths.get_output_directory(), w, h)
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, "%s_%05d_" % (name, counter)), subfolder
    folder = os.path.join(os.getcwd(), "output")
    os.makedirs(folder, exist_ok=True)
    stem = os.path.basename(prefix) or "image-style"
    n = 1
    while any(f.startswith("%s_%05d_" % (stem, n)) for f in os.listdir(folder)):
        n += 1
    return os.path.join(folder, "%s_%05d_" % (stem, n)), ""


class ImageStyleUploadConvert(object):
    """Upload an image, then save it as PNG, JPG, WebP, BMP, TIFF, GIF or SVG."""

    CATEGORY = "image-style"
    FUNCTION = "run"
    OUTPUT_NODE = True
    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("image", "saved_path", "svg_text")
    DESCRIPTION = ("Upload an image (or connect one) and save it in another format. 'svg (trace to vector)' turns it "
                   "into flat-colour vector paths: great for logos, icons and flat art, but photos come out posterised. "
                   "'svg (embed image)' only wraps the picture in an SVG file; it is not vector artwork.")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "format": (convert.FORMATS, {"default": convert.SVG_TRACE}),
                "quality": ("INT", {"default": 90, "min": 1, "max": 100}),
                "svg_colors": ("INT", {"default": 8, "min": 2, "max": 32}),
                "max_trace_size": ("INT", {"default": 512, "min": 64, "max": 1024, "step": 32}),
                "smoothness": ("FLOAT", {"default": 1.0, "min": 0.3, "max": 4.0, "step": 0.1}),
                "filename_prefix": ("STRING", {"default": "image-style"}),
                # must be a required input: ComfyUI only adds the Upload button for a required "image" picker
                "image": (_input_files() + [NONE], {"image_upload": True}),
            },
            "optional": {
                "images": ("IMAGE",),
            },
        }

    @classmethod
    def IS_CHANGED(cls, format, quality, svg_colors, max_trace_size, smoothness, filename_prefix,
                   image=NONE, images=None):
        if images is None and image and image != NONE and folder_paths is not None:
            try:
                with open(folder_paths.get_annotated_filepath(image), "rb") as f:
                    return hashlib.sha256(f.read()).hexdigest()
            except Exception:
                return "missing"
        return ""

    @classmethod
    def VALIDATE_INPUTS(cls, image=NONE):
        if image and image != NONE and folder_paths is not None and not folder_paths.exists_annotated_filepath(image):
            return "Invalid image file: {}".format(image)
        return True

    def run(self, format, quality, svg_colors, max_trace_size, smoothness, filename_prefix,
            image=NONE, images=None):
        if images is not None:
            pils = _tensor_to_pils(images)
            out_tensor = images
        elif image and image != NONE and folder_paths is not None:
            img = Image.open(folder_paths.get_annotated_filepath(image))
            img.seek(0)
            pils = [convert.flatten(ImageOps.exif_transpose(img))]
            import torch  # ComfyUI always has torch
            out_tensor = torch.from_numpy(np.asarray(pils[0], dtype=np.float32) / 255.0)[None, ...]
        else:
            raise ValueError("Upload an image with the Upload button, or connect an IMAGE to 'images'.")

        saved, ui_images, svg_text = [], [], ""
        for pil in pils:
            stem, subfolder = _save_target(filename_prefix, pil.width, pil.height)
            path, svg = convert.save_as(pil, format, stem, quality, svg_colors, max_trace_size, smoothness)
            saved.append(path)
            if not svg_text:
                svg_text = svg
            if format in PREVIEWABLE:
                ui_images.append({"filename": os.path.basename(path), "subfolder": subfolder, "type": "output"})
        ui = {"text": ["\n".join(saved)]}
        if ui_images:
            ui["images"] = ui_images
        return {"ui": ui, "result": (out_tensor, "\n".join(saved), svg_text)}


NODE_CLASS_MAPPINGS = {"ImageStyleUploadConvert": ImageStyleUploadConvert}
NODE_DISPLAY_NAME_MAPPINGS = {"ImageStyleUploadConvert": "Image Style Upload & Convert (SVG, PNG, JPG...)"}
