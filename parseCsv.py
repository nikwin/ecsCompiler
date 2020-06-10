import pyparsing as pp

result = None

def makeCsvTokenParser():
    num = pp.Combine(pp.Optional('-') + pp.Word(pp.nums))
    num.setParseAction(lambda toks: int(toks[0]))

    floatNum = pp.Combine(pp.Optional('-') + pp.Word(pp.nums) + '.' + pp.Word(pp.nums))
    floatNum.setParseAction(lambda toks: float(toks[0]))
    
    identifier = pp.Word(pp.alphanums + " -_.?'>+,![]\";%")

    colonString = pp.Combine(identifier + ': ' + identifier)

    basicToken = num ^ floatNum ^ identifier ^ colonString

    lst = pp.Forward()
    dct = pp.Forward()

    lparen = pp.Suppress('(')
    rparen = pp.Suppress(')')

    lstToken = pp.Group(lparen + lst + rparen)
    dctToken = pp.Group(lparen + dct + rparen)
    token = basicToken ^ lstToken ^ dctToken
    
    singletonLst = token + pp.Suppress('|')
    multiLst = pp.delimitedList(token, delim='|')
    lst << pp.Group(singletonLst ^ multiLst)

    def fn(toks):
        simpleToks = [simplify(part, True) for part in toks[0]]
        return [simpleToks]

    lst.setParseAction(fn)

    dctKey = identifier + (pp.Suppress(':') ^ pp.StringEnd())
    dctVal = token + pp.Suppress(pp.Optional('|'))
    dct << pp.Group(pp.dictOf(dctKey, dctVal))
    dct.setParseAction(lambda toks: {key: simplify(val, True) for key, val in toks[0]})
    
    global result
    result = basicToken ^ lst ^ dct
    

def parseCsvToken(st):
    if st == '':
        return None

    global result

    if not result:
        makeCsvTokenParser()
    
    try:
        parseResult = result.parseString(st, parseAll=True)
    except (pp.ParseException, ValueError) as e:
        print(st)
        raise e
    return simplify(parseResult[0], False)

def simplify(parseResult, index):
    if type(parseResult) in [str, int, float, dict, list]:
        return parseResult
    else:
        return parseResult.asList()[0] if index else parseResult.asList()

def tokenToString(token, wrap=False):
    if token == None:
        return ''
    if type(token) == list:
        st = '|'.join(tokenToString(ele, True) for ele in token)
        if len(token) == 1:
            st += '|'
    elif type(token) == dict:
        items = list(token.items())
        items.sort(key = lambda ele: ele[0])
        st = '|'.join('{}:{}'.format(key, tokenToString(val, True)) for key, val in items)
    else:
        return str(token)

    return '({})'.format(st) if wrap else st

if __name__ == '__main__':
    chks = (
        ('', None),
        ('12', 12),
        ('-3', -3),
        ('0.5', 0.5),
        ('abc', 'abc'),
        ('abc def', 'abc def'),
        ('a.b-c', 'a.b-c'),
        ('abc|', ['abc']),
        ('abc|12|sxy', ['abc', 12, 'sxy']),
        ('abc:12', {'abc': 12}),
        ('abc:12|xyz:2', {'abc': 12, 'xyz': 2}),
        ('abc:(12|a)|xyz:2', {'abc': [12, 'a'], 'xyz': 2}),
        ('abc:(a:12)', {'abc': {'a': 12}}),
        ('(a:2)|3', [{'a': 2}, 3]),
        ('a:that and this|b:this and that', {'a': 'that and this', 'b': 'this and that'}),
        ('a: b', 'a: b'),
        ('a:b', {'a': 'b'})
    )

    for token, chk in chks:
        assert(parseCsvToken(token) == chk)
        assert(tokenToString(parseCsvToken(token)) == token)
