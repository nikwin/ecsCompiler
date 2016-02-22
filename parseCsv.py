import pyparsing as pp

def parseCsvToken(st):
    if st == '':
        return None
    num = pp.Combine(pp.Optional('-') + pp.Word(pp.nums))
    num.setParseAction(lambda toks: int(toks[0]))

    floatNum = pp.Combine(pp.Optional('-') + pp.Word(pp.nums) + '.' + pp.Word(pp.nums))
    floatNum.setParseAction(lambda toks: float(toks[0]))
    
    identifier = pp.Word(pp.alphanums + ' ')
    basicToken = num ^ floatNum ^ identifier

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
    
    result = basicToken ^ lst ^ dct
    try:
        parseResult = result.parseString(st, parseAll=True)
    except (pp.ParseException, ValueError) as e:
        print st
        raise e
    return simplify(parseResult[0], False)

def simplify(parseResult, index):
    if type(parseResult) in [str, int, float, dict, list]:
        return parseResult
    else:
        return parseResult.asList()[0] if index else parseResult.asList()

if __name__ == '__main__':
    assert(parseCsvToken('') == None)
    assert(parseCsvToken('12') == 12)
    assert(parseCsvToken('-3') == -3)
    assert(parseCsvToken('0.5') == 0.5)
    assert(parseCsvToken('abc') == 'abc')
    assert(parseCsvToken('abc|') == ['abc'])
    assert(parseCsvToken('abc|12|sxy') == ['abc', 12, 'sxy'])
    assert(parseCsvToken('abc:12') == {'abc': 12})
    assert(parseCsvToken('abc:12|xyz:2') == {'abc': 12, 'xyz': 2})
    assert(parseCsvToken('abc:(12|a)|xyz:2') == {'abc': [12, 'a'], 'xyz': 2})
    assert(parseCsvToken('abc:(a:12)') == {'abc': {'a': 12}})
    assert(parseCsvToken('(a:2)|3') == [{'a': 2}, 3])
