"""Load editor content and save its PPM and explicit game placements together."""
from dataclasses import replace
from math import floor, isclose
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile

from pyglm import glm

from ..codec.GameStateCodec import PluginStringCodec
from ..codec.map.ObjectPlacementCodec import ObjectPlacementCodec
from ..codec.map.PpmImageCodec import PpmImageCodec
from ..model.component.instances import BoxPlacement
from ..model.plugin.Plugin import Plugin
from .EditorState import EditorState
from .EditorContent import EditorContent


class EditorFiles:
    def __init__(self, map_codec, object_palette, box_archetypes=None, *, game_filename=None, plugin=None):
        self.map_codec = map_codec
        self.object_palette = object_palette
        self.box_archetypes = box_archetypes or {}
        self.ppm_codec = PpmImageCodec()
        self.game_codec = PluginStringCodec()
        self.game_filename = Path(game_filename) if game_filename is not None else None
        self.game_code = self.game_filename.read_text(encoding='utf-8') if self.game_filename else None
        self.plugin = plugin or (self.game_codec.decode(self.game_code) if self.game_code else Plugin())

    def load(self, filename: Path) -> EditorState:
        image = self.ppm_codec.decode(filename.read_text(encoding='ascii'))
        map_ = self.map_codec.decode(image)
        billboards, boxes = ObjectPlacementCodec(
            self.object_palette, map_, disable_validation=True,
            box_archetypes=self.box_archetypes).decode_components(image)
        characters = {key: item for key, item in self.plugin.billboards.items()
                      if key in self.plugin.characters or item.archetype in self.plugin.character_archetypes
                      or any(frame[0] == item.archetype for frame in self.plugin.animation_frames)}
        billboards.update((key, item) for key, item in self.plugin.billboards.items() if key not in characters)
        # Explicit ECS IDs take precedence over generated map IDs, as in GameFiles.
        for key in characters:
            billboards.pop(key, None)
        content = EditorContent(image, billboards, {**boxes, **self.plugin.boxes}, characters)
        return EditorState(content, map_, [(image.width // 2, image.height // 2)])

    def _pack(self, state):
        """Put movable, unnamed objects back in free PPM cells when lossless."""
        content = state.content
        pixels = list(content.image.pixels)
        mapped = ObjectPlacementCodec(self.object_palette, state.map, disable_validation=True,
                                      box_archetypes=self.box_archetypes).decode(content.image)
        tables = [dict(content.billboards), dict(content.boxes)]
        explicit = [{}, {}]
        renamed = {}
        occupied = set().union(*tables, content.character_instances)
        # Named ECS entities must retain IDs used by other component tables.
        reserved = (set(self.plugin.physics) | set(self.plugin.characters)
                    | {key[0] for key in self.plugin.inventory})
        for table, fixed in zip(tables, explicit):
            for key, item in list(table.items()):
                if key in mapped and item == mapped[key]:
                    continue
                position = item.position
                x, y = floor(position.x), floor(position.y)
                index = y * content.image.width + x
                can_pack = (key.startswith('editor-object-') and key not in reserved
                            and 0 <= x < content.image.width and 0 <= y < content.image.height
                            and isclose(position.x, x + .5, abs_tol=1e-6, rel_tol=0)
                            and isclose(position.y, y + .5, abs_tol=1e-6, rel_tol=0)
                            and isclose(position.z, state.map.height(position.xy), abs_tol=1e-6, rel_tol=0)
                            and pixels[index][2] == 0 and str((x, y)) not in occupied)
                palette_id = None
                if can_pack:
                    for number, archetype in sorted(self.object_palette.items()):
                        if (item.archetype == archetype
                                and isinstance(item, BoxPlacement) == (archetype in self.box_archetypes)):
                            palette_id = number
                            break
                if palette_id is None:
                    fixed[key] = item
                else:
                    new_key = str((x, y))
                    renamed[key] = new_key
                    occupied.add(new_key)
                    table[new_key] = replace(table.pop(key), position=glm.vec3(x + .5, y + .5, state.map.height(position.xy)))
                    pixels[index] = (*pixels[index][:2], palette_id)
        image = replace(content.image, pixels=tuple(pixels),
                        maximum=max(content.image.maximum, max(max(p) for p in pixels)))
        content = replace(content, image=image, billboards=tables[0], boxes=tables[1])
        billboards = {**explicit[0], **content.character_instances}
        boxes = explicit[1]
        return replace(state, content=content,
                       selected_objects=frozenset(renamed.get(key, key) for key in state.selected_objects)), billboards, boxes

    def _game_text(self, plugin):
        # Replace only changed placement rows. Other tables, comments, and their
        # formatting survive byte-for-byte (including spreadsheet padding).
        chunks = re.split(r'(\n\t*\n)', self.game_code)
        encoded = re.split(r'\n\t*\n', self.game_codec.encode(plugin))
        for name in ('billboards', 'boxes'):
            if getattr(plugin, name) == getattr(self.plugin, name):
                continue
            pattern = rf'^# {name}(?:\s|$)'
            rows = next(chunk for chunk in encoded if re.match(pattern, chunk))
            rows = [line for line in rows.splitlines() if line.strip() and not line.lstrip().startswith('#')]
            for i in range(0, len(chunks), 2):
                if re.match(pattern, chunks[i]):
                    comments = [line for line in chunks[i].splitlines() if line.lstrip().startswith('#')]
                    chunks[i] = '\n'.join([*comments, *rows])
                    break
            else:
                raise ValueError(f'Missing {name} placement table')
        code = ''.join(chunks)
        self.game_codec.decode(code)  # Validate both outputs before writing either.
        return code

    def save(self, filename: Path, state: EditorState) -> EditorState:
        packed, billboards, boxes = self._pack(state)
        plugin = replace(self.plugin, billboards=billboards, boxes=boxes)
        outputs = {filename: self.ppm_codec.encode(packed.content.image).encode('ascii')}
        if self.game_filename is None:
            if billboards or boxes:
                raise ValueError('Explicit placements require a .game file')
            game_code = None
        else:
            if filename.resolve() == self.game_filename.resolve():
                raise ValueError('PPM and .game paths must be different')
            if self.game_filename.read_text(encoding='utf-8') != self.game_code:
                raise ValueError('The .game file changed outside the editor; reopen it before saving')
            game_code = self._game_text(plugin)
            if game_code != self.game_code:
                outputs[self.game_filename] = game_code.encode('utf-8')
        self._write(outputs)
        self.plugin, self.game_code = plugin, game_code
        return packed

    @staticmethod
    def _write(outputs):
        # Stage all files and rollback copies before replacing either target.
        # Roll back ordinary I/O failures; two paths cannot be crash-atomic.
        pending, backups, replaced = {}, {}, []
        def stage(path, data):
            with NamedTemporaryFile(dir=path.parent, prefix=path.name + '.', suffix='.tmp', delete=False) as file:
                temporary = Path(file.name)
                try:
                    file.write(data)
                    file.flush()
                    os.fsync(file.fileno())
                    if path.exists():
                        temporary.chmod(path.stat().st_mode & 0o777)
                except BaseException:
                    temporary.unlink()
                    raise
            return temporary
        try:
            for path, data in outputs.items():
                pending[path] = stage(path, data)
                backups[path] = stage(path, path.read_bytes()) if path.exists() else None
            for path, temporary in pending.items():
                os.replace(temporary, path)
                replaced.append(path)
        except OSError:
            for path in reversed(replaced):
                if backups[path] is None:
                    path.unlink()
                else:
                    os.replace(backups[path], path)
            raise
        finally:
            for path in (*pending.values(), *backups.values()):
                if path is not None and path.exists():
                    path.unlink()
