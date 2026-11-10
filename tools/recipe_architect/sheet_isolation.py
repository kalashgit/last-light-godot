"""Conservative connected-component separation of original founder sheet cells.

Object silhouettes sometimes cross nominal grid boundaries. Work on the whole
verified sheet, then assign each foreground component to the *nearest indexed
cell by its bounding-box center*. Never infer asset identity or geometry here.
Small disconnected captions are excluded from private VLM input. Uncertain
multi-part components are preserved for review but are not auto-admitted.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np
from PIL import Image
from scipy import ndimage


FOREGROUND_THRESHOLD = 225
MIN_OBJECT_PIXELS = 500
SECONDARY_OBJECT_FRACTION = .10
PAD_PIXELS = 6


class SheetIsolator:
    def __init__(self, sheet: Image.Image, *, rows: int, columns: int):
        if not 1 <= rows <= 20 or not 1 <= columns <= 20:
            raise ValueError("unsupported sheet grid")
        self.original = sheet.convert("RGB")
        self.width, self.height = self.original.size
        self.rows, self.columns = rows, columns
        pixels = np.asarray(self.original)
        foreground = np.min(pixels, axis=2) < FOREGROUND_THRESHOLD
        self.labels, _ = ndimage.label(foreground, structure=np.ones((3, 3), dtype=np.uint8))
        self.regions = defaultdict(list)
        for component, slices in enumerate(ndimage.find_objects(self.labels), start=1):
            if slices is None:
                continue
            area = int(np.count_nonzero(self.labels[slices] == component))
            if area < 75:
                continue
            y0, y1 = slices[0].start, slices[0].stop
            x0, x1 = slices[1].start, slices[1].stop
            row = min(rows - 1, int(((y0 + y1) / 2) * rows / self.height))
            col = min(columns - 1, int(((x0 + x1) / 2) * columns / self.width))
            self.regions[(row, col)].append((area, component, (x0, y0, x1, y1)))
        for items in self.regions.values():
            items.sort(reverse=True)

    def isolate(self, row: int, col: int) -> tuple[Image.Image, dict]:
        if not 0 <= row < self.rows or not 0 <= col < self.columns:
            raise ValueError("cell outside verified sheet")
        candidates = self.regions.get((row, col), [])
        if not candidates or candidates[0][0] < MIN_OBJECT_PIXELS:
            raise ValueError("no sufficiently distinct physical silhouette in indexed cell")
        area, primary, box = candidates[0]
        secondary = [item for item in candidates[1:]
                     if item[0] >= area * SECONDARY_OBJECT_FRACTION]
        included = [candidates[0], *secondary]
        x0 = max(0, min(item[2][0] for item in included) - PAD_PIXELS)
        y0 = max(0, min(item[2][1] for item in included) - PAD_PIXELS)
        x1 = min(self.width, max(item[2][2] for item in included) + PAD_PIXELS)
        y1 = min(self.height, max(item[2][3] for item in included) + PAD_PIXELS)
        subset = self.labels[y0:y1, x0:x1]
        mask = np.isin(subset, [item[1] for item in included])
        # Preserve the light interior of an outlined original object, together
        # with antialiased silhouette edges. Do not copy other nearby objects.
        mask = ndimage.binary_dilation(ndimage.binary_fill_holes(mask), iterations=2)
        original = np.asarray(self.original)[y0:y1, x0:x1]
        isolated = np.full_like(original, 255)
        isolated[mask] = original[mask]
        sheet_border_touch = (box[0] <= 1 or box[1] <= 1 or
                              box[2] >= self.width - 1 or box[3] >= self.height - 1)
        width_ratio = (box[2] - box[0]) * self.columns / self.width
        height_ratio = (box[3] - box[1]) * self.rows / self.height
        oversized = width_ratio > 1.6 or height_ratio > 1.6
        safe = not (secondary or sheet_border_touch or oversized)
        return Image.fromarray(isolated, "RGB"), {
            "method": "whole_sheet_connected_component_v1",
            "primary_component_id": primary,
            "primary_foreground_pixels": area,
            "primary_bbox_xyxy": list(box),
            "isolated_bbox_xyxy": [x0, y0, x1, y1],
            "secondary_large_components": len(secondary),
            "main_component_width_cells": round(width_ratio, 3),
            "main_component_height_cells": round(height_ratio, 3),
            "source_sheet_outer_border_touch": sheet_border_touch,
            "possible_merged_or_oversized_object": oversized,
            "safe_for_unattended_proposal": safe,
            "not_a_semantic_segmentation_or_geometry_approval": True,
        }
