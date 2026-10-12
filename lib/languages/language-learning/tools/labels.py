from tools.indexing import DictKeyIndexing, DictTupleIndexing
from tools.dictstores import DictSpace, DictList, DictSet, DictLookup

class TermLabelEditing:
    '''
    Edits labels that are appended to the keys and values of `dictstores`.
    '''
    def __init__(self):
        pass
    def term(self, term, append='', strip=''):
        dashstrip = f'-{strip}' if strip else ''
        dashappend = f'-{append}' if append else ''
        return term.removesuffix(dashstrip) + dashappend
    def termaxis(self, termaxis, append='', strip=''):
        stripdash = f'{strip}-' if strip else ''
        appenddash = f'{append}-' if append else ''
        return appenddash+termaxis.removeprefix(stripdash)
    def terms(self, terms, append='', strip=''):
        return [self.term(term, append, strip) for term in terms]
    def termaxes(self, termaxes, append='', strip=''):
        return [self.termaxis(termaxis, append, strip) for termaxis in termaxes]
    def termaxis_to_term(self, termaxis_to_term, append='', strip=''):
        return {self.termaxis(termaxis,append,strip):self.term(term,append,strip) 
                for termaxis,term in termaxis_to_term.items()}
    def termaxis_to_terms(self, termaxis_to_terms, append='', strip=''):
        return {self.termaxis(termaxis,append,strip):self.terms(terms,append,strip) 
                for termaxis,terms in termaxis_to_terms.items()}
    def termpoint(self, termpoint, append='', strip=''):
        return tuple([self.term(term, append, strip) for term in termpoint])
    def termpoints(self, termpoints, append='', strip=''):
        return [self.termpoint(termpoint, append, strip) for termpoint in termpoints]
    def terms_to_token(self, terms_to_token, append='', strip=''):
        return {self.termpoint(termpoint):token for termpoint,token in terms_to_token.items()}
    def termindexing(self, indexing, append='', strip=''):
        '''NOTE: fuck polymorphism, I don't want to pollute *Indexing classes
        with design decisions that regard how *Labeling represents labels in strings'''
        return {
            DictKeyIndexing:   lambda: DictKeyIndexing(self.termaxis(indexing.key, append, strip)),
            DictTupleIndexing: lambda: DictTupleIndexing(
                self.termaxes(indexing.keys, append, strip),
                self.termaxis_to_terms(indexing.defaults, append, strip)
            )
        }[type(indexing)]()
    def termspace(self, termspace, append='', strip=''):
        return DictSpace(termspace.name, 
            self.termindexing(termspace.indexing, append, strip),
            self.termaxis_to_terms(termspace.key_to_values, append, strip)
        )
    def termmask(self, termmask, append='', strip=''):
        return DictSet(termmask.name, 
            self.termindexing(termmask.indexing, append, strip),
            set(self.termpoints(termmask.content, append, strip))
        )
    def termpath(self, termpath, append='', strip=''):
        return DictList(termpath.name, 
            self.termindexing(termpath.indexing, append, strip),
            self.termpoints(termpath.sequence, append, strip)
        )
    def termfield(self, termfield, append='', strip=''):
        return DictLookup(termfield.name, 
            self.termindexing(termfield.indexing, append, strip),
            self.terms_to_token(termfield.content, append, strip)
        )

class TermLabelFiltering:
    '''
    Edits labels that are appended to the keys and values of `dictstores`.
    '''
    def __init__(self):
        pass
    def term(self, term, label):
        return term.endswith(f'-{label}')
    def termaxis(self, termaxis, label):
        return termaxis.startswith(f'{label}-')
    def terms(self, terms, label):
        return [term for term in terms if self.term(term, label)]
    def termaxes(self, termaxes, label):
        return [termaxis for termaxis in termaxes if self.termaxis(termaxis, label)]
    def termaxis_to_term(self, termaxis_to_term, label):
        return {termaxis:term for termaxis,term in termaxis_to_term.items() if self.termaxis(termaxis, label)}
    def termaxis_to_terms(self, termaxis_to_term, label):
        return {termaxis:terms for termaxis,terms in termaxis_to_term.items() if self.termaxis(termaxis, label)}
    def termpoint(self, terms, label):
        return tuple([term for term in terms if self.term(term, label)])
    def termpoints(self, termpoints, label):
        return [termpoint for termpoint in termpoints if self.termpoint(termpoint, label)]
    def terms_to_token(self, terms_to_token, label):
        return {self.termpoint(termpoint, label):value for termpoint,value in terms_to_token.items()}
    def termindexing(self, indexing, label):
        #NOTE: this function only makes sense if indexing is an instance of DictTupleIndexing
        return DictTupleIndexing(
            self.termaxes(indexing.keys, label),
            self.termaxis_to_terms(indexing.defaults, label)
        )
    def termspace(self, termspace, label):
        return DictSpace(termspace.name, 
            self.termindexing(termspace.indexing, label),
            self.termaxis_to_terms(termspace.key_to_values, label)
        )
    def termmask(self, termmask, label):
        return DictSet(termmask.name, 
            self.termindexing(termmask.indexing, label),
            set(self.termpoints(termmask.content, label))
        )
    def termpath(self, termpath, label):
        return DictList(termpath.name, 
            self.termindexing(termpath.indexing, label),
            self.termpoints(termpath.sequence, label)
        )
    def termfield(self, termfield, label):
        return DictLookup(termfield.name, 
            self.termindexing(termfield.indexing, label),
            self.terms_to_token(termfield.content, label)
        )
