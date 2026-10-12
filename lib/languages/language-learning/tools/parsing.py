import re

from tools.indexing import DictTupleIndexing
from tools.dictstores import DictSpace, DictList, DictSet, DictLookup

class SeparatedValuesFileParsing:
    '''
    Parses files composed of rows of values that are separated by `delimeters`.
    '''
    def __init__(self, comment='#', delimeter='\t', padding=' \t\r\n', quotation='"'):
        self.comment = comment
        self.delimeter = delimeter
        self.padding = padding
    def rows(self, filename):
        rows_ = []
        with open(filename) as file:
            for line in file.readlines():
                if self.comment is not None:
                    line = line.split(self.comment)[0]
                if len(line.strip()) >= 1:
                    rows_.append([column.strip(self.padding) for column in line.split(self.delimeter)])
        return rows_


class TokenParsing:
    '''
    Parses data structures that are populated by strings that represent tokens.
    "Tokens" are arbitrary strings that use a restricted characterset: [0-9a-z-]
    `TokenParsing` leverages the above guarantee to simplify deck construction and guarantee validity.
    '''
    def __init__(self):
        self.comment_regex = re.compile(r'#[^\n]*')
    def tokens(self, string):
        return [token.strip() for token in string.split()]
    def tokenpoints(self, string):
        tokenbreak = '\n' if '\n' in string else ','
        rows = [row.split('#')[0]
            for row in string.split(tokenbreak)]
        tokenpoints = [tuple(self.tokens(row))
            for row in rows
            if row.strip()]
        return tokenpoints
    def token_to_text(self, string):
        return {
            key: ' '.join(tokens)
            for (key,tokens) in self.token_to_tokens(string).items()
        }
    def token_to_tokens(self, string):
        def itemtoken(item):
            tokens = [token.strip() for token in item.split()]
            return [token for token in tokens if token]
        uncommented = re.sub(self.comment_regex,'',string)
        itemtokens = [itemtoken(row) for row in uncommented.split(':')]
        token_to_text = [[last[-1], current[:-1] if i < len(itemtokens)-2 else current]
            for i, (last,current) in enumerate(zip(itemtokens[:-1],itemtokens[1:]))]
        keys = sorted([item[0] for item in token_to_text])
        dupes = list(set(keys[::2]) & set(keys[1::2]))
        assert not dupes, (
                    '\n'.join([
                        'The error occurs here:',
                        string,
                        'The following keys have duplicate entries: ',
                        *[str(dupe) for dupe in dupes]
                    ]))
        result = {item[0] : item[1]
            for item in token_to_text}
        return result
    def tokenindexing(self, header):
        return DictTupleIndexing(self.tokens(header))
    def tokenpath(self, name, header, body):
        return DictList  (name, self.tokenindexing(header), self.tokenpoints(body))
    def tokenmask(self, name, header, body):
        return DictSet   (name, self.tokenindexing(header), self.tokenpoints(body))
    def tokenspace(self, name, header, body):
        return DictSpace (name, self.tokenindexing(header), self.token_to_tokens(body))
    def tokenfield(self, name, header, body=''):
        assert not body, "support for `body` parameter is not currently implemented"
        return DictLookup(name, self.tokenindexing(header), self.token_to_text(body))


class TermParsing(TokenParsing):
    '''
    Parses native data structures that are populated by strings that represent terms, and termaxes.
    "Terms" are tokens that assume one of several values that are known ahead of time.
    Each terms has a single "Termaxis" associated with it, as given by `term_to_termaxis`.
    `TermParsing` leverages the above guarantees to simplify deck construction and guarantee validity.
    An error is generated if tokens do not match any known term name from `term_to_termaxis`.
    '''
    def __init__(self, term_to_termaxis):
        super().__init__()
        self._term_to_termaxis = term_to_termaxis
        self._terms = set(term_to_termaxis.keys())
        self._termaxes = set(term_to_termaxis.values())
    def term(self, string):
        stripped = string.strip()
        assert stripped in self._terms, f'term is invalid: {stripped}'
        return stripped
    def termaxis(self, string):
        stripped = string.strip()
        assert stripped in self._termaxes, f'termaxis is invalid: {stripped}'
        return stripped
    def terms(self, string):
        tokens = self.tokens(string)
        invalid = {token
            for token in tokens
            if token not in self._terms}
        assert not invalid, f'The following terms are invalid: {invalid}'
        return tokens
    def termaxes(self, string):
        tokens = self.tokens(string)
        invalid = {token
            for token in tokens
            if token not in self._termaxes}
        assert not invalid, f'The following termaxes are invalid: {invalid}'
        return tokens
    def termpoints(self, string):
        tokenpoints = self.tokenpoints(string)
        invalid = [cell
            for row in tokenpoints
            for cell in list(row)
            if cell not in self._terms]
        assert not invalid, f'The following terms are invalid: {invalid}'
        termaxispoints = [
            tuple([self._term_to_termaxis[cell] 
                   for cell in row])
            for row in tokenpoints]
        termaxis_signatures = set(termaxispoints)
        assert len(termaxis_signatures) == 1, (
                    '\n'.join([
                        'The error occurs here:',
                        string,
                        'The error is that rows in the table do not represent the same set of termaxes: ',
                        *[str(signature) for signature in termaxis_signatures]
                    ]))
        (termaxis_signature,) = termaxis_signatures
        sorted_termaxis_signature = sorted(termaxis_signature)
        dupes = list(set(sorted_termaxis_signature[::2]) & set(sorted_termaxis_signature[1::2]))
        assert not dupes, (
                    '\n'.join([
                        'The error occurs here:',
                        string,
                        'The error is that the following termaxes occur in multiple columns: ',
                        *[str(dupe) for dupe in dupes]
                    ]))
        return tokenpoints
    def termaxis_to_term(self, string):
        delimeter = '\n' if '\n' in string else ','
        if ':' in string:
            result = self.token_to_text(string)
            invalid = {token
                for token in result.keys()
                if token not in self._termaxes}
            assert not invalid, f'The following termaxes are invalid: {invalid}'
            invalid = {token
                for token in result.values()
                if token not in self._terms}
            assert not invalid, f'The following terms are invalid: {invalid}'
            return result
        else:
            '''
            term_to_termaxis guarantees that to each term there is a known termaxis
            since termaxis is completely determined by term, 
            termaxis_to_term() is uniquely determined by a list of terms
            '''
            items = [[self._term_to_termaxis[term], term]
                for term in self.terms(string)]
            keys = sorted([item[0] for item in items])
            dupes = list(set(keys[::2]) & set(keys[1::2]))
            assert not dupes, f'The following keys have duplicate entries: {dupes}'
            return {item[0]: item[1]
                for item in items}
    def termaxis_to_terms(self, string):
        if ':' in string:
            result = self.token_to_tokens(string)
            invalid = {key
                for key in result.keys()
                if key not in self._termaxes}
            assert not invalid, f'The following termaxes are invalid: {invalid}'
            invalid = {value
                for values in result.values()
                for value in values
                if value not in self._terms}
            assert not invalid, f'The following terms are invalid: {invalid}'
            return result
        else:
            values = self.terms(string)
            term_termaxes = [[value, self._term_to_termaxis[value]]
                for value in values]
            termaxes = [termaxis for (term,termaxis) in term_termaxes]
            result = {}
            for (term,termaxis) in term_termaxes:
                result[termaxis] = set() if termaxis not in result else result[termaxis]
                result[termaxis].add(term)
            return result
    def termindexing(self, header):
        return DictTupleIndexing(self.termaxes(header))
    def termpath(self, name, header, body):
        return DictList  (name, self.termindexing(header), self.termpoints(body))
    def termmask(self, name, header, body):
        return DictSet   (name, self.termindexing(header), self.termpoints(body))
    def termspace(self, name, header, body):
        return DictSpace (name, self.termindexing(header), self.termaxis_to_terms(body))
    def termfield(self, name, header, body=''):
        assert not body, "support for `body` parameter is not currently implemented"
        return DictLookup(name, self.termindexing(header), {})

class ListParsing:
    '''
    Parses lisp like text to a list of strings
    Start and end parentheses are denoted by 'L' and 'R' strings.
    To simplify implementation, start and end parentheses should be avoided in text 
    unless they indicate L and R.
    To guarantee security, we strongly discourage any manipulation of input `string`s
    if there is a chance that the parser will handle public facing input.
    Modification of `LispInterpreter` and its usages should not proceed until the above sentence is understood.
    '''
    def __init__(self, L='[', R=']'):
        self.L = L
        self.R = R
    def parse(self, string):
        open_count = 0
        stack = [[]]
        # standardize string so that it can be handled without regex escape codes
        standardized = string
        standardized = standardized.replace(self.L,'(')
        standardized = standardized.replace(self.R,')')
        for match in re.finditer('[()]|[^() ]+', standardized):
            token = match.group(0)
            if token == '(':
                stack.append([])
            elif token == ')':
                closed = stack.pop()
                stack[-1].append(closed)
            elif len(token.strip()):
                stack[-1].append(token)
        assert len(stack) == 1, f'start and end delimeter mismatch in string: {string}'
        return stack[0]

class LatexlikeParsing:
    '''
    Introduces LaTEX like escape sequences (e.g.\\foo{bar}).
    The style of start and end marker is described by the given `enclosure`.
    '''
    def __init__(self, enclosure):
        self.enclosure = enclosure
    def decode(self, pattern, string, get_replacement):
        match = re.search(pattern, string)
        while match is not None:
            posttag = string[match.end():]
            bracket_range = self.enclosure.find(posttag)
            if not bracket_range: break
            start, end = bracket_range
            string = ''.join([
                string[:match.start()],
                get_replacement(posttag[start:end]), 
                posttag[end+len(self.enclosure.R):]])
            match = re.search(pattern, string)
        return string
