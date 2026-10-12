class DictBundles:
    '''
    `DictBundles` converts between two representations of a pure function,
    each encoded as a dictionary: a map, from each germ to its stalk,
    and a mathematical bundle, from each stalk to the germs that the function maps to it.
    `map_to_bundle` and `bundle_to_map` are inverse to each other.
    '''
    def __init__(self):
        pass
    def bundle_to_map(self, bundle):
        '''
        Given a mathematical bundle that is encoded as a dictionary,
        `bundle_to_map` returns the inverse of that bundle as a dictionary,
        i.e., a pure function that is encoded as a dictionary and maps each germ in the bundle to its respective stalk.
        '''
        return {
            germ:stalk 
            for (stalk, germs) in bundle.items() 
            for germ in germs
        }
    def map_to_bundle(self, map):
        '''
        Given a pure function that is encoded as a dictionary,
        `map_to_bundle` returns the inverse of that function as a dictionary,
        i.e., a mathematical bundle that maps each stalk to the germs that the function maps to it.
        '''
        bundle = {}
        for (germ, stalk) in map.items():
            bundle.setdefault(stalk, []).append(germ)
        return bundle
