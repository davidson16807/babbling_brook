import math
import itertools

class DictKeyIndexing:
    '''
    `DictKeyIndexing` represents a method for using dictionaries as hashable objects.
    It does so by converting between two domains, known as 'dictkeys' and 'tuplekeys'.
    A 'dictkey' is a dictionary that maps each key to either a value or a set of values.
    A 'dictkey' is indexed by one or more 'tuplekeys', which are ordinary tuples of values
     that can be indexed natively in Python dictionaries.
    `DictKeyIndexing` works by selecting a single key:value pair 
     within a dictkey to serve as the tuplekey(s) to index by.
    It offers several conveniences to allow 
     working with both dictkeys and the values they are indexed by
    '''
    def __init__(self, key):
        self.key = key
    def __str__(self):
        return ''.join([f'DictKeyIndexing(', self.key, ')'])
    def __repr__(self):
        return ''.join([f'DictKeyIndexing(', self.key, ')'])
    def __iter__(self):
        return [self.key].__iter__()
    def dictkey(self, tuplekey):
        return {self.key:tuplekey}
    def check(self, dictkey):
        key = self.key
        if key not in dictkey:
            raise KeyError(' '.join(['Dictionary is missing required key:', key]))
        if type(dictkey[key]) != str:
            raise KeyError(' '.join(['Dictionary maps keys to invalid type:', key]))
    def tuplekey(self, containerkey):
        '''
        Returns a value that represents the `containerkey` according to the indexing,
        where `containerkey` is either a value, or a dict that maps a key from `keys` to a single value.
        '''
        if type(containerkey) == dict:
            return containerkey[self.key]
        else:
            return containerkey
    def tuplekeys(self, dictkey):
        '''
        Returns a generator that iterates through possible values for the given `key`
        given values from a `dictkey` dict that maps a key to either a value or a set of possible values.
        '''
        key = self.key
        if type(dictkey) in {dict}:
            return ([] if key not in dictkey 
                    else dictkey[key] if type(dictkey[key]) in {set,list} 
                    else [dictkey[key]])
        elif type(dictkey) in {set,list}:
            return dictkey
        else:
            return [dictkey]
    def count(self, dictkey):
        key = self.key
        if type(dictkey) in {dict}:
            return (0 if key not in dictkey 
                    else len(dictkey[key]) if type(dictkey[key]) in {set,list} 
                    else 1)
        elif type(dictkey) in {set,list}:
            return len(dictkey)
        else:
            return 1

class DictTupleIndexing:
    '''
    `DictTupleIndexing` represents a method for using dictionaries as hashable objects.
    It does so by converting between two domains, known as 'dictkeys' and 'tuplekeys'.
    A 'dictkey' is a dictionary that maps each key to either a value or a set of values.
    A 'dictkey' is indexed by one or more 'tuplekeys', which are ordinary tuples of values
     that can be indexed natively in Python dictionaries.
    `DictKeyIndexing` works by ordering values in a dictkey 
     into one or more tuplekeys according to a given list of `keys`.
    '''
    def __init__(self, keys, defaults=None):
        self.keys = keys
        self.defaults = {} if defaults is None else defaults
    def __str__(self):
        return ''.join([f'DictTupleIndexing(', ', '.join(self.keys), ')'])
    def __repr__(self):
        return ''.join([f'DictTupleIndexing(', ', '.join(self.keys), ')'])
    def dictkey(self, tuplekey):
        return {
            **self.defaults, 
            **{key:tuplekey[i] for i, key in enumerate(self.keys)}
        }
    def tuplekey(self, containerkey):
        '''
        Returns a tuple that represents the `containerkey` according to the indexing,
        where `containerkey` is either a tuple, or a dict that maps a key from `keys` to a single value.
        '''
        if type(containerkey) == tuple:
            return containerkey
        elif type(containerkey) == dict:
            return tuple([containerkey[key] for key in self.keys])
        else:
            raise ValueError(f'Invalid key of type "{type(containerkey)}"')
    def tuplekeys(self, dictkey):
        '''
        Returns a generator that iterates through 
        possible tuples whose keys are given by `keys`
        and whose values are given by a `dictkey` dict 
        that maps a key from `keys` to either a value or a set of possible values.
        '''
        dictkey = {**self.defaults, **dictkey}
        return [tuple(reversed(tuplekey)) 
                for tuplekey in itertools.product(
                    *[[] if key not in dictkey
                      else dictkey[key] if type(dictkey[key]) in {set,list} 
                      else [dictkey[key]]
                      for key in reversed(self.keys)])]
    def check(self, dictkey):
        dictkey = {**self.defaults, **dictkey}
        missing = [key
                for key in self.keys
                if key not in dictkey
            ]
        if missing:
            raise KeyError(' '.join(['Dictionary is missing required keys:', *missing]))
        invalid = [key
                for key in self.keys
                if type(dictkey[key]) != str
            ]
        if invalid:
            raise KeyError(' '.join(['Dictionary maps keys to invalid type:', *invalid]))
    def count(self, dictkey):
        '''
        Returns the number of possible tuples that can be generated from `self.tuplekeys(dictkey)`.
        '''
        dictkey = {**self.defaults, **dictkey}
        return math.prod([
                    0 if key not in dictkey
                    else len(dictkey[key]) if type(dictkey[key]) in {set,list}
                    else 1
                    for key in self.keys])
    def __iter__(self):
        return self.keys.__iter__()
    def __nonzero__(self):
        return len(self.keys) > 0
    def __bool__(self):
        return len(self.keys) > 0
    def __and__(self, other):
        '''
        Returns a new `DictKeyIndexing` that contains the intersection of keys from both `self` and `other`
        '''
        other_set = set(other)
        return DictTupleIndexing([key 
            for key in self
            if key in other_set])
    def __or__(self, other):
        '''
        Returns a new `DictKeyIndexing` that contains the union of keys from both `self` and `other`
        '''
        self_set = set(self)
        return DictTupleIndexing([
                *self,
                *[key 
                  for key in other
                  if key not in self_set],
            ])
    def __xor__(self, other):
        '''
        Returns a new `DictKeyIndexing` that contains the keys that are from `self` and `other` but not both
        '''
        other_set = set(other)
        self_set = set(self)
        return DictTupleIndexing([
                *[key 
                  for key in self
                  if key not in other_set],
                *[key 
                  for key in other
                  if key not in self_set],
            ])
    def __sub__(self, other):
        '''
        Returns a new `DictKeyIndexing` that contains the negation of keys from `self` and `other`
        '''
        other_set = set(other)
        return DictTupleIndexing([key 
            for key in self.keys
            if key not in other_set])

