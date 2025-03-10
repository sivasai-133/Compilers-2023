from sim import *
from error import typeCheckError, TypeCheckException
from dataclasses import dataclass
from typing import List, Dict, Union

"""
NOTE: In some places we used python exception to raise errors that are not caught at any level.
This is because the error occured due to the bad functioning of the parser(and we want to correct them).
Some errors are to be shifted to the resolver pass and are also not caught at any level.(in Type check scopes)
"""

# Some Utility functions
def checkTypeTwo(firstOperandType: AST, secondOperandType: AST, firstType: type, secondType: type):
    '''
    Utility to check the type of the operands
    '''
    if not issubclass(firstOperandType, firstType):
        return False
    if not issubclass(secondOperandType, secondType):
        return False
    return True

def checkSameType(firstOperandType: AST, secondOperandType: AST):
    '''
    Utility to check the if both operands are of the same type
    '''
    if not (issubclass(firstOperandType, secondOperandType) and issubclass(firstOperandType, secondOperandType)):
        return False
    return True

Number = Int | Float

def createDummyObject(type_ : type):
    '''
    Utility to Create a dummy(useles) object from the given type
    '''
    if type_ == Int:
        return Int(0)
    elif type_ == Bool:
        return Bool(False)
    elif type_ == Str:
        return Str("")
    elif type_ == Float:
        return Float(0)
    elif type_ == nil:
        return nil()


def typecheckAST(program: AST, scopes: Scopes):
    '''
    Typechecks the given AST
    '''
    try:
        typecheck(program, scopes)
    except TypeCheckException as e:
        raise e

def typecheckArray(lst: zArray, lineNumber: int, scopes:Scopes):
    '''
    Utility function to check the sanity of the array
    '''
    if (lst.dtype[1] == zArray):
        for element in lst.elements:
            if isinstance(element, zArray):
                # Recursively check the sanity of the array
                typecheckArray(element, lineNumber, scopes)

                # Check if the data type of the elements of the array is same as the data type mentioned in the array
                if (lst.dtype[1:] != element.dtype):
                    typeCheckError(f"Array of type {lst.dtype} cannot have elements of type {typecheck(element, scopes)}", lineNumber)
            else:
                et = typecheck(element, scopes)
                if (isinstance(et, type)):
                    typeCheckError(f"Array of type {lst.dtype} cannot have elements of type {et.__name__}", lineNumber)
                elif ((not isinstance(et, arrayType))):
                    typeCheckError(f"Array of type {lst.dtype} cannot have elements of type {et}", lineNumber)
                elif (et.dtype != lst.dtype[1:]):
                    typeCheckError(f"Array of type {lst.dtype} cannot have elements of type {et}", lineNumber)
    else:
        for element in lst.elements:
            et = typecheck(element, scopes)
            if (et != lst.dtype[1]):
                typeCheckError(f"Array of type {lst.dtype[1]} cannot have elements of type {et}", lineNumber)


def dimensions(lst):
    if isinstance(lst, zArray):
        return [len(lst.elements)] + dimensions(lst.elements[0])
    else:
        return []

def typecheck(program: AST, scopes = None):
    if (scopes == None):
        scopes = Scopes()
    match program:
        case Float(): 
            return Float
        
        case Int(): 
            return Int
        
        case Bool(): 
            return Bool
        
        case Variable(lineNumber, name, id) as v:
            return scopes.getVariableType(v)
        
        case Str():
            return Str
        
        case This(lineNumber, id):
            return scopes.getVariableType(Variable(lineNumber, "this", id))

        case nil():
            return nil
        
        case InstanceObject() as obj:
            return instanceType(obj.zClass)
        
        case zArray(lineNumber, dtype, lst) as arr:
            typecheckArray(arr, lineNumber, scopes)
            return arrayType(arr.dtype)
        
        case BinOp(lineNumber, operator, firstOperand, secondOperand):
            # Getting the operand types
            firstOperandType = typecheck(firstOperand, scopes)
            secondOperandType = typecheck(secondOperand, scopes)
            # Checking if the operator is defined
            if (operator not in BINARY_OPERATORS):           
                typeCheckError(f"Binary Operator {operator} not recognized", lineNumber)

            # Raising type error in case left or the right side donot evaluate to a type
            if (operator != '=' and (((not isinstance(firstOperandType, type)) and isinstance(firstOperandType, instanceType)) or ((not isinstance(secondOperandType, type)) and isinstance(secondOperandType, instanceType)))):
                typeCheckError(f"Operator {operator} not defined between {firstOperandType} and {secondOperandType}", lineNumber)
            if (operator not in ['=', '+'] and (((not isinstance(firstOperandType, type)) and isinstance(firstOperandType, arrayType)) or ((not isinstance(secondOperandType, type)) and isinstance(secondOperandType, arrayType)))):
                typeCheckError(f"Operator {operator} not defined between {firstOperandType} and {secondOperandType}", lineNumber)
            
            if (operator != '='):
                ft = firstOperandType.__name__ if isinstance(firstOperandType, type) else firstOperandType
                st = secondOperandType.__name__ if isinstance(secondOperandType, type) else secondOperandType
                # General BinOp type error string
                errorString = f"Operator {operator} not defined between data types {ft} and {st}"
            match operator:
                case  "+":
                    if ((not isinstance(firstOperandType, type)) and (not isinstance(secondOperandType, type)) and (firstOperandType != secondOperandType)):
                        typeCheckError(errorString, lineNumber)
                    elif ((isinstance(firstOperandType, type)) and (isinstance(secondOperandType, type)) and issubclass(firstOperandType, Str) and not checkTypeTwo(firstOperandType, secondOperandType, Str, Str)):
                        typeCheckError(errorString, lineNumber)
                    elif ((isinstance(firstOperandType, type)) and (isinstance(secondOperandType, type)) and issubclass(firstOperandType, Number) and not checkTypeTwo(firstOperandType, secondOperandType, Number, Number)):
                        typeCheckError(errorString, lineNumber)

                    if ((not isinstance(firstOperandType, type)) and isinstance(firstOperandType, arrayType)):
                        return firstOperandType
                    elif (issubclass(firstOperandType, Float) or issubclass(secondOperandType, Float)):
                        return Float
                    elif (issubclass(firstOperandType, Str)):
                        return Str
                    else:
                        return Int
                    
                case  "-":
                    
                    if ((not isinstance(firstOperandType, type)) and (not isinstance(secondOperandType, type))):
                        typeCheckError(errorString, lineNumber)

                    if not checkTypeTwo(firstOperandType, secondOperandType, Number, Number):
                        typeCheckError(errorString, lineNumber)
                    
                    if (issubclass(firstOperandType, Float) or issubclass(secondOperandType, Float)):
                        return Float
                    else:
                        return Int

                case "/":
                    if ((not isinstance(firstOperandType, type)) and (not isinstance(secondOperandType, type))):
                        typeCheckError(errorString, lineNumber)

                    if not checkTypeTwo(firstOperandType, secondOperandType, Number, Number):
                        typeCheckError(errorString, lineNumber)
                    return Float
                
                case "*":
                    if ((not isinstance(firstOperandType, type)) and (not isinstance(secondOperandType, type))):
                        typeCheckError(errorString, lineNumber)
                    if (issubclass(firstOperandType,Str) and issubclass(secondOperandType, Int)):
                        return Str

                    elif (issubclass(firstOperandType,Int) and issubclass(secondOperandType,Str)):
                        return Str
                    elif not checkTypeTwo(firstOperandType, secondOperandType, Number, Number):
                        typeCheckError(errorString, lineNumber)
                    else:
                        if (issubclass(firstOperandType, Float) | issubclass(secondOperandType, Float)):
                            return Float
                        else:
                            return Int
                
                case "//" :
                    if ((not isinstance(firstOperandType, type)) and (not isinstance(secondOperandType, type))):
                        typeCheckError(errorString, lineNumber)
                    if not checkTypeTwo(firstOperandType, secondOperandType, Number, Number):
                        typeCheckError(errorString, lineNumber)
                    return Int
                
                case "%" | "<<" | ">>" | "&" | "|":
                    if ((not isinstance(firstOperandType, type)) and (not isinstance(secondOperandType, type))):
                        typeCheckError(errorString, lineNumber)
                    if not checkTypeTwo(firstOperandType, secondOperandType, Int, Int):
                        typeCheckError(errorString, lineNumber)
                    return Int
                
                
                case "<=" | "<" | "==" | ">" | ">=" | "!=":
                    if not checkSameType(firstOperandType, secondOperandType):
                        typeCheckError(errorString, lineNumber)
                    return Bool
                
                case "&&" | "||": 
                    if ((not isinstance(firstOperandType, type)) and (not isinstance(secondOperandType, type))):
                        typeCheckError(errorString, lineNumber)
                    if not checkTypeTwo(firstOperandType, secondOperandType, AST, AST):
                        typeCheckError(errorString, lineNumber)
                    return Bool
                
                case "=":         
                    if ((not isinstance(secondOperandType, type)) and isinstance(secondOperandType, arrayType)):
                        scopes.updateVariable(firstOperand, zArray(lineNumber, secondOperandType.dtype, []))
                        return secondOperandType
                    elif (isinstance(secondOperandType, instanceType)):
                        scopes.updateVariable(firstOperand, InstanceObject(secondOperandType.name, {}))
                        return secondOperandType
                    scopes.updateVariable(firstOperand, createDummyObject(secondOperandType))
                    return secondOperandType
                
                case "^":
                    if ((not isinstance(firstOperandType, type)) and (not isinstance(secondOperandType, type))):
                        typeCheckError(errorString, lineNumber)
                    if not checkTypeTwo(firstOperandType, secondOperandType, Number, Number):
                        typeCheckError(errorString, lineNumber)
                    if (issubclass(firstOperandType, Float) or issubclass(secondOperandType, Float)):
                        return Float
                    else:
                        return Int


        case UnOp(lineNumber, operator, operand):   
            opearandType = typecheck(operand, scopes)
            
            if (operator not in UNARY_OPERATORS):
                typeCheckError(f"Unary Operator {operator} not reconized", lineNumber)
            if (not isinstance(opearandType, type)):
                if (isinstance(opearandType, InstanceObject)):
                    typeCheckError(f"Operator {operator} is not defined for {opearandType}", lineNumber)

            match operator:
                case "-":
                    if not issubclass(opearandType, Number):
                        typeCheckError(f"Operator {operator} is not defined for data type {opearandType.__name__}", lineNumber)
                    elif (isinstance(opearandType, Float)):
                        return Float
                    else:
                        return Int
                case "~":
                    if not issubclass(opearandType, Bool):
                        typeCheckError(f"Operator {operator} is not defined for data type {opearandType.__name__}", lineNumber)
                    return Bool

        case Declare(lineNumber, var, value, dtype, isConst) as dec:
            if (not isinstance(var, Variable)):
                raise Exception("RHS of declaration must be of type \'Variable\'")

            # Make sure all the elements of the array are of the type zArray.dtype
            if ((not isinstance(dtype, type)) and isinstance(dtype, arrayType)):
                at = typecheck(value, scopes)
                if (at != dtype):
                    typeCheckError(f"Cannot initialize {dtype} with {at}.", lineNumber)
                scopes.declareVariable(var, nil(), dtype, isConst)

            else:
                # Evaluating the expression before declaration
                value = typecheck(value, scopes)
                if (not isinstance(dtype, type) and isinstance(dtype, instanceType)):
                    if value != nil:
                        if ((isinstance(value, type)) or not isinstance(value, instanceType)):
                            typeCheckError(f"Cannot initialize {dtype.name} with {value}.", lineNumber)
                        dec.dtype = instanceType(scopes.getVariable(dtype.name))
                        scopes.declareVariable(var, InstanceObject(value.name, {}), instanceType(scopes.getVariable(dtype.name)), isConst)
                    else:
                        dec.dtype = instanceType(scopes.getVariable(dtype.name))
                        scopes.declareVariable(var, nil(), instanceType(scopes.getVariable(dtype.name)), isConst)
                else:
                    scopes.declareVariable(var, createDummyObject(value), dtype, isConst)
            return dtype

        case Slice(lineNumber, value_, first, second):       #checking value_ is string 
            tc = typecheck(value_, scopes)
            tf = typecheck(first, scopes)
            ts = typecheck(second, scopes)
            
            if (not isinstance(tf, type) or not isinstance(ts, type)) or (not (issubclass(tf, Int) or issubclass(ts, Int))):
                typeCheckError(f"Slice indices must be of {Int} type", lineNumber)
            if (not isinstance(tc, type) and isinstance(tc, arrayType)):
                return tc
            elif (isinstance(tc, type) and issubclass(tc, Str)):
                return tc
            else:
                typeCheckError(f"Slice operation not defined for {tc}", lineNumber)
            return tc

        case While(lineNumber, condition, block) :            #checking while condition data type
            tc = typecheck(condition, scopes)
            return typecheck(block, scopes)
        
        case If (lineNumber, condition, ifBlock, elseBlock): #checking if condition data type
            tc = typecheck(condition, scopes)
            tif = typecheck(ifBlock, scopes)
            telse = typecheck(elseBlock, scopes)
            return tif + telse


        case For(lineNumber, initial,condition,block):
            scopes.beginScope()
            
            tc1 = typecheck(initial, scopes)
            tc = typecheck(condition, scopes)
            retType = typecheck(block, scopes)
            
            scopes.endScope()
            return retType
        
        case Set(lineNumber, var, name, value):
            # Type check the value
            tv = typecheck(value, scopes)
            # Type check the variable and get the instanceType of the object
            var = typecheck(var, scopes)
            # Cheking if the returned value is an instanceType
            if (isinstance(var, type) or (not isinstance(var, instanceType))):
                typeCheckError(f"Expected an instance", lineNumber)
            for stmt in list(var.name.methods.values()):
                if (isinstance(stmt, Declare)):
                    if (stmt.var.name == name):
                        if (stmt.dtype != tv):
                            typeCheckError(f"Cannot set field of type {stmt.dtype} to a {tv}", lineNumber)
            return tv
        
        case Seq(lines):
            ret = []
            for line in lines:
                retVal = typecheck(line, scopes)
                
                if (not isinstance(retVal, type) and isinstance(retVal, list)):
                    for r in retVal:
                        if ((not isinstance(r, type)) and isinstance(r, Return)):
                            ret.append(r)
                
                else:
                    if ((not isinstance(retVal, type)) and isinstance(retVal, Return)):
                        ret.append(retVal)
            if ret == []:
                ret.append(nil)
            return ret
        
        case PRINT(lineNumber, exps, sep,end):
            sep = typecheck(sep, scopes)
            end = typecheck(end, scopes)
            for exp in exps:
                exp = typecheck(exp, scopes)
                if (not issubclass(sep, Str)):
                    typeCheckError(f"Invalid separator {sep} in PRINT at {lineNumber}")
                if (not issubclass(end, Str)):
                    typeCheckError(f"Invalid end {end} in PRINT at {lineNumber}")
            return nil
        
        case array_append(lineNumber, element, array_name):
            var_type = typecheck(array_name, scopes)
            element = typecheck(element,scopes)
            if (not isinstance(var_type, type) and isinstance(var_type, arrayType)):
                if (not isinstance(element, type) and isinstance(element, arrayType)):
                    if (var_type.dtype[1:] != element.dtype) :
                        typeCheckError(f"Cannot append {element} to {var_type}.", lineNumber)
                elif (isinstance(element, type)):
                    if (var_type.dtype[1] != element):
                        typeCheckError(f"Cannot append {element.__name__} to {var_type}.", lineNumber)
                elif isinstance(element, instanceType):
                    if (var_type.dtype[1] != element.name):
                        typeCheckError(f"Cannot append {element} to {var_type}.", lineNumber)
            else:
                typeCheckError(f"Expected an array for appending.", lineNumber)
            return nil
        
        case array_remove(lineNumber, index, array_name):
            var_type = typecheck(array_name, scopes)
            ind = typecheck(index, scopes)
            if ((not isinstance(ind, type)) or (not issubclass(ind, Int))):
                typeCheckError(f"Index must be an integer.", lineNumber)
            
            if not (not isinstance(var_type, type) and isinstance(var_type, arrayType)):
                typeCheckError(f"Expected an array for appending.", lineNumber)
            
            if (var_type.dtype[1] == zArray):
                return arrayType(var_type.dtype[1:])
            else:
                return var_type.dtype[1]
            
        case array_len(lineNumber, l):
            l = typecheck(l, scopes)
            if (not isinstance(l, type) and isinstance(l, arrayType)) or (issubclass(l, Str)):
                return Int
            else:
                typeCheckError(f"length attribute not defined for variable of type  {l.__name__}.", lineNumber)
        
        case array_pop(lineNumber, array_name):
            var_type = typecheck(array_name, scopes)
            if (isinstance(var_type, type) or not isinstance(var_type, arrayType)):
                typeCheckError(f"Expected an array for pop.", lineNumber)
            if (var_type.dtype[1] == zArray):
                return arrayType(var_type.dtype[1:])
            else:
                return var_type.dtype[1]
        
        case array_insert(lineNumber, index, element, array_name):
            var_type = typecheck(array_name, scopes)
            element = typecheck(element,scopes)
            ind = typecheck(index, scopes)
            if ((not isinstance(ind, type)) or (not issubclass(ind, Int))):
                typeCheckError(f"Index must be an integer.", lineNumber)

            if (not isinstance(var_type, type) and isinstance(var_type, arrayType)):
                if (not isinstance(element, type) and isinstance(element, arrayType)):
                    if (var_type.dtype[1:] != element.dtype) :
                        typeCheckError(f"Cannot append {element} to {var_type}.", lineNumber)
                elif (isinstance(element, type)):
                    if (var_type.dtype[1] != element):
                        typeCheckError(f"Cannot append {element.__name__} to {var_type}.", lineNumber)
                elif isinstance(element, instanceType):
                    if (var_type.dtype[1] != element.name):
                        typeCheckError(f"Cannot append {element} to {var_type}.", lineNumber)
            else:
                typeCheckError(f"Expected an array for appending.", lineNumber)
            
            return nil
         
        case DeclareFun(lineNumber, f, return_type, params_type, params, body, function_type):
            
            # Declaring the function in the current scope
            scopes.declareFun(f, FnObject(function_type, params_type, params, body, return_type)) 

            # Replacing the reolved references to class object with the actual class object
            for i in range(len(params_type)):
                if (not isinstance(params_type[i], type) and isinstance(params_type[i], instanceType)):
                    params_type[i] = instanceType(scopes.getVariable(params_type[i].name))

            # Strategy to type check the body

            # 1. begin a new scope
            scopes.beginScope()

            # 2. Initialize all the params using a dummy object
            for param, param_type in zip(params, params_type):
                if (not isinstance(param_type, type) and isinstance(param_type, instanceType)):
                    scopes.declareVariable(param, InstanceObject(param_type.name, {}), param_type, False)
                elif (not isinstance(param_type, type) and isinstance(param_type, arrayType)):
                    scopes.declareVariable(param, nil(), param_type, False)
                else:
                    scopes.declareVariable(param, createDummyObject(param_type), param_type, False)

            # 3. type check the body
            retTypes = typecheck(body, scopes)
            # 4. make sure that the return types are the same
            for retType in retTypes:
                if retType != nil:
                    retType = retType.value
                if (not(isinstance(return_type, type)) and isinstance(return_type, instanceType)):
                    if (not isinstance(retType, type)) and (isinstance(retType, instanceType)):
                        if retType.name != return_type.name:
                            typeCheckError(f"Not matching the expected return type of the function", lineNumber)
                    else:
                        typeCheckError(f"Not matching the expected return type of the function", lineNumber)
                
                elif (not(isinstance(return_type, type)) and isinstance(return_type, arrayType)):
                    if (not isinstance(retType, type)) and (isinstance(retType, arrayType)):
                        if retType.dtype != return_type.dtype:
                            typeCheckError(f"Not matching the expected return type of the function", lineNumber)
                    else:
                        typeCheckError(f"Not matching the expected return type of the function", lineNumber)
                
                elif ((not issubclass(retType, nil)) and (not(issubclass(retType, return_type)))):
                    typeCheckError(f"Not matching the expected return type of the function", lineNumber)
            
            # 5. return nil as declaration statements have no return type
            return nil
        
        case FunCall(lineNumber, f, args): 
            # Get the method from the specified object object
            if isinstance(f, Get):
                fn = typecheck(f, scopes) # Would return an ClassObject 
            else:
                fn = scopes.getVariable(f) # Would return a FnObject 
            
            # In case it is a class Object, we instantiate it
            if isinstance(fn, ClassObject):
                # Check if the type of arguments passed is correct
                if "init" in fn.methods:
                    params_type = fn.methods["init"].params_type
                    if len(args) != len(params_type):
                        raise typeCheckError(f"Number of arguments for init method of {fn.name} does not match", lineNumber, "integrityError")
                    for i in range(len(params_type)):
                        arg = typecheck(args[i], scopes)
                        if (not isinstance(params_type[i], type)) and isinstance(params_type[i], instanceType):
                            if (not isinstance(arg, type)) and isinstance(arg, instanceType):
                                if arg.name != params_type[i].name:
                                    typeCheckError(f"{i+1}th Argument passed to the init function is of invalid type", lineNumber)
                            else:
                                typeCheckError(f"{i+1}th Argument passed to the init function is of invalid type", lineNumber)
                        elif (not isinstance(params_type[i], type)) and isinstance(params_type[i], arrayType):
                            if (not isinstance(arg, type)) and isinstance(arg, arrayType):
                                if arg.dtype != params_type[i].dtype:
                                    typeCheckError(f"{i+1}th Argument passed to the init function is of invalid type", lineNumber)
                            else:
                                typeCheckError(f"{i+1}th Argument passed to the init function is of invalid type", lineNumber)
                        elif not (issubclass(arg, params_type[i])):
                            typeCheckError(f"{i+1}th Argument passed to the init function is of invalid type", lineNumber)

                # In case the value arguments are passed but the init method does not exist    
                elif len(args) > 0:
                    raise typeCheckError(f"Class {fn.name} does not have an init method", lineNumber, "integrityError")
                
                # Return the instanceType of the class
                return instanceType(fn)

            # In case of Functions
            # Generate the type of arguments
            argv = []
            for arg in args:
                argv.append(typecheck(arg, scopes))
            
            # Only typechecking the param type and the argument types
            p_types = fn.params_types
            for i in range(len(p_types)):
                if ((not isinstance(p_types[i], type)) and isinstance(p_types[i], instanceType)):
                    if (isinstance(argv[i], type) or not(isinstance(argv[i], instanceType)) or argv[i].name != p_types[i].name):
                        raise typeCheckError(f"{i+1}th Argument passed to the function is of invalid type", lineNumber)
                elif (not isinstance(p_types[i], type) and (isinstance(p_types[i], arrayType))):
                    if (isinstance(argv[i], type) or not(isinstance(argv[i], arrayType)) or argv[i].dtype != p_types[i].dtype):
                        raise typeCheckError(f"{i+1}th Argument passed to the function is of invalid type", lineNumber)
                elif (not(issubclass(p_types[i],(argv[i])))):
                    raise typeCheckError(f"{i+1}th Argument passed to the function is of invalid type", lineNumber)

            # Returning the return type of the function
            return fn.return_type
        
        case Return(lineNumber, exp):
            exp = typecheck(exp, scopes)
            return Return(lineNumber, exp)
        
        case Block(blockStatements):
            # Return the type of the last statement in the seq in block
            retType = typecheck(blockStatements, scopes)
            return retType
        
        case DeclareClass(lineNumber, var, stmts, thisID) as d:
            # Declaring the class object
            classObj = ClassObject(var.name, stmts, thisID)
            scopes.declareVariable(var, classObj, ClassObject, False)
            
            # Performing the typeChecking for Class methods and variable declarations
            # Begining scopes for the this variable
            scopes.beginScope()
            
            # Declaring a dummy this variable
            scopes.declareVariable(Variable(lineNumber, "this", thisID), InstanceObject(classObj, {}), instanceType(classObj), False)

            for stmt in stmts:
                stmt = stmts[stmt]
                # Declaring the instance fields
                if isinstance(stmt, Declare):
                    value = typecheck(stmt.value, scopes)
                    if (isinstance(value, type)):
                        value = createDummyObject(value)
                    if ((not isinstance(stmt.dtype, type)) and isinstance(stmt.dtype, instanceType)):
                        stmt.dtype = instanceType(scopes.getVariable(stmt.dtype.name))
                    scopes.getVariable(Variable(lineNumber, "this", thisID)).fields[stmt.var.name] = [value , stmt.dtype, stmt.isConst]
                elif isinstance(stmt, DeclareFun):
                    typecheck(stmt, scopes)
                else:
                    typeCheckError(f"Invalid statement in class definition", lineNumber)

            scopes.endScope()
            
            return nil
        
        case Get(lineNumber, var, name):
            obj =  typecheck(var, scopes)
            if isinstance(obj, type) or not isinstance(obj, instanceType):
                raise typeCheckError(f"Cannot access field {name} on {obj}", lineNumber, "AttributeError")
            classObj = obj.name
            if name not in classObj.methods:
                raise typeCheckError(f"Cannot access field {name} on {obj}", lineNumber, "AttributeError")
            
            field = nil()
            # Getting the field type
            for attr in classObj.methods:
                if (attr == name):
                    field = classObj.methods[attr]
                    if (isinstance(field, Declare)):
                        if isinstance(field.dtype, type) or isinstance(field.dtype, arrayType):
                            return field.dtype
                        elif isinstance(field.dtype, instanceType):
                            return instanceType(field.dtype.name)
                    elif (isinstance(field, DeclareFun)):
                        # Begining scopes for the this variable
                        scopes.beginScope()

                        # Declaring the this variable
                        scopes.declareVariable(Variable(lineNumber, "this", classObj.thisID), nil(), instanceType(classObj), False)

                        # Declaring the function
                        scopes.declareFun(field.var, FnObject(field.functionType, field.params_type, field.params, field.body, field.return_type))

                        # Obtaining the function object
                        fnObj = scopes.getVariable(field.var)

                        # Returning the function object
                        return fnObj
        
        case AtIndex(lineNumber, var, index):
            obj = typecheck(var, scopes)
            index = typecheck(index, scopes)
            
            # Object must be an array or a string
            if not ((not isinstance(obj, type) and isinstance(obj, arrayType)) or issubclass(obj, Str)):
                typeCheckError(f"Cannot access index {index} on {obj}", lineNumber, "AttributeError")
            
            # Raise error if the index is not an integer
            if (not isinstance(index, type)) or (not issubclass(index, Int)):
                typeCheckError(f"Index should be an integer", lineNumber, "TypeError")
            
            if isinstance(obj, arrayType):
                if (obj.dtype[1] == zArray):
                    return arrayType(obj.dtype[1:])
                else:
                    return obj.dtype[1]
            else:
                return Str
        
        case SetAtIndex(lineNumber, var, index, value):
            obj = typecheck(var, scopes)
            index = typecheck(index, scopes)
            value = typecheck(value, scopes)

            # Raise error if the index is not an integer
            if (not isinstance(index, type)) or (not issubclass(index, Int)):
                typeCheckError(f"Index should be an integer", lineNumber, "TypeError")
            
            # Object must be an array or a string
            if (((not isinstance(obj, type)) and (not isinstance(obj, arrayType))) or (isinstance(obj, type) and not issubclass(obj, Str))):
                typeCheckError(f"Cannot access index {index.__name__} on {obj}", lineNumber, "AttributeError")
            
            if isinstance(obj, arrayType):
                # Raise error if the value is not of the same type as the array
                if (isinstance(value, type)):
                    if [value] != obj.dtype[1:]:
                        typeCheckError(f"Cannot assign {value} to {obj}", lineNumber, "TypeError")
                elif ((not isinstance(value, arrayType)) or (value.dtype != obj.dtype[1:])):
                    typeCheckError(f"Cannot assign {value} to {obj}", lineNumber, "TypeError")
                return arrayType(obj.dtype[1:])
            else:
                # Raise error if the value is not a string
                if (not isinstance(value, type)) or (not issubclass(value, Str)):
                    typeCheckError(f"Cannot assign {value} to {obj}", lineNumber, "TypeError")
                return Str

        case _ as v:
            raise Exception(f"Got {v}, Invalid Expression|Statement")
