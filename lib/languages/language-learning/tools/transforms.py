
class HtmlTextTransform:
    def __init__(self):
        pass
    def mirror(self, emoji):
        return f'''<span style='display:inline-flex; transform: scale(-1,1)'>{emoji}</span>'''
    def flip(self, emoji):
        return f'''<span style='display:inline-flex; transform: scale(1,-1)'>{emoji}</span>'''
    def scale(self, emoji, x,y):
        return f'''<span style='display:inline-flex; transform: scale({x},{y})'>{emoji}</span>'''
    def fontsize(self, emoji, size):
        return f'''<span style='display:inline-flex; font-size:{size}em'>{emoji}</span>'''

class HtmlGroupPositioning:
    def __init__(self):
        pass
    def offset(self, emoji, x, y, size=1):
        return f'''<span style='font-size:{size*100}%; transform:translate({-x/2}em,{-y}em);'>{emoji}</span>'''
    def group(self, emoji, max_width):
        return f'''<span style='max-width:{max_width}em; display:inline-flex; justify-content:center; align-items:center; white-space:nowrap;'>{emoji}</span>'''
    def flex(self, emoji):
        return f'''<span style='display:inline-flex;'>{emoji}</span>'''

class HtmlPersonPositioning:
    def __init__(self, htmlGroupPositioning):
        self.positions = htmlGroupPositioning
        self.offset = 0.1
    def farleft(self, person):
        return self.positions.offset(person,-1,-self.offset)
    def left(self, person):
        return self.positions.offset(person,-1,-self.offset)
    def center(self, person):
        return person
    def right(self, person):
        return self.positions.offset(person, 1,-self.offset)
    def group(self, *people):
        return self.positions.group(''.join(people), 1+self.offset*(len(people)-1))

class HtmlNumberTransform:
    def __init__(self, htmlPersonPositioning):
        self.positions = htmlPersonPositioning
    def singular(self, a): 
        return a
    def dual(self, a,b): 
        return self.positions.group(self.positions.left(a), self.positions.center(b))
    def plural(self, a,b,c): 
        return self.positions.group(self.positions.left(a), self.positions.center(b), self.positions.right(c))
    def dual_inclusive(self, a,b): 
        return self.positions.group(self.positions.farleft(a), self.positions.center(b))
    def plural_inclusive(self, a,b,c): 
        return self.positions.group(self.positions.farleft(a), self.positions.center(b), self.positions.right(c))

class HtmlTenseTransform:
    def __init__(self):
        pass
    def present(self, scene): 
        return f'''{scene}'''
    def past(self, scene): 
        # old timey sepia filter
        return f'''<span style='filter: sepia(0.8)  drop-shadow(0px 0px 5px black)'>{scene}</span>'''
    def future(self, scene): 
        # blurry filter because we can't see the future
        return f'''<span style='filter: blur(1px) drop-shadow(0px 0px 5px black)'>{scene}</span>'''

class HtmlNounFormTransform:
    def __init__(self, htmlGroupPositioning):
        self.positions = htmlGroupPositioning
    def interrogative(self, scene): 
        # "who's that pokemon!?"
        return (f'''<span style="filter: drop-shadow(0 0 0.3em #7777FF)"><span style="filter:brightness(0)">{scene}</span></span>''' 
            + self.positions.offset('?',1,1,0.7))
    def demonstrative(self, scene): 
        return scene + self.positions.offset('← ',1,1,0.7)

class HtmlProgressTransform:
    def __init__(self):
        pass
    def atomic(self, scene): 
        return f'''{scene}'''
    def atelic(self, scene): 
        return f'''{scene}'''
    def started(self, scene): 
        return f'''{scene}<progress style='width:1em; height:0.7em; position:relative; top:0.5em; right:0.3em;' max='10' value='7'></progress>'''
    def unfinished(self, scene): 
        return f'''{scene}<progress style='width:1em; height:0.7em; position:relative; top:0.5em; right:0.3em;' max='10' value='7'></progress>'''
    def finished(self, scene): 
        return f'''{scene}<progress style='width:1em; height:0.7em; position:relative; top:0.5em; right:0.3em;' max='10' value='10'></progress>'''
    # def perfect_progressive(self, scene): 
    #     return f'''<span style='filter: sepia(0.3) drop-shadow(0px 0px 2px black)'>{scene}<progress style='width:1em; height:0.7em; position:relative; top:0.5em; right:0.3em;' max='10' value='10'></progress></span>'''

class HtmlBubble:
    def __init__(self):
        pass
    def affirmative(self, scene): 
        return f'''<div style='margin-bottom: 1em;'><span style='border-radius: 0.5em; padding: 1em; background:#ccc !important; z-index:-2;'>{scene}</span></div>'''
    def negative(self, scene): 
        return f'''<div style='margin-bottom: 1em;'><span style='border-radius: 0.5em; padding: 1em; background: linear-gradient(to left top, #ccc 47%, red 48%, red 52%, #ccc 53%) !important; border-style: solid; border-color:red; border-width:6px; z-index:-2;'>{scene}</span></div>'''
    def box(self, scene):
        return f"<span style='border-radius: 0.5em; padding: 0.4em; border-style: solid; border-color:grey; border-width:3px;'>{scene}</span>"
    def negative_box(self, scene):
        return f"<span style='border-radius: 0.5em; padding: 0.4em; background: linear-gradient(to left top, transparent 47%, red 48%, red 52%, transparent 53%); border-style: solid; border-color:red; border-width:6px;'>{scene}</span>"
