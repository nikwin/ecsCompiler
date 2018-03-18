import re

class SimpleParse(object):
    def __init__(self, parsedVal):
        self.parsedVal = parsedVal
        
    def valToInsert(self):
        return self.parsedVal

class HashParse(SimpleParse):
    @staticmethod
    def canParse(token):
        return token[0] == '#'
    
    def __init__(self, token, key, fil):
        super(HashParse, self).__init__(token[1:])
        
class KeyHashParse(SimpleParse):
    @staticmethod
    def canParse(token):
        return token == '#'
    
    def __init__(self, token, key, fil):
        super(KeyHashParse, self).__init__(key)
        
class EcsRef(object):
    ecsRegex = '(.+)\(\)'
    @classmethod
    def canParse(cls, token):
        return re.match(cls.ecsRegex, token)
    
    def __init__(self, token, key, fil):
        mat = re.match(self.ecsRegex, token)
        self.ecsRef = mat.group(1)

    def valToInsert(self):
        return 'ecs.{0}(args)'.format(self.ecsRef)

class KeyEcsRef(EcsRef):
    @staticmethod
    def canParse(token):
        return token == '()'
    
    def __init__(self, token, key, fil):
        self.ecsRef = key

class KeywordParse(SimpleParse):
    @staticmethod
    def canParse(token):
        return token in ('true', 'false', 'undefined')
    
    def __init__(self, token, key, fil):
        super(KeywordParse, self).__init__(token)

class IntParse(SimpleParse):
    @staticmethod
    def canParse(token):
        try:
            int(token)
            return True
        except ValueError:
            return False

    def __init__(self, token, key, fil):
        super(IntParse, self).__init__(int(token))

class FloatParse(SimpleParse):
    @staticmethod
    def canParse(token):
        try:
            float(token)
            return True
        except ValueError:
            return False

    def __init__(self, token, key, fil):
        super(FloatParse, self).__init__(float(token))

class ListParse(object):
    @staticmethod
    def canParse(token):
        return token[0] == '['

    def __init__(self, token, key, fil):
        st = token[1:-1]
        self.lst = [parseToken(s.strip(), key, fil) for s in st.split(',')] if st else []
        
    def valToInsert(self):
        return '[{0}]'.format(', '.join(str(parsed.valToInsert()) for parsed in self.lst))


class ConditionParse(object):
    conditionRegex = '\?\((.+)\) (.*)'
    @classmethod
    def canParse(cls, token):
        return re.match(cls.conditionRegex, token)
    
    def __init__(self, token, key, fil):
        mat = re.match(self.conditionRegex, token)
        groups = mat.groups()
        self.condition = groups[0]
        self.token = parseToken(groups[1], key, fil)

    def valToInsert(self):
        return '({0}) ? {1} : undefined'.format(self.condition, self.token.valToInsert())

class CheckDefaultParse(object):
    @staticmethod
    def canParse(token):
        return token[0] == '?'

    def __init__(self, token, key, fil):
        self.key = key
        self.token = parseToken(token[1:], key, fil)
        
    def valToInsert(self):
        return '(args["{0}"] === undefined) ? {1} : args["{0}"]'.format(self.key, self.token.valToInsert())

class StringParse(SimpleParse):
    @staticmethod
    def canParse(token):
        return token[0] == '"'
    
    def __init__(self, token, key, fil):
        super(StringParse, self).__init__(token)

class DefaultParse(object):
    @staticmethod
    def canParse(token):
        return True
    
    def __init__(self, token, key, fil):
        self.argKey = token

    def valToInsert(self):
        return "args['{0}']".format(self.argKey)

class BlankParse(DefaultParse):
    @staticmethod
    def canParse(token):
        return not token
    
    def __init__(self, token, key, fil):
        self.argKey = key

    def getAsserts(self):
        return self.argKey

class TildeParse(EcsRef):
    tildeRegex = '~(.+)\(\)'
    
    @classmethod
    def canParse(cls, token):
        return re.match(cls.tildeRegex, token)

    def __init__(self, token, key, fil):
        mat = re.match(self.tildeRegex, token)
        baseClass = mat.group(1)
        self.ecsRef = fil + baseClass[0].upper() + baseClass[1:]

class OnlyTildeParse(EcsRef):
    @staticmethod
    def canParse(token):
        return token == '~()'

    def __init__(self, token, key, fil):
        self.ecsRef = fil + key[0].upper() + key[1:]

    
def parseToken(token, key, fil):
    parsers = (
        BlankParse,
        KeyHashParse, 
        HashParse, 
        KeyEcsRef, 
        KeywordParse, 
        IntParse,
        FloatParse,
        ListParse,
        ConditionParse,
        CheckDefaultParse,
        StringParse,
        OnlyTildeParse,
        TildeParse,
        EcsRef,
        DefaultParse
    )
    for parser in parsers:
        if parser.canParse(token):
            return parser(token, key, fil)
    return None
