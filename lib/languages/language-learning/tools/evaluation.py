
class IdentityEvaluation:
    def __init__(self):
        pass
    def __call__(self, annotation):
        return annotation

class KeyEvaluation:
    def __init__(self, key):
        self.key = key
    def __call__(self, annotation):
        return annotation[self.key]

class MultiKeyEvaluation:
    def __init__(self, keys):
        self.keys = keys
    def __call__(self, annotation):
        return {key:annotation[key] for key in self.keys}
