import sys

from lexertab import CoolLexer
from parsertab import CoolParser
from semantics import (TypeCollector, TypeBuilder, OverriddenMethodChecker, TypeChecker, topological_ordering)
from semantics.formatter import CodeBuilder
from semantics.execution import Executor, ExecutionError
from semantics.type_inference import InferenceChecker
from semantics.utils.scope import Context, Scope

execution_errors = r"""
(* class A {
    a (n: Int) : Int { 0 };
}

class B inherits A {
    a (x: String) : String { 1 };
} *)

class Main {
    x: Int;

    main (): Object {
        let a: Main in a.f()
    };

    f() : Int {
        0
    };
}
"""

inference_program_01 = r"""
class Main { main (): Object { 0 }; }

class Point {
    x: AUTO_TYPE;
    y: AUTO_TYPE;

    init(x0: Int, y0: Int): AUTO_TYPE {{
        x <- x0;
        y <- y0;
        self;
    }};
}
"""

inference_program_02 = r"""
class Main { main (): Object { 0 }; }

class Ackermann {
    ackermann(m: AUTO_TYPE, n: AUTO_TYPE): AUTO_TYPE {
        if m = 0 then n + 1 else
            if n = 0 then ackermann(m - 1, 1) else
                ackermann(m - 1, ackermann(m, n - 1))
            fi
        fi
    };
}
"""

inference_program_03 = r"""
class Main {
    main (): Object { 0 };

    f(a: AUTO_TYPE, b: AUTO_TYPE): AUTO_TYPE {
        if a = 1 then b else
            g(a + 1, b / 1) 
        fi
    };
    
    g(a: AUTO_TYPE, b: AUTO_TYPE): AUTO_TYPE {
        if b = 1 then a else
            f(a / 2, b + 1) 
        fi
    };
}
"""

execution_program_01 = r"""
class A { }

class B inherits A { }

class C inherits A { }

class Main inherits IO {
    number: Int <- 5;

    main () : Object {
        0
    };
    
    testing_case() : IO {
        let a: A <- new C in 
            case a of
                x: B => out_string("Is type B.\n");
                x: C => out_string("Is type C.\n");
            esac
    };
    
    testing_fibonacci(n: Int) : IO {{
        out_string("Iterative Fibonacci : ");
        out_int(iterative_fibonacci(5));
        out_string("\n");

        out_string("Recursive Fibonacci : ");
        out_int(recursive_fibonacci(5));
        out_string("\n");
    }};
    
    recursive_fibonacci (n: AUTO_TYPE) : AUTO_TYPE {
        if n <= 2 then 1 else recursive_fibonacci(n - 1) + recursive_fibonacci(n - 2) fi
    };
    
    iterative_fibonacci(n: AUTO_TYPE) : AUTO_TYPE {
        let  i: Int <- 2, n1: Int <- 1, n2: Int <- 1, temp: Int in {
            while i < n loop
                let temp: Int <- n2 in {
                    n2 <- n2 + n1;
                    n1 <- temp;
                    i <- i + 1;
                }
            pool;
            n2;
        }
    };
}
"""

syntactic_errors = """
class Main {
    a: Int
    
    b: String
    
    main () : Object { let a: Int <- "" in 0 }
    
    errors() : Object {
        case a of
            x: Int => (new IO).out_int(x)
            y: String => (new IO).out_string(x)
        esac
    }
}
"""

verbose = bool(sys.argv[1]) if len(sys.argv) > 1 else False
lexer = CoolLexer()
parser = CoolParser(verbose)

if __name__ == '__main__':

    tokens = lexer(syntactic_errors)
    ast = parser(tokens)

    if parser.contains_errors:
        for e in parser.errors:
            sys.stderr.write(e + '\n')

    if ast is not None:
        context = Context()
        errors = []
        scope = Scope()

        TypeCollector(context, errors).visit(ast)
        TypeBuilder(context, errors).visit(ast)
        topological_ordering(ast, context, errors)
        OverriddenMethodChecker(context, errors).visit(ast)
        InferenceChecker(context, errors).visit(ast, scope)
        TypeChecker(context, errors).visit(ast, scope)

        if verbose:
            print(CodeBuilder().visit(ast, 0), '\n')

        if not errors and not parser.contains_errors:
            try:
                Executor(context).visit(ast, Scope())
                print('Program finished...')
            except ExecutionError as e:
                sys.stderr.write(e.text + '\n')

        for error in errors:
            sys.stderr.write(error + '\n')
