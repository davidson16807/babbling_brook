

class ObjectPlacementCodec:
    def __init__(self, object_palette: dict, map: Map):
        self.object_palette = object_palette
        self.map = map

    def decode(self, image: PpmImage) -> list[ObjectPlacement]:
        def object_placement(i, object_):
            x,y = i % image.width, i // image.width
            return ObjectPlacement((x,y), object_,
                    glm.vec3(x,y, self.map.height(glm.ivec2(position(i))))
                )
        try:
            return [
                object_placement(i, self.object_palette[b])
                for i, (r, _, b) in enumerate(image.pixels)
                if b == 0 
            ]
        except KeyError as error:
            raise ValueError(f"Unknown object palette index: {error.args[0]}") from error
