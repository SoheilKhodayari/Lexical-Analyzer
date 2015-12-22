import re
from functools import reduce

lineCount=1
blkNO = 0
blkORD = 0
symbolTable={}
numTable={}
flag=''
entryNumber=0
dataTypes={'int':4, 'float':8, 'double':16, 'char':1, 'long':8, 'ptr':4, 'bool':1}
addr=1000

g=open("Output.xls","w")


class Token(object):
    
    """ A basic Token class used as a wrapper for tokenzing"""
    
    def __init__(self, type, val, pos, lineno, blockno = 0, blockord = 0):
        self.type = type
        self.val = val
        self.pos = pos
        self.lineno= lineno
        self.blockord = blockord
        self.blockno = blockno        
        
    def __str__(self):
        return '%s(%s) at pos(%s) in line(%s) - blockNumber(%s) blockOrder(%s)' % (self.type, self.val, self.pos,self.lineno,self.blockno,self.blockord)

class LexerError(Exception):
    def __init__(self, pos):
        self.pos = pos

class Lexer(object):
    
    """ A basic regex-based lexer/scanner"""
    
    def __init__(self, rules, skip_whitespace=True):
        """ this initialzes a lexer.

            rules:
                An array of (regex,type) pair rules.

            skip_whitespace:
                If True, whitespace (\s+) will be skipped 
        """
        self.rules = []
        for regex, type in rules:
            self.rules.append((re.compile(regex), type))
        self.skip_whitespace = skip_whitespace
        self.re_ws_skip = re.compile('[^ \t\v\f\r]')
        

    def input(self, buf):
        """ embed the initialized lexer with a buffer as an input
        """
        self.buf = buf
        self.pos = 0
    
    def tableEntry(self,tok):
        global symbolTable
        global numTable
        global dataTypes
        global addr
        global flag
        global entryNumber
        global blkORD
        global blkNO
        if( tok.type =='LBRACE'):
    	        blkNO += 1
    	        blkORD +=1
           
        if( tok.type == "RBRACE"):
            	blkNO -=1

        tok.blockno = blkNO
        tok.blockord = blkORD

        if (tok not in symbolTable.keys()):
            if(tok.type == 'LIBRARY'):
                tok.val == tok.val[tok.val.find('<'):tok.val.find('>')+1]
            if(tok.type == 'FUNCTION'):
                 tok.val = tok.val[:tok.val.find('(')]
            if(tok.type == 'IDENTIFIER' ):
                print(tok)
                try:                
                    symbolTable[tok] = (hex(addr),flag,dataTypes[flag])
                    addr += dataTypes[flag]
                except:pass
                
            if(tok.type=='ARRAY' or tok.type=='PTRARRAY'):
                try:
                    pat='\[(\d+)\]'
                    m=re.findall(pat,tok.val)
                    m=list(map(int,m))
                    m=reduce(lambda x,y:x*y,m)
                    tok.val = tok.val.split('[')[0]
                    symbolTable[tok] = (hex(addr),flag,dataTypes[flag]*m)
                    addr = addr + m*dataTypes[flag]
                except:pass
                
        if(tok not in numTable.keys()):
            if(tok.type=='INTEGER'):
                numTable[tok]=(entryNumber,tok.val,tok.type,'int')
                entryNumber+=1
            elif(tok.type=='FLOAT'):
                numTable[tok]=(entryNumber,tok.val,tok.type,'float')
                entryNumber+=1
            elif(tok.type=='CHAR'):
                numTable[tok]=(entryNumber,ord(tok.val[1:2]),tok.type,'char')
                entryNumber+=1
            elif(tok.type=='LONG'):
                numTable[tok]=(entryNumber,ord(tok.val[1:2]),tok.type,'char')
                entryNumber+=1
            elif(tok.type=='DOUBLE'):
                numTable[tok]=(entryNumber,ord(tok.val[1:2]),tok.type,'char')
                entryNumber+=1

    def token(self):
        """ Returns the next token object in buffer
            Retruns None if reaches the end of the buffer
            Raises LexerError if no re patterns matches
        """
        if self.pos >= len(self.buf):
            return None
        if self.skip_whitespace:
            m = self.re_ws_skip.search(self.buf, self.pos)
            if m:
                self.pos = m.start()
            else:
                return None
        
        global g
        for regex, type in self.rules:
            m = regex.match(self.buf, self.pos)
            global lineCount
           
            if m:
                if(type == 'NEWLINE'):
                    lineCount+=1
                tok = Token(type, m.group(), self.pos,lineCount)
                self.pos = m.end()
                global flag
                if(tok.type == 'DATATYPE'):
                    flag=tok.val
                    if   flag == 'int': tok.type="DATATYPE-INT"
                    elif flag == 'float': tok.type="DATATYPE-FLOAT"
                    elif flag == 'double': tok.type="DATATYPE-DOUBLE"
                    elif flag == 'long': tok.type="DATATYPE-LONG"
                    elif flag == 'bool': tok.type="DATATYPE-BOOL"
                    elif flag == 'char': tok.type="DATATYPE-CHAR"
                    
                if(tok.type == 'PTR'):
                    flag = 'ptr'
                self.tableEntry(tok)
                if(tok.type == 'MLINECOMMENTS'):
                    n = len(tok.val.split('\n'))
                    lineCount += n
                if(tok.type == 'SLINECOMMENT'):
                    lineCount += 1
                if tok.type != 'NEWLINE' and tok.type != 'SLINECOMMENT' and tok.type != 'MLINECOMMENTS':
                    if(tok.type == 'IDENTIFIER'):
                        try:
                            value = (symbolTable[tok][0], int(symbolTable[tok][0], 16))
                        except:
                            value = '--'
                            pass
                    elif(tok.type == 'INTEGER' or tok.type == 'FLOAT'):
                        value = tok.val
                    elif(tok.type == 'CHAR'):
                        value = ord(tok.val[1:2])
                    elif(tok.type == 'ARRAY'or tok.type == 'PTRARRAY'):
                        if(tok.val[tok.val.find('[')+1] != ']'):
                            tok = tok.val.split('[')[0]
                            value = (symbolTable[tok][0], int(symbolTable[tok][0], 16))
                        else:
                            value = '--'
                        if(flag == 'ptr'):
                            tok.type = 'PTRARRAY'
                    else:
                        value='--'
                    print(tok.lineno,"\t\t",tok.val,"\t\t",tok.type,"\t\t\t",tok.blockno,"\t\t",tok.blockord,file=g)
                return tok
        raise LexerError(self.pos)

    def tokens(self):
        """
             Iterating through the tokens in buffer
        """
        while 1:
            tok = self.token()
            if tok is None: break
            yield tok

rules = [
    (r'\n','NEWLINE'),
    ('\#include','PREPROCESSOR'),
    ('\#define','MACRO'),
    ('<(.)*?>','LIBRARY'),
    ('"(.)*?[\.h|\.c]"','HEADER'),
    ('<=','LE'),
    ('>=','GE'),
    ('>','GT'),
    ('!=','NE'),
    ('<<','LSHIFT'),
    ('>>','RSHIFT'),
    ('<','LT'),
    ('\/\/(.)*?\n','SLINECOMMENT'),
    ('\"([^\\\n]|(\\.))*?\"','STRCONST'),
    (r'\d+\.(\d+)','FLOAT'),
    (r'\d+','INTEGER'),
    ('/\*(.|\n)*?\*/','MLINECOMMENTS'),
    (r'\bint(\s)*\*\b','PTR'),
    (r'\bfloat(\s)*\*\b','PTR'),
    (r'\bdouble(\s)*\*\b','PTR'),
    (r'\blong(\s)*\*\b','PTR'),
    (r'\bchar(\s)*\*','PTR'),
    (r'\bbool\b','DATATYPE'),
    (r'\bint\b','DATATYPE'),
    (r'\bfloat\b','DATATYPE'),
    (r'\bdouble\b','DATATYPE'),
    (r'\blong\b','DATATYPE'),
    (r'\bchar\b','DATATYPE'),
    (r'\bmain\b','FUNCTION_MAIN'),
    (r'\bvoid\b','ReservedKey_VOID'),
    (r'\bprintf\b','ReservedKey_PRINT'),
    (r'\bcout\b','ReservedKey_COUT'),
    (r'\bcin\b','ReservedKey_CIN'),
    (r'\busing\b','ReservedKey_USING'),
    (r'\bnamespace\b','ReservedKey_NSPACE'),
    (r'\bstd\b','STD_NAMESPACE'),
    (r'\bvoid\b','ReservedKey_VOID'),
    (r'\bif\b','ReservedKey_IF'),
    (r'\bauto\b','ReservedKey_AUTO'),
    (r'\bbreak\b','ReservedKey_BREAK'),
    (r'\bcase\b','ReservedKey_CASE'),
    (r'\bconst\b','ReservedKey_CONST'),
    (r'\bcontinue\b','ReservedKey_CONT'),
    (r'\bdefault\b','ReservedKey_DEFLT'),
    (r'\bdo\b','ReservedKey_DO'),
    (r'\bdouble\b','ReservedKey_DBL'),
    (r'\belse\b','ReservedKey_ELSE'),
    (r'\benum\b','ReservedKey_ENUM'),
    (r'\bextern\b','ReservedKey_EXTRN'),
    (r'\bfor\b','ReservedKey_FOR'),
    (r'\bgoto\b','ReservedKey_GOTO'),
    (r'\bregister\b','ReservedKey_RGIST'),
    (r'\breturn\b','ReservedKey_RET'),
    (r'\bshort\b','ReservedKey_SHORT'),
    (r'\bsigned\b','ReservedKey_SIGNED'),
    (r'\bsizeof\b','ReservedKey_SIZOF'),
    (r'\bstatic\b','ReservedKey_STATIC'),
    (r'\bstruct\b','ReservedKey_STRUCT'),
    (r'\bswitch\b','ReservedKey_SWITCH'),
    (r'\btypedef\b','ReservedKey_TYPDEF'),
    (r'\bunion\b','ReservedKey_UNION'),
    (r'\bvoid\b','ReservedKey_VOID'),
    (r'\bvolatile\b','ReservedKey_VOLATILE'),
    (r'\bwhile\b','ReservedKey_WHILE'),
    (r'\btrue\b','ReservedKey_TRUE'),
    (r'\bfalse\b','ReservedKey_FALSE'),
    (r'\bpublic\b','ReservedKey_PUBL'),
    (r'\bprivate\b','ReservedKey_PRIV'),
    (r'\bprotected\b','ReservedKey_PRTCT'),
    ('->','ARROW'),
    ('\?','CONDOP'),
    ('[a-zA-Z_]\w*\(', 'FUNCTION'),
    ('[a-zA-Z_]\w*\*(\[(.)*?\])+',    'PTRARRAY'),
    ('[a-zA-Z_]\w*(\[(.)*?\])+',    'ARRAY'),
    ('[a-zA-Z_]\w*',    'IDENTIFIER'),
    ('\+=','PLUSEQUALS'),
    ('-=','MINUSQUALS'),
    ('\*=','TIMESEQUALS'),
    ('\/=','DIVIDEEQUALS'),
    ('%=','MODEQUALS'),
    ('<<=','LSHIFTEQUALS'),
    ('>>=','RSHIFTEQUALS'),
    ('&=','ANDEQUALS'),
    ('\|=','OREQUALS'),
    ('^=','XOREQUALS'),
    ('\+\+','POSTINCREMENT'),
    ('\-\-','POSTDECREMENT'),
    ('\+','PLUS'),
    ('\-','MINUS'),
    ('\*','MULTIPLY'),
    ('\/','DIVIDE'),
    ('\(','LPAREN'),
    ('\)',  'RPAREN'),
    ('==','EQ'),
    ('=', 'EQUALS'),
    ('%',   'MOD'),
    ('\[','LBRACKET'),
    ('\]','RBRACKET'),
    ('\{','LBRACE'),
    ('\}','RBRACE'),
    (',','COMMA'),
    ('\.','PERIOD'),
    (';','SEMICOLON'),
    (':','COLON'),
    ('\|' ,'OR'),
    ('&','AND'),
    ('~','NOT'),
    ('\^','XOR'),
    ('\|\|','SHTCKTOR'),
    ('&&','SHTCKTAND'),
    ('!','LNOT'),
    (r'(L)?\'([^\\\n]|(\\.))*?\'','CHAR')
]



lx = Lexer(rules, skip_whitespace=True)
f=open('test.c')
inp=f.read()
f.close()
lx.input(inp)
staticTable=[]
try:
    print("\nOutput Table\nLine NO\t\t","Lexeme\t\t","Token\t\t\t","blockNumber\t\t","blockOrder",file=g)
    for tok in lx.tokens():
        if tok == '' or tok == ' ':continue
        if tok.type == 'MLINECOMMENTS' or tok.type == 'SLINECOMMENT':
            staticTable.append((tok.val,tok.type,tok.lineno,tok.pos,tok.blockno,tok.blockord))
except LexerError as err:
    print('LexerError at position %s' % err.pos)
    
    

    

ListsymbolTable=sorted(symbolTable.items(), key = lambda item:item[1][0])
ListnumTable = sorted(numTable.items(), key = lambda item:item[1][0])




print("\nSymbolTable\n",file=g)
print("Token\t\t\t\t\t\t\t","Symbol","\t\tType\t","\tSize",file=g)
for i in ListsymbolTable:
    print(i[0],"\t\t\t\t\t\t\t",i[0].val,"\t\t",i[1][1],"\t\t",i[1][2],file=g)
        

print("\nNumTable\n",file=g)
print("Number\t\t\t\t\t\t","\tToken","\t\tType\t","\tValue\t",file=g)
for i in ListnumTable:
    print(i[0],"\t\t\t\t\t\t\t",i[1][2],"\t\t",i[1][3],"\t\t",i[1][1],file=g)

    
print("\nCommentTable\n",file=g)
print("Token\t\t\t\t","Type\t\t","line\t\t","position\t\t","blockNumber\t\t","blockOrder",file=g)
for (tokVal,tokType,tokLine,tokPOS,tokBlkNO,tokBlkORD) in staticTable:
    print(tokVal,"\t\t\t\t",tokType,"\t\t",tokLine,"\t\t",tokPOS,"\t\t",tokBlkNO,"\t\t",tokBlkORD,file=g)



g.close()

###########################
