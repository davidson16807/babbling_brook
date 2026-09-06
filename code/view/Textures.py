# HUMAN VETTED

class Textures:
    def __init__(self, gl, files):
        self.gl, self.files, self.cache = gl, files, {}

    def get(self, name):
        if name not in self.cache:
            image = self.files.read(name)
            texture = self.gl.texture(image.size, 4, image.rgba)
            texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
            texture.repeat_x = texture.repeat_y = False
            self.cache[name] = texture
        return self.cache[name]

    def release(self):
        for texture in self.cache.values():
            texture.release()
        self.cache.clear()
