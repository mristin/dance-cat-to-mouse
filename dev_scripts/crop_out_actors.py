"""Crop out cat and mouse sprites from a sprite sheet."""

import argparse
import os
import pathlib
import sys

import PIL
import PIL.Image


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.parse_args()

    this_path = pathlib.Path(os.path.realpath(__file__))
    this_dir = this_path.parent
    images_dir = this_dir.parent / "dancecattomouse/media/images"

    # noinspection SpellCheckingInspection
    sheet_path = this_dir / "lpccatratdog.png"

    image = PIL.Image.open(str(sheet_path))
    png_info = dict()
    if image.mode not in ['RGB', 'RGBA']:
        image = image.convert('RGBA')
        png_info = image.info

    image_w, image_h = image.size
    sprite_w = int(image_w / 9)
    sprite_h = int(image_h / 8)

    names_positions = [
        ("mouse_south0", (0, 0)),
        ("mouse_south1", (0, 1)),
        ("mouse_south2", (0, 2)),

        ("mouse_west0", (1, 0)),
        ("mouse_west1", (1, 1)),
        ("mouse_west2", (1, 2)),

        ("mouse_east0", (2, 0)),
        ("mouse_east1", (2, 1)),
        ("mouse_east2", (2, 2)),

        ("mouse_north0", (3, 0)),
        ("mouse_north1", (3, 1)),
        ("mouse_north2", (3, 2)),

        ("dog_south0", (4, 0)),
        ("dog_south1", (4, 1)),
        ("dog_south2", (4, 2)),

        ("dog_west0", (5, 0)),
        ("dog_west1", (5, 1)),
        ("dog_west2", (5, 2)),

        ("dog_east0", (6, 0)),
        ("dog_east1", (6, 1)),
        ("dog_east2", (6, 2)),

        ("dog_north0", (7, 0)),
        ("dog_north1", (7, 1)),
        ("dog_north2", (7, 2)),

        ("cat_south0", (0, 3)),
        ("cat_south1", (0, 4)),
        ("cat_south2", (0, 5)),

        ("cat_west0", (1, 3)),
        ("cat_west1", (1, 4)),
        ("cat_west2", (1, 5)),

        ("cat_east0", (2, 3)),
        ("cat_east1", (2, 4)),
        ("cat_east2", (2, 5)),

        ("cat_north0", (3, 3)),
        ("cat_north1", (3, 4)),
        ("cat_north2", (3, 5)),
    ]

    for name, (row, column) in names_positions:
        xmin = column * sprite_w
        xmax = column * sprite_w + sprite_w

        ymin = row * sprite_h
        ymax = row * sprite_h + sprite_h

        cropped = image.crop((xmin, ymin, xmax, ymax))
        cropped.save(str(images_dir / f"{name}.png"), **png_info)

    return 0


if __name__ == "__main__":
    sys.exit(main())
