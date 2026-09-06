# HUMAN WRITTEN

class MapCodec:
    def __init__(self, tile_palette: dict):
        self.tile_palette = tile_palette

    def decode(self, image: PpmImage) -> Map:
        try:
            return Map(glm.ivec2(image.width, image.height), 
                        tuple(r * self.height_scale for r, _, _ in image.pixels),
                        tuple(self.tile_palette[g] for _, g, _ in image.pixels))
        except KeyError as error:
            raise ValueError(f"Unknown tile palette index: {error.args[0]}") from error
