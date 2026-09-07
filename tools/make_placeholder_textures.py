"""Rebuild the small geometric MVP placeholders (optional authoring dependency: Pillow)."""
from pathlib import Path
from PIL import Image, ImageDraw

output = Path(__file__).resolve().parents[1] / 'data' / 'textures'
output.mkdir(parents=True, exist_ok=True)
for name, base, detail in [('grass', '#729852', '#86a761'), ('path', '#bcaa79', '#c8b88b'), ('stone', '#a1a497', '#b8b8a7')]:
    image = Image.new('RGBA', (32, 32), base)
    draw = ImageDraw.Draw(image)
    draw.line([(0, 31), (31, 31), (31, 0)], fill=detail)
    for x, y in [(5, 8), (21, 5), (13, 23), (27, 17)]:
        draw.line((x, y, x+2, y), fill=detail)
    if name == 'stone':
        draw.line((0, 16, 32, 16), fill='#848c85')
        draw.line((16, 0, 16, 16), fill='#848c85')
        draw.line((8, 16, 8, 32), fill='#848c85')
    image.save(output / f'{name}.png')
for name in ('tree', 'apple', 'crate', 'stick'):
    image = Image.new('RGBA', (32, 48), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    if name == 'tree':
        draw.rectangle((13, 20, 18, 47), fill='#715640')
        draw.ellipse((1, 6, 30, 33), fill='#365c40')
        draw.ellipse((4, 0, 27, 25), fill='#59814b')
        draw.ellipse((8, 2, 23, 16), fill='#719a57')
        for x, y in ((7, 20), (24, 15), (16, 7)):
            draw.ellipse((x-1, y-1, x+2, y+3), fill='#ce7752')
    elif name == 'apple':
        draw.ellipse((2, 10, 29, 47), fill='#9b3f37')
        draw.ellipse((4, 10, 26, 42), fill='#d96b4e')
        draw.rectangle((14, 3, 16, 13), fill='#604732')
        draw.ellipse((17, 2, 26, 9), fill='#648f46')
        draw.ellipse((8, 15, 12, 21), fill='#edaa70')
    elif name == 'crate':
        draw.rectangle((1, 3, 30, 47), fill='#795a3b', outline='#4d402d', width=2)
        draw.rectangle((5, 7, 26, 43), fill='#ab8153')
        draw.line((5, 7, 26, 43), fill='#d2a974', width=4)
        draw.line((26, 7, 5, 43), fill='#d2a974', width=4)
    else:
        draw.line((4, 43, 27, 6), fill='#66513b', width=5)
        draw.line((5, 43, 28, 6), fill='#a48659', width=2)
        draw.line((17, 24, 10, 8), fill='#806346', width=3)
    image.save(output / f'{name}.png')
for name, shirt in [('child', '#719baa'), ('villager', '#ab806b')]:
    for direction in ('front', 'back'):
        for frame in (0, 1):
            image = Image.new('RGBA', (32, 48), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            bob = frame
            draw.rectangle((9, 35, 13, 45), fill='#404e50')
            draw.rectangle((19, 35, 23, 45), fill='#404e50')
            draw.rectangle((7, 44, 13, 47), fill='#574739')
            draw.rectangle((19, 44, 25, 47), fill='#574739')
            draw.rectangle((8, 20+bob, 24, 36+bob), fill=shirt)
            draw.rectangle((4, 23+bob, 8, 34+bob), fill='#e1ba8b')
            draw.rectangle((24, 23+bob, 28, 34+bob), fill='#e1ba8b')
            draw.rectangle((9, 5+bob, 23, 20+bob), fill='#e1ba8b')
            draw.rectangle((7, 3+bob, 24, 10+bob), fill='#654b37')
            if direction == 'front':
                draw.rectangle((10, 12+bob, 11, 14+bob), fill='#344247')
                draw.rectangle((19, 12+bob, 20, 14+bob), fill='#344247')
            else:
                draw.rectangle((8, 8+bob, 24, 18+bob), fill='#654b37')
            image.save(output / f'{name}-{direction}-{frame}.png')
