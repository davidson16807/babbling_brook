
class DeckGeneration:
    def __init__(self, omit_codes = ['—','❕','❔']):
        self.omit_codes = omit_codes
    def generate(self, 
            demonstrations,
            traversal, 
            tag_templates={},
        ):
        for tuplekey in traversal:
            tags = traversal.indexing.dictkey(tuplekey)
            card = ' '.join([
                str(demonstration(tags, tag_templates)) 
                for demonstration in demonstrations])
            if all([symbol not in card for symbol in self.omit_codes]):
                # if '{{' not in card:
                #     breakpoint()
                yield card


class CardFormatting:
    def __init__(self):
        pass
    def emoji_focus(self, content):
        fonts = ''' sans-serif, Twemoji, "Twemoji Mozilla", "Segoe UI Emoji", "Noto Color Emoji" '''
        return f'''<div style='font-size:3em; padding: 1em 0em; display:inline-box; font-family: {fonts}'>{content}</div>'''
    def foreign_focus(self, content):
        return f'''<div style='font-size:3em'>{content}</div>'''
    def foreign_side_note(self, content):
        return f'''<div style='font-size:2em'>{content}</div>'''
    def native_word(self, content):
        return f'''<div>{content}</div>'''

