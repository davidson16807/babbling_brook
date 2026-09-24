# HUMAN VETTED

from dataclasses import dataclass

@dataclass(frozen=True)
class PpmImage:
    width: int
    height: int
    maximum: int
    pixels: tuple[tuple[int, int, int], ...]


class PpmImageCodec:
    def encode(self, image: PpmImage) -> str:
        if image.width <= 0 or image.height <= 0 or not 1 <= image.maximum <= 65535:
            raise ValueError("Invalid PPM dimensions or maximum")
        if len(image.pixels) != image.width * image.height:
            raise ValueError("PPM sample count does not match dimensions")
        if any(len(pixel) != 3 or any(
            not isinstance(value, int) or not 0 <= value <= image.maximum for value in pixel
        ) for pixel in image.pixels):
            raise ValueError("PPM sample outside declared range")
        # One pixel per line also keeps 16-bit samples within P3's line-length recommendation.
        pixels = '\n'.join(' '.join(map(str, pixel)) for pixel in image.pixels)
        return f'P3\n{image.width} {image.height}\n{image.maximum}\n{pixels}\n'

    def decode(self, code: str) -> PpmImage:
        tokens = "\n".join(line.split("#", 1)[0] for line in code.splitlines()).split()
        if len(tokens) < 4 or tokens[0] != "P3":
            raise ValueError("Maps must use text P3 PPM")
        width, height, maximum = map(int, tokens[1:4])
        if width <= 0 or height <= 0 or not 1 <= maximum <= 65535:
            raise ValueError("Invalid PPM dimensions or maximum")
        if len(tokens) - 4 != width * height * 3:
            raise ValueError("PPM sample count does not match dimensions")
        values = tuple(map(int, tokens[4:]))
        if any(v < 0 or v > maximum for v in values):
            raise ValueError("PPM sample outside declared range")
        return PpmImage(width, height, maximum, tuple(zip(values[::3], values[1::3], values[2::3])))
