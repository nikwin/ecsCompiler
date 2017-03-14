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
    
    def __init__(self, token, key):
        super(HashParse, self).__init__(token[1:])
        
class KeyHashParse(SimpleParse):
    @staticmethod
    def canParse(token):
        return token == '#'
    
    def __init__(self, token, key):
        super(KeyHashParse, self).__init__(key)
        
class EcsRef(object):
    ecsRegex = '(.+)\(\)'
    @classmethod
    def canParse(cls, token):
        return re.match(cls.ecsRegex, token)
    
    def __init__(self, token, key):
        mat = re.match(self.ecsRegex, token)
        self.ecsRef = mat.group(1)

    def valToInsert(self):
        return 'ecs.{0}(args)'.format(self.ecsRef)

class KeyEcsRef(EcsRef):
    @staticmethod
    def canParse(token):
        return token == '()'
    
    def __init__(self, token, key):
        self.ecsRef = key

class BoolParse(SimpleParse):
    @staticmethod
    def canParse(token):
        return token in ('true', 'false')
    
    def __init__(self, token, key):
        super(BoolParse, self).__init__(token)

class IntParse(SimpleParse):
    @staticmethod
    def canParse(token):
        try:
            int(token)
            return True
        except ValueError:
            return False

    def __init__(self, token, key):
        super(IntParse, self).__init__(int(token))

class FloatParse(SimpleParse):
    @staticmethod
    def canParse(token):
        try:
            float(token)
            return True
        except ValueError:
            return False

    def __init__(self, token, key):
        super(FloatParse, self).__init__(float(token))

class ListParse(object):
    @staticmethod
    def canParse(token):
        return token[0] == '['

    def __init__(self, token, key):
        st = token[1:-1]
        self.lst = [parseToken(s.strip(), key) for s in st.split(',')] if st else []
        
    def valToInsert(self):
        return '[{0}]'.format(', '.join(str(parsed.valToInsert()) for parsed in self.lst))


class ConditionParse(object):
    conditionRegex = '\?\((.+)\) (.*)'
    @classmethod
    def canParse(cls, token):
        return re.match(cls.conditionRegex, token)
    
    def __init__(self, token, key):
        mat = re.match(self.conditionRegex, token)
        groups = mat.groups()
        self.condition = groups[0]
        self.token = parseToken(groups[1], key)

    def valToInsert(self):
        return '({0}) ? {1} : undefined'.format(self.condition, self.token.valToInsert())

class CheckDefaultParse(object):
    @staticmethod
    def canParse(token):
        return token[0] == '?'

    def __init__(self, token, key):
        self.key = key
        self.token = parseToken(token[1:], key)
        
    def valToInsert(self):
        return '(args["{0}"] === undefined) ? {1} : args["{0}"]'.format(self.key, self.token.valToInsert())

class StringParse(SimpleParse):
    @staticmethod
    def canParse(token):
        return token[0] == '"'
    
    def __init__(self, token, key):
        super(StringParse, self).__init__(token)

class DefaultParse(object):
    @staticmethod
    def canParse(token):
        return True
    
    def __init__(self, token, key):
        self.argKey = token

    def valToInsert(self):
        return "args['{0}']".format(self.argKey)

class BlankParse(DefaultParse):
    @staticmethod
    def canParse(token):
        return not token
    
    def __init__(self, token, key):
        self.argKey = key

    def getAsserts(self):
        return self.argKey
        
def parseToken(token, key):
    parsers = (
        BlankParse,
        KeyHashParse, 
        HashParse, 
        KeyEcsRef, 
        BoolParse, 
        IntParse,
        FloatParse,
        ListParse,
        ConditionParse,
        CheckDefaultParse,
        StringParse,
        EcsRef,
        DefaultParse
    )
    for parser in parsers:
        if parser.canParse(token):
            return parser(token, key)
    return None
