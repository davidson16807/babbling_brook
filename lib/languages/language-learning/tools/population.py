import copy

class FlatLookupPopulation:
    '''
    `FlatLookupIndexing` converts a list of annotations
    (such as those output by `*Annotations`)
    to a representation where cells are stored in a lookup.
    The cells are indexed by their annotations according to the indexing behavior 
    within a given `template_lookup`.
    '''
    def __init__(self, template_lookup, evaluation, debug=False):
        self.template_lookup = template_lookup
        self.evaluation = evaluation
        self.debug = debug
    def index(self, annotations):
        if self.debug: breakpoint()
        lookup = copy.deepcopy(self.template_lookup)
        for annotation in annotations:
            lookup[annotation] = self.evaluation(annotation)
        return lookup

class NestedLookupPopulation:
    '''
    `NestedLookupPopulation` converts a list of annotations
    (such as those output by `*Annotations`)
    to a representation where cells are stored in nested lookups.
    The cells are indexed by their annotations according to 
    the indexing behavior within a given `template_lookups`.
    Nested lookups can be especially useful if the data 
    that they are indexing is nonnormalized, 
    since inner nested lookups can each use separate indexing methods,
    so that their content is a strict function of the key and nothing else.
    '''
    def __init__(self, template_lookups, evaluation, debug=False):
        self.template_lookups = template_lookups
        self.evaluation = evaluation
        self.debug = debug
    def index(self, annotations):
        if self.debug: breakpoint()
        lookups = copy.deepcopy(self.template_lookups)
        for annotation in annotations:
            for tuplekey in lookups.indexing.tuplekeys(annotation):
                lookup = lookups[tuplekey]
                lookup[annotation] = self.evaluation(annotation)
            if self.debug: breakpoint()
        return lookups

class ListLookupPopulation:
    '''
    `FlatLookupIndexing` converts a list of annotations
    (such as those output by `*Annotations`)
    to a representation where cells are stored in a lookup.
    The cells are indexed by their annotations according to the indexing behavior 
    within a given `template_lookup`.
    '''
    def __init__(self, template_lookup, evaluation, debug=False):
        self.template_lookup = template_lookup
        self.evaluation = evaluation
        self.debug = debug
    def index(self, annotations):
        if self.debug: breakpoint()
        lookup = copy.deepcopy(self.template_lookup)
        for annotation in annotations:
            for tuplekey in lookup.indexing.tuplekeys(annotation):
                lookup[tuplekey].append(self.evaluation(annotation))
        return lookup

class DictSetPopulation:
    '''
    `DictSetPopulation` converts a list of annotations
    (such as those output by `*Annotations`)
    to a representation where cells are stored in a set.
    The cells are indexed by their annotations according to the indexing behavior 
    within a given `template_set`.
    '''
    def __init__(self, template_set, debug=False):
        self.template_set = template_set
        self.debug = debug
    def index(self, annotations):
        if self.debug: breakpoint()
        dictset = copy.deepcopy(self.template_set)
        for annotation in annotations:
            for tuplekey in dictset.indexing.tuplekeys(annotation):
                dictset.content.add(tuplekey)
        return dictset
