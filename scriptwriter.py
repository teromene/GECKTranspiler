from tokenizer import Token
from translator import Translator
#Very basic rewriter, cannot even do symbol collection
class GECKFunction:
	target = None
	functionName = ""
	argList = []

	def __init__(self, target, functionName, argList = []):
		self.target = target
		self.functionName = functionName
		self.argList = argList
	
	def addToParam(self):
		pass
		
	def nextParam(self):
		pass
	
	def writeFunction(self):
		print(self.target, self.functionName, self.argList)
		#Call the translator on this, and collect the vartypes output
		translator = Translator(self)
		
#Used to check typing, especially of REFS
class GECKCondition:
	leftOperand = None
	rightOperand = None
	logicOp = None
	
	def __init__(self):
		pass
		
	def addToLeft(self, token):
		pass
		
	def addToRight(self, token):
		pass
		
	def setLogicOp(self, token):
		pass
	
class ScriptWriter:

	buffer = ""	

	def __init__(self, tokens, outfile):
		self.tokens = tokens
		self.outfile = outfile

	def run(self):
		self.indentLevel = 0
		currentFunction = None
		for token in self.tokens:
			if token.tokenType == Token.TOKEN_SCRIPTNAME:
				self.writeLine("Scriptname " + token.val1 + "\n")
			elif token.tokenType == Token.TOKEN_COMMENT:
				self.writeLine(";" + token.val1)
			elif token.tokenType == Token.TOKEN_BEGINBLOCK:
				self.writeLine("\nEvent " + token.val1 + "()", False, False)
				self.indentLevel += 1
			elif token.tokenType == Token.TOKEN_ENDBLOCK:
				self.indentLevel -= 1
				self.writeLine("EndEvent\n", False, False)
			elif token.tokenType == Token.TOKEN_STATEMENTSTART:
				self.writeLine("", True, False)
			elif token.tokenType == Token.TOKEN_STATEMENTEND:
				self.removeLastCharEquals("\n")
				self.removeLastCharEquals(" ")
				self.writeLine("", False, True)
			elif token.tokenType == Token.TOKEN_VARINT:
				self.writeLine("int " + token.val1 + " ")
			elif token.tokenType == Token.TOKEN_VARREF:
				self.writeLine("ObjectReference Property " + token.val1 + " ")
			elif token.tokenType == Token.TOKEN_VAR:
				if token.val2 != None:
					self.writeLine(token.val1 + "." + token.val2 + " ")
				else:
					self.writeLine(token.val1 + " ")				
			elif token.tokenType == Token.TOKEN_IFSTART:
				self.writeLine("If ", True, False)
			elif token.tokenType == Token.TOKEN_IFEND:
				self.indentLevel -= 1
				self.writeLine("EndIf", False, False)
			elif token.tokenType == Token.TOKEN_IFCONDSTART:
				pass
			elif token.tokenType == Token.TOKEN_IFCONDEND:
				self.writeLine("", False)
				self.indentLevel += 1
			elif token.tokenType == Token.TOKEN_ELSE:
				self.indentLevel -= 1
				self.writeLine("Else ", False, False)
				self.indentLevel += 1
			elif token.tokenType == Token.TOKEN_ELSEIF:
				self.indentLevel -= 1
				self.writeLine("ElseIf ", True, False)
			elif token.tokenType in [Token.TOKEN_RELOP, Token.TOKEN_NUMOP, Token.TOKEN_MATHOP, Token.TOKEN_LOGICOP]:
				self.writeLine(token.val1 + " ")
			elif token.tokenType == Token.TOKEN_FUNCALL:
				if token.val1 == None:
					self.writeLine(token.val2)
				else:
					self.writeLine(token.val1 + "." + token.val2)
				currentFunction = GECKFunction(token.val1, token.val2)
			elif token.tokenType == Token.TOKEN_FUNPARAMLISTSTART:
				self.writeLine("(")
			elif token.tokenType == Token.TOKEN_FUNPARAMLISTEND:
				self.removeLastCharEquals(" ")
				self.removeLastCharEquals(",")
				currentFunction.writeFunction()
				self.writeLine(") ")
			elif token.tokenType == Token.TOKEN_FUNPARAMSTART:
				currentFunction.nextParam()
			elif token.tokenType == Token.TOKEN_FUNPARAMEND:
				self.removeLastCharEquals(" ")
				self.writeLine(", ")
			elif token.tokenType == Token.TOKEN_BRACKETSTART:
				self.writeLine("(")
			elif token.tokenType == Token.TOKEN_BRACKETEND:
				self.removeLastCharEquals(" ")
				self.writeLine(")")
			elif token.tokenType == Token.TOKEN_SETCALLSTART:
				pass
			elif token.tokenType == Token.TOKEN_SETCALLEND:
				pass
			elif token.tokenType == Token.TOKEN_SETCALLVAR:
				if token.val2 == None:
					self.writeLine(token.val1 + " ")
				else:
					self.writeLine(token.val1 + "." + token.val2 + " ")
			elif token.tokenType == Token.TOKEN_SETCALLVALSTART:
				self.writeLine("= ")
			elif token.tokenType == Token.TOKEN_SETCALLVALEND:
				pass
			else:
				print("ERR: Unknown token " + token.tokenType)
				self.writeFile()
				return

		self.writeFile()

	def writeFile(self):
		self.outfile.write(self.buffer)

	def removeLastCharEquals(self, char):
		if self.buffer[-1] == char:
			self.buffer = self.buffer[:-1]

	def writeLine(self, text, ignoreLR = True, ignoreIndent = True):
		if not ignoreIndent:
			for i in range(0, self.indentLevel):
				self.buffer += "\t"
		self.buffer += text
		if not ignoreLR:
			self.buffer += "\n"
