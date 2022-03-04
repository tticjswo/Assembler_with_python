def make_line_list(filename):   #input file을 한 줄 씩 읽고 저장하는 함수
    fp = open(filename , 'r')
    lines = fp.readlines()
    global start_addr
    for line in lines :         # .으로 시작하는 모든 line 제거 
        if line.startswith(".") :
            lines.remove(line)
    for line in lines :         # .으로 시작하는 모든 line 제거 
        if line.startswith(".") :
            lines.remove(line)
    for line in lines :
        tmp_line_list = line.split('\t')
        if "START" in tmp_line_list[1] :
            start_addr = int(tmp_line_list[2],16)

    return lines

class InstTable: 
    def __init__(self):
        self.instDic = {} #dictionary { inst name : line }
        
    def openFile(self, fileName):   ### inst.data file 오픈하여 파싱.
        f = open(fileName,'r')
        instructions = f.readlines()
        for line in instructions:
            instruction = line.split(' ') #' '을 기준으로 파싱
            self.instDic[instruction[0]] = instruction

    def get_format(self,op): #파라미터의 형식을 정수로 반환
        if op[0]=='+':
            op = op[1:] 
            return 4
        if self.instDic.get(op)==None :
            return -1
        elif "3/4" in self.instDic[op][1]: 
            return 3
        elif "2" in self.instDic[op][1]: 
            return 2

    def get_opcode(self,label):  #label을 기준으로 opcode 반환
        if '+' in label:
            label = label[1:]
        if self.instDic.get(label) == None:
            return -1
        else: 
            return int(self.instDic[label][2],16) #op_code를 16진수 정수로 변환하여 반환
    
class SymbolTable: #딕셔너리 구조로 symbolTable 구성
    def __init__(self):
        self.symbolDic = {}
    
    def putSymbol(self,symbol,location): # symbol table에 주어진 symbol 을 삽입
        if(self.search(symbol)<0): #이미 symbol table에 있을시
            self.symbolDic[symbol] = location #딕셔너리 key : symbol , value : location
            
    def search(self,symbol):    #symbolTable 검색
        if(self.symbolDic.get(symbol)==None):
            return -1
        else:
            return self.symbolDic[symbol] 
    
    def size(self):
        return len(self.symbolDic)


class LiteralTable: #딕셔너리 구조로 LiteralTable 구성
    def __init__(self):
        self.litDic = {}
        
    def putLiteral(self,literal,location): # literal table 삽입
            self.litDic[literal] = location # 딕셔너리 key : literal , value : location
    
            
    def search(self,literal):   #literal table 검색
        if(self.litDic.get(literal)==None):
            return -1
        else:
            return self.litDic[literal]
    
    def size(self):
        return len(self.litDic)

class ExtTable: #두개의 리스트 구조로 ExtTable 구성
    def __init__(self):
        self.extdef = []    #각각 define 리스트, reference 리스트로 구성
        self.extref = []
        
    def addD(self,symList): #extdef 리스트에 삽입
        self.extdef = symList
    
    def addR(self,symList): #extref리스트에 삽입
        self.extref = symList
        
    def searchD(self,symbol): #extdef에서 탐색
        for s in self.extdef:
            if(s == symbol):
                return self.extdef.index(s)
        return -1
    
    def searchR(self,symbol): #extref에서 탐색
        for s in self.extref:
            if(s == symbol):
                return self.extref.index(s)
        return -1       

class Token : 
    def __init__(self,tokens) : 
        # { label, operator, operand[], comment, locctr, byteSize, Objectcode, nixbpe }
        self.label = tokens[0]
        self.operator = tokens[1].rstrip('\n')
        if len(tokens)>2  :
            self.operand= tokens[2].rstrip('\n').split(',')  
        else :
            self.operand = None
        if len(tokens)>3 :
            self.commenet = tokens[3]
        else : 
            self.comment = None
        
        self.locctr = 0
        self.byteSize = 0
        self.Objectcode = ""
        self.nixbpe=[0,0,0,0,0,0]   
        

class TokenTable:
    global start_addr
    def __init__(self,symtab,littab,insttab): #필요 테이블 링크
        self.symTab = symtab
        self.literalTab = littab
        self.instTab = insttab
        self.extTab = ExtTable()
        self.locctr = start_addr
        self.size = 0
        self.modiLIst = [] 
        self.tokenList = []
        self.ltorg_flag = False
        self.name = ""
        self.modificationList = []

    def putToken(self,line): # 일반 문자열을 받아서 Token단위로 분리시켜 tokenList에 추가한다. 
        newToken = Token(line.split('\t'))
        newToken.location = self.locctr
        if "START" in newToken.operator:
            self.symTab.putSymbol(newToken.label,start_addr) #symbolTable에 프로그램 이름 저장
            self.name = newToken.label
            return 1
        elif "CSECT" in newToken.operator: #control section 분리
            if not self.ltorg_flag: #LTORG 호출 없을때
                #LTORG 가 없을 때 literal 이 나오게 되면 CSECT 의 operand 부분에 literal 을 임의로 넣음으로써 literal의 loccation을 조정한다.
                for lit in self.literalTab.litDic.keys():
                    self.literalTab.putLiteral(lit,self.locctr)
                    if lit[1] =='C' :
                        self.locctr += (len(lit)-4) # ex) =C'EOF' 에서 '=','C',' ' ', ' ' ' 총 4개 삭제
                        newToken.byteSize = len(lit)-4
                    elif lit[1] =='X' :
                        self.locctr += int((len(lit)-4)/2)
                        newToken.byteSize = int((len(lit)-4)/2)
                    newToken.operand = [lit]   
                self.ltorg_flag = True
            self.size = self.locctr
            self.tokenList.append(newToken)
            return -1 #음수 리턴
        elif("END" in newToken.operator): #프로그램 종료
            if not self.ltorg_flag: #LTORG 호출 없을 때
                #LTORG 가 없을 때 literal 이 나오게 되면 END 의 operand 부분에 literal 을 임의로 넣음으로써 literal의 loccation을 조정한다.
                for lit in self.literalTab.litDic.keys():
                    self.literalTab.putLiteral(lit,self.locctr)
                    if lit[1] =='C' :
                        self.locctr += len(lit)-4 
                        newToken.byteSize = len(lit)-4
                    elif lit[1] =='X' :
                        self.locctr += int((len(lit)-4)/2)  # ex) =X'05' 에서 '=','X',' ' ', ' ' ' 총 4개 삭제 후 16진수 두글자당 한 바이트기 때문에 /2 
                        newToken.byteSize = int((len(lit)-4)/2)
                    newToken.operand = [lit]
                self.ltorg_flag = True
            self.size = self.locctr
            self.tokenList.append(newToken)
            return 0
        elif "EXTDEF" in newToken.operator: #ExtTable.extdef에 저장
            self.extTab.addD(newToken.operand)
            return 1
        elif "EXTREF" in newToken.operator: #ExtTable.extref에 저장
            self.extTab.addR(newToken.operand)
            return 1
        elif "LTORG" in newToken.operator: #literalTable에 주소 갱신
            if not self.ltorg_flag:
                for lit in self.literalTab.litDic.keys():
                    self.literalTab.putLiteral(lit,self.locctr)
                    self.locctr += len(lit)-4
                    newToken.operand = [lit]
                    newToken.byteSize = len(lit)-4
                self.ltorg_flag = True
            self.tokenList.append(newToken)
            return 1           

        if(newToken.label!=""): #lable을 알맞은 주소로 symbolTable에 저장
            if("EQU" in newToken.operator):
                if "*" in newToken.operand[0]:
                    self.symTab.putSymbol(newToken.label,self.locctr)
                    newToken.location = start_addr
                    newToken.byteSize = 0
                elif(not newToken.operand[0].isdigit()):
                    addr =0
                    # '-' 일때 minus '+'일 때 plus, 일반 적인 주소연산에서 +,- 를 제외하고 쓰이지 않는다고 가정한다.
                    if "-" in newToken.operand[0] :
                        newToken.operand = newToken.operand[0].split('-')
                        addr = self.symTab.search(newToken.operand[0])-self.symTab.search(newToken.operand[1])
                    elif "+" in newToken.operand[0] :
                        newToken.operand = newToken.operand[0].split('+')
                        addr = self.symtTab.search(newToken.operand[0])+self.symTab.search(newToken.operand[1])
                    self.symTab.putSymbol(newToken.label,addr)
                    newToken.location = start_addr
                    newToken.byteSize=0
            else:
                self.symTab.putSymbol(newToken.label,self.locctr)
        
        if(newToken.operand != None):
            if("=" in newToken.operand[0]): #operand 에 literal 사용할 때
                self.literalTab.putLiteral(newToken.operand[0],0)          
        
        if(self.instTab.get_opcode(newToken.operator)<0):   #instTable 에 해당 operator 가 없다면
            if "RESB" in newToken.operator:
                newToken.byteSize = int(newToken.operand[0])
                self.locctr += newToken.byteSize
            elif "RESW" in newToken.operator:
                newToken.byteSize = int(newToken.operand[0])*3
                self.locctr += newToken.byteSize
            elif "BYTE" in newToken.operator:
                newToken.byteSize = 1
                self.locctr += 1
            elif "WORD" in newToken.operator:
                newToken.byteSize = 3
                self.locctr += 3
                if "-" in newToken.operand[0] :
                    newToken.operand = newToken.operand[0].split('-')
                    addr = self.symTab.search(newToken.operand[0])-self.symTab.search(newToken.operand[1])
                elif "+" in newToken.operand[0] :
                    newToken.operand = newToken.operand[0].split('+')    
                    addr = self.symTab.search(newToken.operand[0])+self.symTab.search(newToken.operand[1])
        else:
            a = self.instTab.get_format(newToken.operator)  #format 값만큼 bytesize 저장
            newToken.byteSize = a
            self.locctr += a

        self.tokenList.append(newToken)
        return 1


    def makeObjectCode(self,index): 
        token = self.tokenList[index]
        opcode = self.instTab.get_opcode(token.operator)
        addflag = 0
        #program countrer 은 다음 명령어의 주소를 가리킨다.
        if index == len(self.tokenList)-1: 
            pc = self.tokenList[index].location + token.byteSize
        else:
            pc = self.tokenList[index+1].location
        addr = 0
        token.nixbpe[0] = True
        token.nixbpe[1] = True
        
        if token.byteSize == 2: #2형식
            r = []
            for i in range(len(token.operand)): #레지스터 번호 저장
                if "A" in token.operand[i]:
                    r.append(0)
                elif "X" in token.operand[i]:
                    r.append(1)
                elif "S" in token.operand[i]:
                    r.append(4)
                elif "T" in token.operand[i]:
                    r.append(5)
            if len(r) == 1:
                r.append(0)
            
            token.Objectcode = "%X%X%X"%(opcode,r[0],r[1])
            self.tokenList[index] = token
            return
        str = token.operand[0]

        if opcode < 0: #operator 가 insttable 에 없을 때
            if "WORD" in token.operator or "BYTE" in token.operator:
                if self.extTab.searchR(str)<0: # ex) X'F1'
                    str = str[2:-1]
                else:
                    str = "000000"
                    self.modificationList.append("%06X06+%s\n"%(token.location,token.operand[0]))
                    self.modificationList.append("%06X06-%s\n"%(token.location,token.operand[1]))
                token.Objectcode = str
            elif "=" in str: #리터럴 ex) =C'EOF'
                if "C" in str:
                    str = str[3:-1]
                    token.Objectcode = "%X%X%X"%(ord(str[0]),ord(str[1]),ord(str[2]))
                elif "X" in str:
                    str = str[3:-1]
                    token.Objectcode = str
        else: # operator 가 instTable에 정의 되어 있음
            if "+" in token.operator: #4형식
                token.nixbpe[-1] = True
            if not token.operand[0]: #operand 가 없는 operator
                addr = 0
            elif self.symTab.search(token.operand[0])>=0: #symbol 피연산자
                addr = self.symTab.search(token.operand[0])
                addr -=pc
                token.nixbpe[4] = True
            elif self.extTab.searchR(token.operand[0])>=0: #외부에 정의된 피연산자
                self.modificationList.append("%06X05+%s\n"%(token.location+1,token.operand[0])) #M record에 저장
                addr = 0
            elif self.literalTab.search(token.operand[0])>=0: #literal 피연산자
                addr = self.literalTab.search(token.operand[0])
                addr -=pc
                token.nixbpe[4] = True
            elif "#" in token.operand[0]: #immediate addressing
                token.nixbpe[0] = False
                addr = int(str[1:])
            elif "@" in token.operand[0]: #indirect addressing
                token.nixbpe[1] = False
                addr = self.symTab.search((token.operand[0])[1:])
                addr -=pc
                token.nixbpe[4] = True
            if token.operand and len(token.operand)>1 and "X" in token.operand[1]: #indexing loop 사용
                token.nixbpe[2] = True
            
            #nixbpe비트 설정에 따른 값 저장
            if token.nixbpe[0]: 
                opcode += 2
            if token.nixbpe[1]: 
                opcode += 1

            if token.nixbpe[2]: 
                addflag += 8
            if token.nixbpe[3]: 
                addflag += 4
            if token.nixbpe[4]: 
                addflag += 2
            if token.nixbpe[5]: 
                addflag += 1
        
            if addr<0: #pc relative 계산 시 음수일 경우 보수 처리
                str = hex((addr + (1 << 12)) % (1 << 12))
                addr = str[2:]
            else:
                addr = hex(addr)
                addr = addr[2:]
                
            if token.nixbpe[5]: #4형식 objectcode
                token.Objectcode = "%02X%X%s"%(opcode,addflag,addr.zfill(5).upper()) #4형식 objectcode 저장
            else: #3형식 objectcode
                token.Objectcode = "%02X%X%s"%(opcode,addflag,addr.zfill(3).upper()) #3형식 objectcode 저장
        self.tokenList[index] = token

def pass1(symboltabList,literalList,tokentabList,instTable,lineList):
    tokenTab = TokenTable(symboltabList[0],literalList[0],instTable)
    sec_n = 0
    global start_addr
    for line in lineList: #input의 한 줄씩 토큰 분석 진행
        if(tokenTab.putToken(line)<0): #control section이 분리될때 -1 반환
            tokentabList.append(tokenTab)
            symboltabList.append(SymbolTable())
            literalList.append(LiteralTable())
            sec_n +=1
            new = Token(line.split('\t'))
            symboltabList[sec_n].putSymbol(new.label,start_addr) #새로운 control section의 이름 저장
            tokenTab = TokenTable(symboltabList[sec_n],literalList[sec_n],instTable)
            tokenTab.name = new.label #새로운 control section의 이름 저장
    tokentabList.append(tokenTab)        

def pass2(tokentabList,instTable):
    sec_n = 0
    codeList = []
    global start_addr
    for tokentab in tokentabList:
        current_addr = start_addr
        length = 0
        str = ""
        codeList.append("H%-6s%06X%06X\n"%(tokentab.name,start_addr,tokentab.size)) # 'H'
        if tokentab.extTab.extdef: # 'D'
            codeList.append("D")
            for symbol in tokentab.extTab.extdef:
                codeList.append("%-6s%06X"%(symbol,tokentab.symTab.search(symbol)))
            codeList.append("\n")
        if(tokentab.extTab.extref != None): # 'R'
            codeList.append("R")
            for symbol in tokentab.extTab.extref:
                codeList.append("%-06s"%(symbol))
            codeList.append("\n")
        i=0
        while i <len(tokentab.tokenList): # 'T'
            if tokentab.tokenList[i].byteSize != 0: #메모리 크기를 필요로 하는 명령어만 objectcode 생성
                tokentab.makeObjectCode(i)
            if not tokentab.tokenList[i].Objectcode:    #다음 명령어의 objectcode 가 없어지만 지금까지의 str을 codeList에 저장
                codeList.append("T%06X%02X%s\n"%(current_addr,length,str)) 
                str = ""
                length = 0
                while i<len(tokentab.tokenList) and not tokentab.tokenList[i].Objectcode:
                    if tokentab.tokenList[i].byteSize !=0:
                        tokentab.makeObjectCode(i)
                        if tokentab.tokenList[i].Objectcode:
                            break
                    i += 1
                if i<len(tokentab.tokenList):
                    current_addr = tokentab.tokenList[i].location
                i -= 1
            elif length+tokentab.tokenList[i].byteSize >= 32: # 한 줄당 용량 : 32
                codeList.append("T%06X%02X%s\n"%(current_addr,length,str))  # 한 줄에 들어갈 수 있는 용량이 꽉 차면 지금까지의 만들어진 str 을 포멧에 맞추어 codeList에 추가
                current_addr += length
                str = ""
                length = 0
                i -=1
            else:
                str += tokentab.tokenList[i].Objectcode
                length += tokentab.tokenList[i].byteSize
            i+=1
        if str:
            codeList.append("T%06X%02X%s\n"%(current_addr,length,str))
        
        if tokentab.modificationList: # 'M'
            for record in tokentab.modificationList:
                codeList.append("M%s"%(record))
        
        if sec_n == 0: # 'E'
            codeList.append("E000000\n")
        else:
            codeList.append("E\n")
        codeList.append("\n")
        
        sec_n +=1
    return codeList

if __name__ == '__main__' :
    instTable = InstTable()
    instTable.openFile("inst.data")
    lineList = make_line_list("input.txt")

    symboltabList = [SymbolTable()]
    literaltabList = [LiteralTable()]
    tokentabList = []
    pass1(symboltabList,literaltabList,tokentabList,instTable,lineList)

    f = open("symtab_20162449.txt",'w')
    for symtab in symboltabList:
        for key,value in symtab.symbolDic.items():
            f.write("%s\t%X\n"%(key,value))
        f.write("\n")
    f.close()

    f = open("literaltab_20162449.txt",'w')
    for littab in literaltabList:
        for key,value in littab.litDic.items():
            f.write("%s\t%X\n"%(key,value))
    f.close()
    """pass2"""
    codeList = pass2(tokentabList,instTable)

    """objectcode가 저장된 codeList내용 파일에 저장"""
    f = open("output_20162449.txt",'w')
    for line in codeList:
        f.write(line)
    f.close()

