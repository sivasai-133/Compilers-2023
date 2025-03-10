import sys
from parser import *
from typechecking import *
from sim import *
import pprint
from error import *
from resolver import *
import time
try:
    import readline
except:
    from pyreadline3 import Readline
    readline = Readline()

# Global error flag also takes care of exceptions
isError = False

# Function definitions
def executeFile(path: str):
    '''
    Executes the file at the given path
    '''
    # Try to obtain the stream of characters
    try: 
        stream = None
        with open(path, 'r') as file:
            stream = ''.join(file.readlines()).strip()
    # In case the given file location is invalid
    except:
        print(f"Specified file at {path} does not exist!")
        exit(-1)
    
    execute(stream, ResolverScopes(), Scopes(), Scopes())

def execute(stream:str, resolverScopes: ResolverScopes, typecheckerScopes: Scopes, scopes: Scopes):
    global isError
    try: 
        programAST = parse(stream) 
        
        # print(programAST)
        # Resolving the AST
        pp = pprint.PrettyPrinter(indent=4)
        # print(programAST)
        resolvedProgram = resolve(programAST, resolverScopes)
        # pp.pprint(resolvedProgram)
        # Performing typechecking
        typecheckAST(resolvedProgram, typecheckerScopes) # any TypecheckError in the stream would be caught in the typecheckAST function and the error flag would be set
        output = evaluate(resolvedProgram, scopes)
        return output
        
    
    except (RuntimeException, TypeCheckException, ParseException, ResolveException, RecursionError) as e:
        isError = True
        return nil()
    
    except Exception as e:
        # An uncaught expression for development purpose (Due to unhandled cases in the parser)
        raise e

def interactiveShell():
    '''
    Run the lanuage in interactive shell form
    '''

    global isError

    # Creating Scopes
    scopes = Scopes()

    # Creating scopes for typechecking
    typecheckerScopes = Scopes()

    # Creating scopes for resolving
    resolverScopes = ResolverScopes()

    try:
        while True:
            
            # variable to get all the lines
            lines = ""
            
            # Initially get line as input
            line = input(">> ").strip()
            lines += line 

            # Take input until the no line is given if the line does not end with ";"
            if (not line.endswith(';')):
                while(line != ""):
                    line = input(".. ").strip()
                    if (line != ""):
                        lines += line
            
            # Way to exit the shell
            if (lines.strip() == "exit") :
                print("Goodbye")
                break
            
            # Executing the lines
            output = execute(lines, resolverScopes, typecheckerScopes, scopes)
            
            # Printing new line after each line
            print()

            isError = False
            
    except KeyboardInterrupt:
        print("GoodBye")

if __name__ == "__main__":
    
    args = sys.argv

    n = len(args)

    if (n > 2):
        # Error (Invalid arguments provided)
        print("Invalid Number of arguments")
        exit(-1)

    elif (n == 2):
        # Runninng the given script
        executeFile(args[1])
    else:
        # Running the interactive shell
        interactiveShell()
