import math
import itertools
from collections import OrderedDict

from .indexing import DictTupleIndexing

class DictList:
    '''
    `DictList` is a data structure that stores a sequence of 'dictkeys'. 
    It allows ordered traversal but forbids tests for membership to prevent unintended performance issues.
    It matches the format of other Dict* stores in having a given `indexing` method,
    where `indexing` is of a class that shares the same iterface as `DictIndexing`.
    It can be considered a set of points within a `DictSpace`.
    A 'dictkey' is a dictionary that maps each key to either a value or a set of values.
    A 'dictkey' is indexed by one or more 'tuplekeys', which are ordinary tuples of values.
    '''
    def __init__(self, name, indexing, sequence):
        self.name = name
        self.indexing = indexing
        self.sequence = [indexing.tuplekey(entry) for entry in sequence]
        misaligned = [len(tuplekey) 
            for tuplekey in self.sequence
            if len(tuplekey) != len(indexing.keys)]
        if misaligned:
            raise ValueError(
                f'DictList indexing is misaligned with keys: expected {len(indexing.keys)}, got '+
                ', '.join(misaligned))
    def __str__(self):
        cell_width = 13
        return '\n'.join([
                f'DictList {self.name} [{len(self)} rows]:', 
                ' '.join([element.rjust(cell_width) for element in self.indexing]),
                *[' '.join([element.rjust(cell_width) for element in tuplekey]) for tuplekey in self.sequence],
            ])
    def __repr__(self):
        cell_width = 13
        return '\n'.join([
                f'DictList {self.name} [{len(self)} rows]:', 
                ' '.join([element.rjust(cell_width) for element in self.indexing]),
                *[' '.join([element.rjust(cell_width) for element in tuplekey]) for tuplekey in self.sequence],
            ])
    def __contains__(self, key):
        raise NotImplementedError('Cannot allow performant check for membership')
    def __iter__(self):
        return self.sequence.__iter__()
    def __len__(self):
        return len(self.sequence)
    def empty(self):
        return len(self.sequence) < 1
    def fallback(self, other):
        assert type(other) == DictSpace
        return self*DictSpace('fallback',
                        other.indexing - self.indexing,
                        other.key_to_values)
    def __add__(self, other):
        '''
        Return a `DictList` that contains the contents of `self` followed by `other`.
        Preserve the order of keys from `self`. Only add keys from `other` if they are unique
        '''
        name = f'({self.name}) + ({other.name})'
        indexing = self.indexing
        nonequivalent = self.indexing ^ other.indexing
        assert set(self.indexing) == set(other.indexing), '\n'.join([
            f'Indexes of "{self.name}" and "{other.name}" are not equivalent.',
            f'Addition is only supported for equivalent indexes.',
            f'The nonequivalent keys are: {nonequivalent}'])
        result = DictList(
            name, indexing,
            sequence = [
                *self,
                *[indexing.tuplekey(other.indexing.dictkey(tuplekey))
                  for tuplekey in other]
            ])
        return result
    def __mul__(self, other):
        '''
        Return the cartesian product of two `DictList`s.
        Preserve the order of keys from `self`. Only add keys from `other` if they are unique
        '''
        name = f'({self.name}) * ({other.name})'
        indexing = self.indexing | other.indexing
        overlap = self.indexing & other.indexing
        assert not bool(overlap), '\n'.join([
            f'Indexes of "{self.name}" and "{other.name}" are not disjoint.',
            f'Multiplication is only supported for disjoint indexes. ',
            f'The overlapping keys are: {overlap}'])
        result = DictList(
            name, indexing,
            sequence = [
                indexing.tuplekey({**dictkey1, **dictkey2})
                for (dictkey1, dictkey2) in itertools.product(
                    [other.indexing.dictkey(tuplekey) for tuplekey in other],
                    [self.indexing.dictkey(tuplekey) for tuplekey in self])
            ])
        return result
    def __and__(self, other):
        '''
        Return the intersection of `self` with a `DictSet`s whose keys are disjoint with those of `self`.
        '''
        assert type(other) in {DictSet, DictSpace}
        name = f'({self.name}) & ({other.name})'
        result = DictList(name,
            self.indexing,
            sequence = [tuplekey
                 for tuplekey in self
                 if self.indexing.dictkey(tuplekey) in other])
        if result.empty(): raise ValueError(f'Empty DictList: {name}')
        return result
    def __sub__(self, other):
        '''
        Return the negation of `self` with a `DictSet`.
        '''
        assert type(other) in {DictSet, DictSpace}
        name = f'({self.name}) - ({other.name})'
        result = DictList(name,
            self.indexing,
            sequence = [tuplekey
                 for tuplekey in self
                 if self.indexing.dictkey(tuplekey) not in other])
        if result.empty(): raise ValueError(f'Empty DictList: {name}')
        return result

class DictSpace:
    '''
    `DictSpace` is a representation for all possible states that could be assumed by a dictionary,
    given that the dictionary has a set of keys, and each key has a set of values that could be assigned, 
    as defined by a dictionary, `key_to_values`.
    It supports both deterministic traversal and performant tests for memberships
    '''
    def __init__(self, name, indexing, key_to_values):
        missing = [key for key in indexing.keys if key not in key_to_values.keys()]
        if missing:
            raise ValueError(f'DictSpace indexing is missing keys: ' + ', '.join(missing))
        # missing = [key for key in key_to_values.keys() if key not in indexing.keys or type(key_to_values[key]) in {set,list}]
        # if missing:
        #     raise ValueError(f'DictSpace key_to_values is missing keys: ' + ', '.join(missing))
        constants = [key 
            for (key, values) in key_to_values.items()
            if type(values) not in {set, list}]
        self.name = name
        self.indexing = indexing | DictTupleIndexing(constants)
        # self.key_to_values = key_to_values
        self.key_to_values = {
            key: (values if type(values) in {set, list} else [values])
            for key, values in key_to_values.items()
        }
    def __str__(self):
        return '\n'.join([
            f'DictSpace {self.name}:',
            f'[{len(self)} rows]',
            *[f'{key:10}:{values}' for (key,values) in self.key_to_values.items()],
        ])
    def __repr__(self):
        return '\n'.join([
            f'DictSpace {self.name}:',
            f'[{len(self)} rows]',
            *[f'{key:10}:{values}' for (key,values) in self.key_to_values.items()],
        ])
    def __contains__(self, dictkey):
        assert type(dictkey) in {dict}
        return all([
            key in dictkey and dictkey[key] in values
            for (key,values) in self.key_to_values.items()])
        # return all([
        #     key in self.key_to_values and value in self.key_to_values[key]
        #     for (key,value) in dictkey.items()])
    def __iter__(self):
        return self.indexing.tuplekeys(self.key_to_values).__iter__()
    def __len__(self):
        return math.prod([len(self.key_to_values[key]) for key in self.indexing])
    def empty(self):
        return not any([value for value in self.key_to_values.values()])
    def fallback(self, other):
        indexing = self.indexing | other.indexing
        assert type(other) == DictSpace
        return DictSpace(
            f'({self.name}) ? ({other.name})',
            indexing,
            {**other.key_to_values,
             **self.key_to_values})
    def override(self, other):
        indexing = other.indexing | self.indexing
        assert type(other) in {DictSpace, DictList}
        if type(other) == DictSpace:
            return DictSpace(
                f'({self.name}), ({other.name})',
                indexing,
                {**self.key_to_values, 
                 **other.key_to_values})
        elif type(other) == DictList:
            return other*DictSpace('fallback',
                            self.indexing - other.indexing,
                            self.key_to_values)
    def __add__(self, other):
        '''
        Return the concatenation of two `DictList`s.
        Preserve the order of keys from `self`. Only add keys from `other` if they are unique
        '''
        name = f'({self.name}) + ({other.name})'
        indexing = self.indexing
        nonequivalent = self.indexing ^ other.indexing
        assert set(self.indexing) == set(other.indexing), '\n'.join([
            f'Indexes of "{self.name}" and "{other.name}" are not equivalent.',
            f'Addition is only supported for equivalent indexes.',
            f'The nonequivalent keys are: {nonequivalent}'])
        result = DictList(
            name, indexing,
            sequence = [
                *self,
                *[indexing.tuplekey(other.indexing.dictkey(tuplekey)) 
                  for tuplekey in other]
            ])
        return result
    def __mul__(self, other):
        '''
        Return the cartesian product of two `DictSpace`s.
        Preserve the order of keys from `self`. Only add keys from `other` if they are unique
        '''
        name = f'({self.name}) * ({other.name})'
        indexing = self.indexing | other.indexing
        overlap = self.indexing & other.indexing
        assert not bool(overlap), '\n'.join([
            f'Indexes of "{self.name}" and "{other.name}" are not disjoint.',
            f'Multiplication is only supported for disjoint indexes. ',
            f'The overlapping keys are: {overlap}'])
        if type(other) == DictList:
            tuplekeys = [
                    indexing.tuplekey({**dictkey1, **dictkey2})
                    for (dictkey1, dictkey2) in itertools.product(
                        [other.indexing.dictkey(tuplekey) for tuplekey in other],
                        [self.indexing.dictkey(tuplekey) for tuplekey in self])
                ]
            result = DictList(
                name, indexing,
                sequence = [tuplekey 
                    for tuplekey in tuplekeys
                    if indexing.dictkey(tuplekey) in self
                    or indexing.dictkey(tuplekey) in other
                ])
            return result
        elif type(other) == DictSpace:
            result = DictSpace(
                name, indexing,
                {
                    **self.key_to_values,
                    **other.key_to_values,
                })
            return result
    def __and__(self, other):
        '''
        Return the intersection of two `DictSpace`s whose keys are disjoint.
        If keys are not disjoint, replace values from `self` with those of `other`.
        '''
        name = f'({self.name}) & ({other.name})'
        result = DictList(
                name, self.indexing,
                sequence = [tuplekey
                    for tuplekey in self
                    if self.indexing.dictkey(tuplekey) in other])
        if result.empty():
            raise ValueError(f'Empty DictList: {name}')
        return result
    def __sub__(self, other):
        '''
        Return the negation of two `DictSpace`s.
        '''
        name = f'({self.name}) - ({other.name})'
        result = DictList(
                name, self.indexing,
                sequence = [tuplekey
                    for tuplekey in self
                    if self.indexing.dictkey(tuplekey) not in other])
        if result.empty():
            raise ValueError(f'Empty DictList: {name}')
        return result

class DictSet:
    '''
    `DictSet` is a data structure that uniquely stores 'dictkeys' by hashing them with a given `indexing` method,
    where `indexing` is of a class that shares the same iterface as `DictIndexing`.
    It enables performant tests for membership but forbids anky kind of traversal to prevent errors of nondeterministic ordering.
    It can be considered a set of points within a `DictSpace`.
    A 'dictkey' is a dictionary that maps each key to either a value or a set of values.
    A 'dictkey' is indexed by one or more 'tuplekeys', which are ordinary tuples of values.
    '''
    def __init__(self, name, indexing, content):
        self.name = name
        self.indexing = indexing
        self.content = set([indexing.tuplekey(entry) for entry in content])
    def __contains__(self, key):
        assert type(key) in {tuple, str, dict}
        return self.indexing.tuplekey(key) in self.content
    def __str__(self):
        cell_width = 13
        return '\n'.join([
                f'DictSet {self.name} [{len(self)} rows]:', 
                ' '.join([element.rjust(cell_width) for element in self.indexing]),
                *[' '.join([element.rjust(cell_width) for element in tuplekey]) for tuplekey in self.content],
            ])
    def __repr__(self):
        cell_width = 13
        return '\n'.join([
                f'DictSet {self.name} [{len(self)} rows]:', 
                ' '.join([element.rjust(cell_width) for element in self.indexing]),
                *[' '.join([element.rjust(cell_width) for element in tuplekey]) for tuplekey in self.content],
            ])
    def __len__(self):
        return len(self.content)
    def empty(self):
        return len(self.content) < 1

class DictLookup:
    '''
    `DictLookup` is a data structure that maps 'dictkeys' to values by hashing them with a given `indexing` method,
    where `indexing` is of a class that shares the same iterface as `DictIndexing`.
    A 'dictkey' is a dictionary that maps each key to either a value or a set of values.
    A 'dictkey' is indexed by one or more 'tuplekeys', which are ordinary tuples of values.
    '''
    def __init__(self, name, indexing, content=None):
        self.name = name
        self.indexing = indexing
        self.content = content or {}
    def __str__(self):
        cell_width = 13
        return '\n'.join([
                f'DictLookup {self.name}',
                f'[{len(self)} rows]:', 
                ' '.join([element.rjust(cell_width) for element in self.indexing]),
                *[' '.join([element.rjust(cell_width) for element in tuplekey]) + ':' + value.rjust(cell_width)
                  for (tuplekey, value) in self.content.items()],
            ])
    def __repr__(self):
        cell_width = 13
        return '\n'.join([
                f'DictLookup {self.name}',
                f'[{len(self)} rows]:', 
                ' '.join([element.rjust(cell_width) for element in self.indexing]),
                *[' '.join([element.rjust(cell_width) for element in tuplekey]) + ':' + value.rjust(cell_width)
                  for (tuplekey, value) in self.content.items()],
            ])
    def __getitem__(self, dictkey):
        '''
        Return the value that is indexed by `dictkey` 
        if it is the only such value, otherwise return None.
        '''
        assert type(dictkey) in {tuple, str, dict}
        if type(dictkey) in {tuple,str}:
            return self.content[dictkey]
        else:
            # self.indexing.check(dictkey)
            tuplekeys = [tuplekey 
                for tuplekey in self.indexing.tuplekeys(dictkey)
                if tuplekey in self.content]
            if len(tuplekeys) == 1:
                return self.content[tuplekeys[0]]
            elif len(tuplekeys) == 0:
                self.indexing.check(dictkey)
                raise KeyError('\n'.join([
                                    'Key does not exist within the dictionary.',
                                    *(['Lookup:', '\t'+str(self.name)] if self.name else []),
                                    'Key:', '\t'+str(dictkey),
                                    'Attempted interpretations:',
                                    *['\t'+str(self.indexing.dictkey(tuplekey)) 
                                      for tuplekey in self.indexing.tuplekeys(dictkey)]
                                ]))
            else:
                raise KeyError('\n'.join([
                                    'Key is ambiguous.',
                                    *(['Lookup:', '\t'+str(self.name)] if self.name else []),
                                    'Key:', '\t'+str(dictkey),
                                    'Available interpretations:',
                                    *['\t'+str(self.indexing.dictkey(tuplekey)) 
                                      for tuplekey in tuplekeys]
                                ]))
    def __setitem__(self, dictkey, value):
        '''
        Store `value` within the indices represented by `dictkey`.
        '''
        assert type(dictkey) in {tuple, str, dict}
        if type(dictkey) in {tuple,str}:
            self.content[dictkey] = value
        else:
            # self.indexing.check(dictkey)
            for tuplekey in self.indexing.tuplekeys(dictkey):
                if tuplekey in self.content and value != self.content[tuplekey]:
                    raise KeyError('\n'.join([
                                    'Key already exists within the dictionary.',
                                    *(['Lookup:', '\t'+str(self.name)] if self.name else []),
                                    'Key:', '\t'+str(self.indexing.dictkey(tuplekey)),
                                    'Old Value:', '\t'+str(self.content[tuplekey]),
                                    'New Value:', '\t'+str(value),
                                ]))
                else:
                    self.content[tuplekey] = value
    def __call__(self, other):
        inpath = [other.indexing.dictkey(point) for point in other]
        indexing = DictTupleIndexing(
            list(OrderedDict.fromkeys(key for inpoint in inpath 
                        if inpoint in self
                        for key in self[inpoint].keys()))
        )
        overlap  = indexing & other.indexing
        indexing = indexing | other.indexing
        assert not bool(overlap), '\n'.join([
            f'Indexes of "{self.name}" and "{other.name}" are not disjoint.',
            f'Composition is only supported for disjoint indexes. ',
            f'The overlapping keys are: {overlap}'])
        composition = DictList(
            f'({self.name})∘({other.name})', indexing, 
            [indexing.tuplekey({**self[inpoint], **inpoint})
             for inpoint in inpath
             if inpoint in self])
        return composition
    def __contains__(self, dictkey):
        assert type(dictkey) in {tuple, str, dict}
        if type(dictkey) in {tuple,str}:
            return dictkey in self.content
        else:
            # self.indexing.check(dictkey)
            tuplekeys = list(self.indexing.tuplekeys(dictkey))
            return len(tuplekeys) == 1 and tuplekeys[0] in self
    def __iter__(self):
        return self.content.__iter__()
    def __len__(self):
        return self.content.__len__()

class DefaultDictLookup:
    '''
    `DictLookup` is a lookup that indexes 'dictkeys' by a given `indexing` method,
    where `indexing` is of a class that shares the same iterface as `DictIndexing`.
    A 'dictkey' is a dictionary that maps each key to either a value or a set of values.
    A 'dictkey' is indexed by one or more 'tuplekeys', which are ordinary tuples of values.
    '''
    def __init__(self, name, indexing, get_default, content=None):
        self.name = name
        self.indexing = indexing
        self.get_default = get_default
        self.content = content or {}
    def __getitem__(self, key):
        '''
        Return the value that is indexed by `key` 
        if it is the only such value, otherwise return None.
        '''
        assert type(key) in {tuple, str, dict}
        if type(key) in {tuple, str}:
            if key in self.content:
                return self.content[key]
            else:
                value = self.get_default(self.indexing.dictkey(key))
                self.content[key] = value
                return value
        else:
            # if type(key) in {dict}:
            #     assert all([type(value)==list for (key, value) in key.items()]), 'key should not map keys to lists'
            # self.indexing.check(key)
            tuplekeys = list(self.indexing.tuplekeys(key))
            if len(tuplekeys) == 1:
                return self.__getitem__(tuplekeys[0])
            else:
                raise KeyError('\n'.join([
                                    'Key is ambiguous.',
                                    *(['Lookup:', '\t'+str(self.name)] if self.name else []),
                                    'Key:', '\t'+str(key),
                                    'Available interpretations:',
                                    *['\t'+str(self.indexing.dictkey(tuplekey)) 
                                      for tuplekey in tuplekeys]
                                ]))
    def __setitem__(self, key, value):
        '''
        Store `value` within the indices represented by `key`.
        '''
        assert type(key) in {tuple, str, dict}
        if type(key) in {tuple, str}:
            self.content[key] = value
        else:
            if type(key) in {dict}:
                assert all([type(value)==list for (key, value) in key.items()]), 'key should not map keys to lists'
            # self.indexing.check(key)
            for tuplekey in self.indexing.tuplekeys(key):
                if tuplekey in self.content and value != self.content[tuplekey]:
                    raise KeyError('\n'.join([
                                    'Key already exists within the dictionary.',
                                    *(['Lookup:', '\t'+str(self.name)] if self.name else []),
                                    'Key:', '\t'+str(self.indexing.dictkey(tuplekey)),
                                    'Old Value:', '\t'+str(self.content[tuplekey]),
                                    'New Value:', '\t'+str(value),
                                ]))
                else:
                    self.content[tuplekey] = value
    def __contains__(self, key):
        assert type(key) in {tuple, str, dict}
        if type(key) in {tuple,str}:
            return key in self.content
        else:
            # if type(key) in {dict}:
            #     assert all([type(value)==list for (key, value) in key.items()]), 'key should not map keys to lists'
            # self.indexing.check(key)
            tuplekeys = list(self.indexing.tuplekeys(key))
            return len(tuplekeys) == 1 and tuplekeys[0] in self
    def __iter__(self):
        return self.content.__iter__()
    def __len__(self):
        return self.content.__len__()

class NestedDictLookup:
    '''
    `NestedDictLookup` is a lookup that wraps nested DictLookups
    '''
    def __init__(self, dict_lookups):
        self.dict_lookups = dict_lookups
    def __getitem__(self, key):
        assert type(key) in {tuple, str, dict}
        return self.dict_lookups[key][key]
    def __setitem__(self, key, value):
        assert type(key) in {tuple, str, dict}
        self.dict_lookups[key][key] = value
    def __contains__(self, key):
        return key in self.dict_lookups and key in self.dict_lookups[key]

class FallbackDictLookup:
    '''
    `NestedDictLookup` is a lookup that returns a procedural value if no value is found from an inner lookup
    '''
    def __init__(self, main, fallback):
        self.main = main
        self.fallback = fallback
    def __getitem__(self, key):
        assert type(key) in {tuple, str, dict}
        if key in self.main:
            return self.main[key]
        else:
            value = self.fallback[key]
            self.main[key] = value
            return value
    def __setitem__(self, key, value):
        assert type(key) in {tuple, str, dict}
        self.main[key] = value
    def __contains__(self, key):
        assert type(key) in {tuple, str, dict}
        return True

class UniformDictLookup:
    '''
    `UniformDictLookup` is a lookup that returns a constant for any index
    '''
    def __init__(self, constant):
        self.constant = constant
    def __getitem__(self, key):
        assert type(key) in {tuple, str, dict}
        return self.constant
    def __contains__(self, key):
        assert type(key) in {tuple, str, dict}
        return True
    def __iter__(self):
        return [self.constant].__iter__()

class ProceduralLookup:
    '''
    `ProceduralLookup` is a lookup that returns a value that is procedurally determined from the key
    '''
    def __init__(self, get):
        self.get = get
    def __getitem__(self, key):
        assert type(key) in {tuple, str, dict}
        return self.get(key)
    def __contains__(self, key):
        assert type(key) in {tuple, str, dict}
        return True
