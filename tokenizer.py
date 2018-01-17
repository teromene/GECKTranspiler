"""
Few things to change here: var are not in their contex, meaning that some vars might not be differenciated from funcalls
Also, comments in setblocks ?
"""
import string
class Token :

	TOKEN_SCRIPTNAME = "TOKEN_SCRIPTNAME"
	TOKEN_COMMENT = "TOKEN_COMMENT"
	TOKEN_BEGINBLOCK = "TOKEN_BEGINBLOCK"
	TOKEN_ENDBLOCK = "TOKEN_ENDBLOCK"
	TOKEN_STATEMENTSTART = "TOKEN_STATEMENTSTART"
	TOKEN_STATEMENTEND = "TOKEN_STATEMENTEND"
	TOKEN_VARINT = "TOKEN_VARINT"
	TOKEN_VARREF = "TOKEN_VARREF"
	TOKEN_VAR = "TOKEN_VAR"
	TOKEN_IFSTART = "TOKEN_IFSTART"
	TOKEN_IFEND = "TOKEN_IFEND"
	TOKEN_IFCONDSTART = "TOKEN_IFCONDSTART"
	TOKEN_IFCONDEND = "TOKEN_IFCONDEND"
	TOKEN_ELSE = "TOKEN_ELSE"
	TOKEN_ELSEIF = "TOKEN_ELSEIF"
	TOKEN_RELOP = "TOKEN_RELOP"
	TOKEN_LOGICOP = "TOKEN_LOGICOP"	
	TOKEN_NUMOP = "TOKEN_NUMOP"
	TOKEN_MATHOP =  "TOKEN_MATHOP"
	TOKEN_FUNCALL = "TOKEN_FUNCALL"
	TOKEN_FUNPARAMLISTSTART = "TOKEN_FUNPARAMLISTSTART"
	TOKEN_FUNPARAMLISTEND = "TOKEN_FUNPARAMLISTEND"
	TOKEN_FUNPARAMSTART = "TOKEN_FUNPARAMSTART"
	TOKEN_FUNPARAMEND = "TOKEN_FUNPARAMEND"
	TOKEN_BRACKETSTART = "TOKEN_BRACKETSTART"
	TOKEN_BRACKETEND = "TOKEN_BRACKETEND"
	TOKEN_SETCALLSTART = "TOKEN_SETCALLSTART"
	TOKEN_SETCALLEND = "TOKEN_SETCALLEND"
	TOKEN_SETCALLVAR = "TOKEN_SETCALLVAR"
	TOKEN_SETCALLVALSTART = "TOKEN_SETCALLVALSTART"
	TOKEN_SETCALLVALEND = "TOKEN_SETCALLVALEND"

	def __init__(self, tokenType, val1 = None, val2 = None, valArr = []):
		self.tokenType = tokenType
		self.val1 = val1
		self.val2 = val2
		self.valArr = valArr

	def __repr__(self) :
		return self.tokenType + " " + (self.val1 if self.val1 != None else "") + " " + (self.val2 if self.val2 != None else "") + "\n"

class Tokenizer:

	tokens = []
	variableList = []

	def __init__(self, sourcefile, useListFile):
		self.sourcefile = sourcefile
		self.useListFile = useListFile
		if useListFile:
			with open("rewriter/GECKFunctionList", "r") as functionList:
				self.functionList = functionList.readlines()
			self.functionList = [line.strip() for line in self.functionList]

	def run(self) :
		if self.sourcefile == None:
			return

		scriptTitle = self.sourcefile.read(3)
		assert(scriptTitle.startswith("scn"))
		self.tokens.append(Token(Token.TOKEN_SCRIPTNAME, self.readNoWhiteUntil()))

		oldpos = -1
		while self.sourcefile.tell() != oldpos:
			oldpos = self.sourcefile.tell()
			self.fastForward()
			self.parseLine()

		#We finished tokenizing the source. Now, we check that some ambiguous call/vars haven't been clarified later on
		self.rewroteCount = 0
		for pos in range(0, len(self.tokens)):
			if pos >= len(self.tokens):
				return

			token = self.tokens[pos]
			if token.tokenType == Token.TOKEN_FUNCALL and ((token.val2 == None and token.val1 in self.variableList) or (token.val1 + "." + str(token.val2)) in self.variableList):
				self.rewroteCount += 1
				token.tokenType = Token.TOKEN_VAR
				self.tokens.pop(pos + 1)
				self.tokens.pop(pos + 1)

		if self.useListFile:
			#Use the GECK function list to remove some ambiguity.
			for pos in range(0, len(self.tokens)):
				if pos >= len(self.tokens):
					return

				token = self.tokens[pos]

				if token.tokenType == Token.TOKEN_FUNCALL and ( not (token.val2 != None and token.val2.lower() in self.functionList) and token.val1.lower() not in self.functionList):
					if self.tokens[pos + 2].tokenType == Token.TOKEN_FUNPARAMLISTEND:
						self.rewroteCount += 1
						token.tokenType = Token.TOKEN_VAR
						self.tokens.pop(pos + 1)
						self.tokens.pop(pos + 1)
			
	def parseLine(self):
		if self.readNoEat(1) == ";" :
			self.parseComment()
		elif self.readNoEat(5) == "begin" :
			self.parseBeginBlock()
		elif self.readNoEat(5) == "short" or self.readNoEat(3) == "int" or self.readNoEat(4) == "long":
			self.parseVarDeclInt()
		elif self.readNoEat(3) == "ref":
			self.parseVarDeclRef()
		elif self.readNoEat(2) == "if":
			self.parseIfBlock()
		elif self.readNoEat(6) == "elseif":
			self.parseElseIfBlock()
		elif self.readNoEat(4) == "else":
			self.parseElseBlock()
		elif self.readNoEat(5) == "endif":
			self.parseEndIfBlock()
		elif self.readNoEat(3) == "end":
			self.parseEndBlock()
		else :
			self.parseStatementLine()

	def gotoNextToken(self):
		start = self.readNoWhiteUntil(sep=["\n"], override=[], limit = 1)
		out = ""
		if start == "\n" or start == "":
			return "\n", False
		if start in string.ascii_letters:
			readchar = start
			while readchar in (string.ascii_letters + string.digits + (".")):
				out += readchar
				readchar = self.sourcefile.read(1)
			self.rewind(1)
		elif start in (string.digits + (".") + ("-")):
			readchar = start
			while readchar in (string.digits + (".") + ("-")):
				out += readchar
				readchar = self.sourcefile.read(1)
			self.rewind(1)
		elif start in ["=", "!", ">"]:
			out = start
			if self.readNoEat(1) == "=":
				out += self.sourcefile.read(1)
		elif start in ["|", "&"]:
			out = start + self.sourcefile.read(1)
		elif start in ["/", "*", "+", "(", ")", ",", " "]:
			out = start
		elif start in ["\"", "\'"]:
			readchar = ""
			while readchar != start:
				out += readchar
				readchar = self.sourcefile.read(1)
			out = start + out + start
		elif start == ";":
			readchar = start
			while readchar != "\n":
				out += readchar
				readchar = self.sourcefile.read(1)
			self.rewind(1)
		return out, True
	def parseStatementLine(self, inIf = False):

		continueLineParse = True
		contextFunctionCall = False
		contextFunParam = False
		contextSetCall = 0
		firstParam = False

		if not inIf :
			self.tokens.append(Token(Token.TOKEN_STATEMENTSTART))	

		while continueLineParse:

			if not firstParam:
				token, continueLineParse = self.gotoNextToken()
			else:
				firstParam =  not firstParam

			if token == "":
				continue

			if token.startswith("Set") or token.startswith("set"):
				self.tokens.append(Token(Token.TOKEN_SETCALLSTART))
				contextSetCall = 1
			elif token.startswith("to") or token.startswith("To"):
				contextSetCall = 2
				self.tokens.append(Token(Token.TOKEN_SETCALLVALSTART))
			elif token == "(":
				self.tokens.append(Token(Token.TOKEN_BRACKETSTART))
			elif token == ")":
				self.tokens.append(Token(Token.TOKEN_BRACKETEND))
			elif token in ["==", "!=", ">", "<", ">=", "<="]:
				if self.tokens[-1].tokenType == Token.TOKEN_FUNPARAMSTART:
					self.tokens.pop(-1)
					self.tokens.append(Token(Token.TOKEN_FUNPARAMLISTEND))
				contextFunctionCall = False
				self.tokens.append(Token(Token.TOKEN_RELOP, token))
			elif token in ["||", "&&"]:
				if contextFunctionCall:
					self.tokens.append(Token(Token.TOKEN_FUNPARAMEND))
				contextFunctionCall = False
				self.tokens.append(Token(Token.TOKEN_LOGICOP, token))
				
			elif token[0] in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ".", "-"]:
				self.tokens.append(Token(Token.TOKEN_NUMOP, token))
			elif token in ["+", "-", "*", "/", "%"]:
				if self.tokens[-1].tokenType == Token.TOKEN_FUNPARAMSTART:
					self.tokens.pop(-1)
					self.tokens.append(Token(Token.TOKEN_FUNPARAMLISTEND))
					contextFunctionCall = False
				self.tokens.append(Token(Token.TOKEN_MATHOP, token))
			elif token == "," or (token == " " and contextFunctionCall and self.tokens[-1].tokenType == Token.TOKEN_VAR):

				if contextFunctionCall:
					self.tokens.append(Token(Token.TOKEN_FUNPARAMEND))
					self.tokens.append(Token(Token.TOKEN_FUNPARAMSTART))
			elif token == " ":
				continue
			elif token == "\n":
				if contextFunctionCall:
					if self.tokens[-1].tokenType == Token.TOKEN_FUNPARAMSTART:
						self.tokens.pop(-1)
					else:
						self.tokens.append(Token(Token.TOKEN_FUNPARAMEND))
					self.tokens.append(Token(Token.TOKEN_FUNPARAMLISTEND))
			elif token[0] == ";":
				if contextFunctionCall:
					if self.tokens[-1].tokenType == Token.TOKEN_FUNPARAMSTART:
						self.tokens.pop(-1)
					else:
						self.tokens.append(Token(Token.TOKEN_FUNPARAMEND))
					self.tokens.append(Token(Token.TOKEN_FUNPARAMLISTEND))
					contextFunctionCall = False
				self.tokens.append(Token(Token.TOKEN_COMMENT, token[1:]))
			else:
				if not contextFunctionCall:
					if token in self.variableList:
						self.tokens.append(Token(Token.TOKEN_VAR, token))
					else:
						if "." in token:
							#Never seen a more-than-one dotted funcall/varcall
							target = token.split(".")[0]
							function = token.split(".")[1]
							if contextSetCall != 1:
								self.tokens.append(Token(Token.TOKEN_FUNCALL, target, function))
								self.tokens.append(Token(Token.TOKEN_FUNPARAMLISTSTART))
								self.tokens.append(Token(Token.TOKEN_FUNPARAMSTART))
								contextFunParam = True
								contextFunctionCall = True
							else:
								if token not in self.variableList:
									self.variableList.append(token)
								self.tokens.append(Token(Token.TOKEN_SETCALLVAR, target, function))
						else:
							if contextSetCall != 1:
								self.tokens.append(Token(Token.TOKEN_FUNCALL, token))
								self.tokens.append(Token(Token.TOKEN_FUNPARAMLISTSTART))
								self.tokens.append(Token(Token.TOKEN_FUNPARAMSTART))
								contextFunParam = True
								contextFunctionCall = True
							else:
								if token not in self.variableList:
									self.variableList.append(token)
								self.tokens.append(Token(Token.TOKEN_SETCALLVAR, token))

				else:
					self.tokens.append(Token(Token.TOKEN_VAR, token))
					if token not in self.variableList:
						self.variableList.append(token)

		if contextSetCall == 2:
			self.tokens.append(Token(Token.TOKEN_SETCALLVALEND))

		if not inIf :
			self.tokens.append(Token(Token.TOKEN_STATEMENTEND))	

	def parseIfBlock(self):
		assert(self.sourcefile.read(2) == "if")
		self.tokens.append(Token(Token.TOKEN_IFSTART))
		self.tokens.append(Token(Token.TOKEN_IFCONDSTART))
		self.parseStatementLine(True)
		self.tokens.append(Token(Token.TOKEN_IFCONDEND))

	def parseElseBlock(self):
		assert(self.sourcefile.read(4) == "else")
		self.tokens.append(Token(Token.TOKEN_ELSE))

	def parseElseIfBlock(self):
		assert(self.sourcefile.read(6) == "elseif")
		self.tokens.append(Token(Token.TOKEN_ELSEIF))
		self.tokens.append(Token(Token.TOKEN_IFCONDSTART))
		self.parseStatementLine(True)
		self.tokens.append(Token(Token.TOKEN_IFCONDEND))

	def parseEndIfBlock(self):
		assert(self.sourcefile.read(5) == "endif")
		self.tokens.append(Token(Token.TOKEN_IFEND))

	def parseBeginBlock(self):
		assert(self.sourcefile.read(5) == "begin")
		blockType = self.readNoWhiteUntil()
		self.tokens.append(Token(Token.TOKEN_BEGINBLOCK, blockType))

	def parseEndBlock(self):
		assert(self.sourcefile.read(3) == "end")
		self.tokens.append(Token(Token.TOKEN_ENDBLOCK))

	def parseVarDeclInt(self):
		self.readNoWhiteUntil(sep=[" "])
		self.lineFastForward()
		varName = self.readNoWhiteUntil(sep=["\n", ";"])
		self.tokens.append(Token(Token.TOKEN_STATEMENTSTART))	
		self.tokens.append(Token(Token.TOKEN_VARINT, varName))
		self.variableList.append(varName)
		self.parseStatementLine(True)
		self.tokens.append(Token(Token.TOKEN_STATEMENTEND))

	def parseVarDeclRef(self):
		self.readNoWhiteUntil(sep=[" "])
		self.lineFastForward()
		varName = self.readNoWhiteUntil(sep=["\n", ";"])
		self.tokens.append(Token(Token.TOKEN_STATEMENTSTART))
		self.tokens.append(Token(Token.TOKEN_VARREF, varName))
		self.variableList.append(varName)
		self.parseStatementLine(True)
		self.tokens.append(Token(Token.TOKEN_STATEMENTEND))

	def parseComment(self):
		assert(self.sourcefile.read(1) == ";")
		self.tokens.append(Token(Token.TOKEN_STATEMENTSTART))
		commentValue = self.readNoWhiteUntil(override=[])
		self.tokens.append(Token(Token.TOKEN_COMMENT, commentValue))
		self.tokens.append(Token(Token.TOKEN_STATEMENTEND))
			
	def readNoEat(self, size):
		pos = self.sourcefile.tell()
		val = self.sourcefile.read(size)
		self.sourcefile.seek(pos)
		return val

	def rewind(self, count):
		self.sourcefile.seek(self.sourcefile.tell() - count)

	def fastForward(self):
		while True:
			readChar = self.sourcefile.read(1)
			if readChar not in [" ", "\t", "\n"] :
				break
		self.sourcefile.seek(self.sourcefile.tell() - 1, 0)

	def lineFastForward(self):
		count = 0
		while True:
			readChar = self.sourcefile.read(1)

			if ord(readChar) == 10:
				break
			elif readChar not in [" ", "\t", ","] :
				break

			count += 1
		self.sourcefile.seek(self.sourcefile.tell() - 1, 0)
		return count

	def readNoWhiteUntil(self, sep = ["\n"], override = None, limit = None):
		outstring = ""
		inStr = False

		while True:
			readChar = self.sourcefile.read(1)
			if readChar in sep and not inStr:
				self.sourcefile.seek(self.sourcefile.tell() - 1, 0)
				return outstring

			if readChar == "\"":
				inStr = not inStr

			if override == None and (readChar not in [" ", "\t"] or inStr):
				outstring += readChar
			elif override != None and (readChar not in override or inStr):
				outstring += readChar
			if limit != None and len(outstring) == limit:
				return outstring
		self.sourcefile.seek(self.sourcefile.tell() - 1, 0)
		return outstring
