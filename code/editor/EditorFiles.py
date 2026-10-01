"""Read and atomically save the editor's P3 PPM at the filesystem boundary."""
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from ..codec.map.ObjectPlacementCodec import ObjectPlacementCodec
from ..codec.map.PpmImageCodec import PpmImageCodec
from .EditorState import EditorState


class EditorFiles:
    def __init__(self, map_codec, object_palette, boxes=None):
        self.map_codec = map_codec
        self.object_palette = object_palette
        self.box_templates = boxes or {}
        self.ppm_codec = PpmImageCodec()

    def load(self, filename: Path) -> EditorState:
        image = self.ppm_codec.decode(filename.read_text(encoding='ascii'))
        map_ = self.map_codec.decode(image)
        billboards, boxes = ObjectPlacementCodec(
            self.object_palette, map_, disable_validation=True,
            boxes=self.box_templates).decode_components(image)
        fixed = {key: box for key, box in self.box_templates.items()
                 if key not in self.object_palette.values()}
        return EditorState(image, map_, billboards, [(image.width // 2, image.height // 2)],
                           boxes={**boxes, **fixed})

    def save(self, filename: Path, state: EditorState) -> None:
        code = self.ppm_codec.encode(state.image)
        temporary = None
        try:
            with NamedTemporaryFile(mode='w', encoding='ascii', newline='\n',
                                    dir=filename.parent, prefix=filename.name + '.',
                                    suffix='.tmp', delete=False) as file:
                temporary = Path(file.name)
                file.write(code)
                file.flush()
                os.fsync(file.fileno())
            if filename.exists():
                temporary.chmod(filename.stat().st_mode & 0o777)
            os.replace(temporary, filename)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
