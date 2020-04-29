"""This module contains definitions of classes for make different travels through the AST of a cool program. All
classes defined here follows the visitor pattern using the module cmp.visitor, with this we can get a more decoupled
inspection. """
from typing import List, Optional

import astnodes as ast
import visitor as visitor

from scope import Context, SemanticError, Type, Scope, Method, AutoType, IntType, BoolType, StringType, ErrorType, \
    SelfType

"""
Object
    abort() : Object
    type_name() : String
    copy() : SELF_TYPE

IO
    out_string(x : String) : SELF_TYPE
    out_int(x : Int) : SELF_TYPE
    in_string() : String
    in_int() : Int

Int (Sealed)
    default -> 0

Bool (Sealed)
    default -> False

String
    length() : Int
    concat(s : String) : String
    substr(i : Int, l : Int) : String
"""
WRONG_SIGNATURE = 'Method "%s" already defined in "%s" with a different signature.'
SELF_IS_READONLY = 'Variable "self" is read-only.'
LOCAL_ALREADY_DEFINED = 'Variable "%s" is already defined in method "%s".'
INCOMPATIBLE_TYPES = 'Cannot convert "%s" into "%s".'
VARIABLE_NOT_DEFINED = 'Variable "%s" is not defined in "%s".'
INVALID_BINARY_OPERATION = 'Operation "%s" is not defined between "%s" and "%s".'
INVALID_UNARY_OPERATION = 'Operation "%s" is not defined for "%s".'


class Formatter:
    @visitor.on('node')
    def visit(self, node, tabs):
        pass

    @visitor.when(ast.ProgramNode)
    def visit(self, node: ast.ProgramNode, tabs: int = 0):
        ans = '\t' * tabs + f'\\__ProgramNode [<class> ... <class>]'
        statements = '\n'.join(self.visit(child, tabs + 1) for child in node.declarations)
        return f'{ans}\n{statements}'

    @visitor.when(ast.ClassDeclarationNode)
    def visit(self, node: ast.ClassDeclarationNode, tabs: int = 0):
        parent = '' if node.parent is None else f": {node.parent}"
        ans = '\t' * tabs + f'\\__ClassDeclarationNode: class {node.id} {parent} {{ <feature> ... <feature> }}'
        features = '\n'.join(self.visit(child, tabs + 1) for child in node.features)
        return f'{ans}\n{features}'

    @visitor.when(ast.AttrDeclarationNode)
    def visit(self, node: ast.AttrDeclarationNode, tabs: int = 0):
        ans = '\t' * tabs + f'\\__AttrDeclarationNode: {node.id} : {node.type}'
        return f'{ans}'

    @visitor.when(ast.MethodDeclarationNode)
    def visit(self, node: ast.MethodDeclarationNode, tabs: int = 0):
        params = ', '.join(':'.join(param) for param in node.params)
        ans = '\t' * tabs + f'\\__FuncDeclarationNode: {node.id}({params}) : {node.type} -> <body>'
        body = self.visit(node.body, tabs + 1)
        return f'{ans}\n{body}'

    @visitor.when(ast.LetNode)
    def visit(self, node: ast.LetNode, tabs: int = 0):
        declarations = '\n'.join(self.visit(declaration, tabs + 1) for declaration in node.declarations)
        ans = '\t' * tabs + f'\\__LetNode:  let'
        expr = self.visit(node.expr, tabs + 2)
        return f'{ans}\n {declarations}\n' + '\t' * (tabs + 1) + 'in\n' + f'{expr}'

    @visitor.when(ast.VarDeclarationNode)
    def visit(self, node: ast.VarDeclarationNode, tabs: int = 0):
        if node.expr is not None:
            return '\t' * tabs + f'\\__VarDeclarationNode: {node.id}: {node.type} <-\n{self.visit(node.expr, tabs + 1)}'
        else:
            return '\t' * tabs + f'\\__VarDeclarationNode: {node.id} : {node.type}'

    @visitor.when(ast.AssignNode)
    def visit(self, node: ast.AssignNode, tabs: int = 0):
        ans = '\t' * tabs + f'\\__AssignNode: {node.id} <- <expr>'
        expr = self.visit(node.expr, tabs + 1)
        return f'{ans}\n{expr}'

    @visitor.when(ast.BlockNode)
    def visit(self, node: ast.BlockNode, tabs: int = 0):
        ans = '\t' * tabs + f'\\__BlockNode:'
        body = '\n'.join(self.visit(child, tabs + 1) for child in node.expressions)
        return f'{ans}\n{body}'

    @visitor.when(ast.ConditionalNode)
    def visit(self, node: ast.ConditionalNode, tabs: int = 0):
        ifx = self.visit(node.if_expr, tabs + 2)
        then = self.visit(node.then_expr, tabs + 2)
        elsex = self.visit(node.else_expr, tabs + 2)

        return '\n'.join([
            '\t' * tabs + f'\\__IfThenElseNode: if <expr> then <expr> else <expr> fi',
            '\t' * (tabs + 1) + f'\\__if \n{ifx}',
            '\t' * (tabs + 1) + f'\\__then \n{then}',
            '\t' * (tabs + 1) + f'\\__else \n{elsex}',
        ])

    @visitor.when(ast.WhileNode)
    def visit(self, node: ast.WhileNode, tabs: int = 0):
        condition = self.visit(node.condition, tabs + 2)
        body = self.visit(node.body, tabs + 2)

        return '\n'.join([
            '\t' * tabs + f'\\__WhileNode: while <expr> loop <expr> pool',
            '\t' * (tabs + 1) + f'\\__while \n{condition}',
            '\t' * (tabs + 1) + f'\\__loop \n{body}',
        ])

    @visitor.when(ast.SwitchCaseNode)
    def visit(self, node: ast.SwitchCaseNode, tabs: int = 0):
        expr = self.visit(node.expr, tabs + 2)
        cases = '\n'.join(self.visit(case, tabs + 3) for case in node.cases)

        return '\n'.join([
            '\t' * tabs + f'\\__SwitchCaseNode: case <expr> of [<case> ... <case>] esac',
            '\t' * (tabs + 1) + f'\\__case \n{expr} of',
        ]) + '\n' + cases

    @visitor.when(ast.CaseNode)
    def visit(self, node: ast.CaseNode, tabs: int = 0):
        expr = self.visit(node.expr, tabs + 1)
        return '\t' * tabs + f'\\__CaseNode: {node.id} : {node.type} =>\n{expr}'

    @visitor.when(ast.MethodCallNode)
    def visit(self, node: ast.MethodCallNode, tabs: int = 0):
        obj = self.visit(node.obj, tabs + 1)
        ans = '\t' * tabs + f'\\__CallNode: <obj>.{node.id}(<expr>, ..., <expr>)'
        args = '\n'.join(self.visit(arg, tabs + 1) for arg in node.args)
        return f'{ans}\n{obj}\n{args}'

    @visitor.when(ast.BinaryNode)
    def visit(self, node: ast.BinaryNode, tabs: int = 0):
        ans = '\t' * tabs + f'\\__<expr> {node.__class__.__name__} <expr>'
        left = self.visit(node.left, tabs + 1)
        right = self.visit(node.right, tabs + 1)
        return f'{ans}\n{left}\n{right}'

    @visitor.when(ast.AtomicNode)
    def visit(self, node: ast.AtomicNode, tabs: int = 0):
        return '\t' * tabs + f'\\__ {node.__class__.__name__}: {node.lex}'

    @visitor.when(ast.InstantiateNode)
    def visit(self, node: ast.InstantiateNode, tabs: int = 0):
        return '\t' * tabs + f'\\__ InstantiateNode: new {node.lex}()'


class TypeCollector:
    def __init__(self, context: Context = Context(), errors: List[str] = []):
        self.errors: List[str] = errors
        self.context: Context = context

    @visitor.on('node')
    def visit(self, node):
        pass

    @visitor.when(ast.ProgramNode)
    def visit(self, node):
        self_type = self.context.create_type('SELF_TYPE')
        self.context.types['AUTO_TYPE'] = AutoType()
        object_type = self.context.create_type('Object')
        io_type = self.context.create_type('IO')
        string_type = self.context.create_type('String')
        int_type = self.context.create_type('Int')
        bool_type = self.context.create_type('Bool')

        io_type.parent = object_type
        string_type.parent = object_type
        int_type.parent = object_type
        bool_type.parent = object_type

        object_type.define_method('abort', ['self'], [object_type], object_type)
        object_type.define_method('get_type', ['self'], [object_type], string_type)
        object_type.define_method('copy', ['self'], [object_type], self_type)

        io_type.define_method('out_string', ['self', 'x'], [io_type, string_type], self_type)
        io_type.define_method('out_int', ['self', 'x'], [io_type, int_type], self_type)
        io_type.define_method('in_string', ['self'], [io_type], string_type)
        io_type.define_method('in_int', ['self'], [io_type], int_type)

        string_type.define_method('length', ['self'], [string_type], int_type)
        string_type.define_method('concat', ['self', 's'], [string_type, string_type], string_type)
        string_type.define_method('substr', ['self', 'i', 'l'], [string_type, int_type, int_type], string_type)

        for declaration in node.declarations:
            self.visit(declaration)

    @visitor.when(ast.ClassDeclarationNode)
    def visit(self, node):
        try:
            self.context.create_type(node.id)
        except SemanticError as e:
            self.errors.append(e.text)


class TypeBuilder:
    def __init__(self, context: Context, errors: List[str] = []):
        self.context: Context = context
        self.current_type: Optional[Type] = None
        self.errors: List[str] = errors

    @visitor.on('node')
    def visit(self, node):
        pass

    @visitor.when(ast.ProgramNode)
    def visit(self, node: ast.ProgramNode):
        for declaration in node.declarations:
            self.visit(declaration)

    @visitor.when(ast.ClassDeclarationNode)
    def visit(self, node: ast.ClassDeclarationNode):
        try:
            self.current_type = self.context.get_type(node.id)
            if node.parent is not None:
                if node.parent in (IntType(), BoolType(), StringType()):
                    self.errors.append(f'Cannot inherit from type "{node.parent}"')
                self.current_type.set_parent(self.context.get_type(node.parent))
            else:
                self.current_type.set_parent(self.context.get_type('Object'))
        except SemanticError as e:
            self.errors.append(e.text)

        for feature in node.features:
            self.visit(feature)

    @visitor.when(ast.AttrDeclarationNode)
    def visit(self, node: ast.AttrDeclarationNode):
        try:
            name = node.id
            typex = self.context.get_type(node.type)
            self.current_type.define_attribute(name, typex)
        except SemanticError as e:
            # Todo: Fix up Object Assignment (Most be error)
            # self.current_type.define_attribute(node.id, self.context.get_type('Object'))
            self.errors.append(e.text)

    @visitor.when(ast.MethodDeclarationNode)
    def visit(self, node: ast.MethodDeclarationNode):
        name = node.id
        param_names = ['self']
        param_types = [self.current_type]
        for name, typex in node.params:
            param_names.append(name)
            try:
                param_types.append(self.context.get_type(name))
            except SemanticError as e:
                # param_types.append(self.context.get_type('Object'))
                self.errors.append(e.text)
        try:
            return_type = self.context.get_type(node.type)
            self.current_type.define_method(name, param_names, param_types, return_type)
        except SemanticError as e:
            # self.current_type.define_method(name, param_names, param_types, self.context.get_type('Object'))
            self.errors.append(e.text)


class TypeChecker:
    def __init__(self, context: Context, errors: List[str] = []):
        self.context: Context = context
        self.errors: List[str] = errors
        self.current_type: Type = None
        self.current_method: Method = None

    @visitor.on('node')
    def visit(self, node, tabs):
        pass

    @visitor.when(ast.ProgramNode)
    def visit(self, node: ast.ProgramNode, scope: Scope = None):
        if scope is None:
            scope = Scope()

        for elem in node.declarations:
            self.visit(elem, scope)

    @visitor.when(ast.ClassDeclarationNode)
    def visit(self, node: ast.ClassDeclarationNode, scope: Scope):
        self.current_type = self.context.get_type(node.id)
        for elem in node.features:
            self.visit(elem, scope)

    @visitor.when(ast.AttrDeclarationNode)
    def visit(self, node: ast.AttrDeclarationNode, scope: Scope):
        expected_type = self.context.get_type(node.type)
        if node.expr is not None:
            typex = self.visit(node.expr, scope)
            if not typex.conforms_to(expected_type):
                self.errors.append(INCOMPATIBLE_TYPES % (node.type, expected_type.name))
        scope.define_variable(node.id, expected_type)

    @visitor.when(ast.MethodDeclarationNode)
    def visit(self, node: ast.MethodDeclarationNode, scope: Scope):
        self.current_method = self.current_type.get_method(node.id)
        for i, param in enumerate(node.params):
            if scope.is_local(param[0]):
                self.errors.append(LOCAL_ALREADY_DEFINED % (param[0], self.current_method.name))
            else:
                scope.define_variable(param[0], self.context.get_type(param[1]))
        tipo = self.visit(node.body, scope.create_child())
        expected_type = self.context.get_type(node.type)
        if not tipo.conforms_to(expected_type):
            self.errors.append(INCOMPATIBLE_TYPES % (tipo.name, expected_type.name))

    @visitor.when(ast.LetNode)
    def visit(self, node: ast.LetNode, scope: Scope):
        for elem in node.declarations:
            self.visit(elem, scope)
        return self.visit(node.expr, scope)

    @visitor.when(ast.VarDeclarationNode)
    def visit(self, node: ast.VarDeclarationNode, scope: Scope):
        try:
            expected_type = self.context.get_type(node.type)
            if expected_type.name == 'SELF_TYPE':
                expected_type = self.current_type
        except SemanticError as e:
            expected_type = self.context.get_type('Object')
            self.errors.append(e.text)
        if scope.is_local(node.id):
            self.errors.append(LOCAL_ALREADY_DEFINED % (node.id, self.current_method.name))
        else:
            scope.define_variable(node.id, expected_type)
        if node.expr is not None:
            tipo = self.visit(node.expr, scope)
            if not (tipo.conforms_to(expected_type)):
                self.errors.append(INCOMPATIBLE_TYPES % (tipo.name, expected_type.name))

    @visitor.when(ast.AssignNode)
    def visit(self, node: ast.AssignNode, scope: Scope):
        return_type = self.visit(node.expr, scope)
        var = scope.find_variable(node.id)
        if var is None:
            self.errors.append(VARIABLE_NOT_DEFINED % (node.id, self.current_method.name))
        else:
            if not return_type.conforms_to(var.type):
                self.errors.append(INCOMPATIBLE_TYPES % (return_type.name, var.type.name))
        return var.type if var.type.name != 'SELF_TYPE' else self.current_type

    @visitor.when(ast.BlockNode)
    def visit(self, node: ast.BlockNode, scope: Scope):
        return_type = ErrorType()
        for inst in node.expressions:
            return_type = self.visit(inst, scope)
        return return_type

    @visitor.when(ast.ConditionalNode)
    def visit(self, node: ast.ConditionalNode, scope: Scope):
        if_type = self.visit(node.if_expr, scope)
        then_type = self.visit(node.then_expr, scope)
        else_type = self.visit(node.else_expr, scope)
        if if_type.name != 'Bool':
            self.errors.append(INCOMPATIBLE_TYPES % (if_type.name, 'Bool'))
        if then_type.conforms_to(else_type):
            return then_type
        if else_type.conforms_to(then_type):
            return then_type
        return self.context.get_type('Object')

    @visitor.when(ast.WhileNode)
    def visit(self, node: ast.WhileNode, scope: Scope):
        condition = self.visit(node.condition, scope)
        if condition.name != 'Bool':
            self.errors.append(INCOMPATIBLE_TYPES % (condition.name, 'Bool'))
        return self.visit(node.body, scope)

    @visitor.when(ast.SwitchCaseNode)
    def visit(self, node: ast.SwitchCaseNode, scope: Scope):
        self.visit(node.expr, scope)
        for item in node.cases:
            self.visit(item, scope.create_child())
        return self.context.get_type('Object')

    @visitor.when(ast.CaseNode)
    def visit(self, node: ast.CaseNode, scope: Scope):
        try:
            v = scope.define_variable(node.id, self.context.get_type(node.type))
        except SemanticError as e:
            v = scope.define_variable(node.id, self.context.get_type('Object'))
            self.errors.append(e.text)
        self.visit(node.expr, scope)
        return v.type if v.type.name != 'SELF_TYPE' else self.current_type

    @visitor.when(ast.MethodCallNode)
    def visit(self, node: ast.MethodCallNode, scope: Scope):
        typex = self.visit(node.obj, scope)
        try:
            method = typex.get_method(node.id)
        except SemanticError:
            self.errors.append(f'Method "{node.id}" is not defined in {node.type}.')
            method = None
        if method is not None and len(node.args) + 1 != len(method.param_names):
            self.errors.append(WRONG_SIGNATURE % (method.name, typex.name))
        for i, var in enumerate(node.args):
            var_type = self.visit(var, scope)
            if method is not None:
                expected_return_type = method.param_types[i + 1]
                if not var_type.conforms_to(expected_return_type):
                    self.errors.append(INCOMPATIBLE_TYPES % (var_type.name, expected_return_type.name))
        return self.context.get_type('Object') if method is None else method.return_type

    @visitor.when(ast.IntegerNode)
    def visit(self, node: ast.IntegerNode, scope: Scope):
        return IntType()

    @visitor.when(ast.StringNode)
    def visit(self, node: ast.StringNode, scope: Scope):
        return StringType()

    @visitor.when(ast.BooleanNode)
    def visit(self, node: ast.BooleanNode, scope: Scope):
        return BoolType()

    @visitor.when(ast.VariableNode)
    def visit(self, node: ast.VariableNode, scope: Scope):
        var = scope.find_variable(node.lex)
        if var is None:
            var = self.context.get_type('Object')
            self.errors.append(VARIABLE_NOT_DEFINED % (node.lex, self.current_method.name))
        return var.type if var.name != 'SELF_TYPE' else self.current_type

    @visitor.when(ast.InstantiateNode)
    def visit(self, node: ast.InstantiateNode, scope: Scope):
        try:
            return self.context.get_type(node.lex)
        except SemanticError as e:
            self.errors.append(e.text)
            return ErrorType()

    @visitor.when(ast.NegationNode)
    def visit(self, node: ast.NegationNode, scope: Scope):
        return self._check_unary_operation(node, scope, 'not', BoolType())

    @visitor.when(ast.ComplementNode)
    def visit(self, node: ast.ComplementNode, scope: Scope):
        return self._check_unary_operation(node, scope, '~', IntType())

    @visitor.when(ast.IsVoidNode)
    def visit(self, node: ast.IsVoidNode, scope: Scope):
        self.visit(node.obj, scope)
        return BoolType()

    @visitor.when(ast.PlusNode)
    def visit(self, node: ast.PlusNode, scope: Scope):
        return self._check_int_binary_operation(node, scope, '+', IntType())

    @visitor.when(ast.MinusNode)
    def visit(self, node: ast.MinusNode, scope: Scope):
        return self._check_int_binary_operation(node, scope, '-', IntType())

    @visitor.when(ast.StarNode)
    def visit(self, node: ast.StarNode, scope: Scope):
        return self._check_int_binary_operation(node, scope, '*', IntType())

    @visitor.when(ast.DivNode)
    def visit(self, node: ast.DivNode, scope: Scope):
        return self._check_int_binary_operation(node, scope, '/', IntType())

    @visitor.when(ast.LessEqualNode)
    def visit(self, node: ast.LessEqualNode, scope: Scope):
        return self._check_int_binary_operation(node, scope, '<=', BoolType())

    @visitor.when(ast.LessThanNode)
    def visit(self, node: ast.LessThanNode, scope: Scope):
        return self._check_int_binary_operation(node, scope, '<', BoolType())

    @visitor.when(ast.EqualNode)
    def visit(self, node: ast.EqualNode, scope: Scope):
        self.visit(node.left, scope)
        self.visit(node.right, scope)
        return BoolType()

    def _check_int_binary_operation(self, node: ast.BinaryNode, scope: Scope, operation: str, return_type: Type):
        left_type = self.visit(node.left, scope)
        right_type = self.visit(node.right, scope)

        if left_type == right_type == IntType():
            return return_type
        self.errors.append(INVALID_BINARY_OPERATION % (operation, left_type.name, right_type.name))
        return ErrorType()

    def _check_unary_operation(self, node: ast.UnaryNode, scope: Scope, operation: str, expected_type: Type):
        typex = self.visit(node.obj, scope)
        if typex == expected_type:
            return typex
        self.errors.append(INVALID_UNARY_OPERATION % (operation, typex.name))
        return ErrorType()


class InferenceTypeChecker:
    def __init__(self, context: Context, errors: List[str] = []):
        self.context: Context = context
        self.errors: List[str] = errors
        self.current_type: Type = None
        self.current_method: Method = None

    @visitor.on('node')
    def visit(self, node, tabs):
        pass

    @visitor.when(ast.ProgramNode)
    def visit(self, node: ast.ProgramNode, scope: Scope = None):
        pass

    @visitor.when(ast.ClassDeclarationNode)
    def visit(self, node: ast.ClassDeclarationNode, scope: Scope):
        pass

    @visitor.when(ast.AttrDeclarationNode)
    def visit(self, node: ast.AttrDeclarationNode, scope: Scope):
        pass

    @visitor.when(ast.MethodDeclarationNode)
    def visit(self, node: ast.MethodDeclarationNode, scope: Scope):
        pass

    @visitor.when(ast.LetNode)
    def visit(self, node: ast.LetNode, scope: Scope):
        pass

    @visitor.when(ast.VarDeclarationNode)
    def visit(self, node: ast.VarDeclarationNode, scope: Scope):
        pass

    @visitor.when(ast.AssignNode)
    def visit(self, node: ast.AssignNode, scope: Scope):
        pass

    @visitor.when(ast.BlockNode)
    def visit(self, node: ast.BlockNode, scope: Scope):
        pass

    @visitor.when(ast.ConditionalNode)
    def visit(self, node: ast.ConditionalNode, scope: Scope):
        pass

    @visitor.when(ast.WhileNode)
    def visit(self, node: ast.WhileNode, scope: Scope):
        pass

    @visitor.when(ast.SwitchCaseNode)
    def visit(self, node: ast.SwitchCaseNode, scope: Scope):
        pass

    @visitor.when(ast.CaseNode)
    def visit(self, node: ast.CaseNode, scope: Scope):
        pass

    @visitor.when(ast.MethodCallNode)
    def visit(self, node: ast.MethodCallNode, scope: Scope):
        pass

    @visitor.when(ast.IntegerNode)
    def visit(self, node: ast.IntegerNode, scope: Scope):
        pass

    @visitor.when(ast.StringNode)
    def visit(self, node: ast.StringNode, scope: Scope):
        pass

    @visitor.when(ast.BooleanNode)
    def visit(self, node: ast.BooleanNode, scope: Scope):
        pass

    @visitor.when(ast.VariableNode)
    def visit(self, node: ast.VariableNode, scope: Scope):
        pass

    @visitor.when(ast.InstantiateNode)
    def visit(self, node: ast.InstantiateNode, scope: Scope):
        pass

    @visitor.when(ast.NegationNode)
    def visit(self, node: ast.NegationNode, scope: Scope):
        pass

    @visitor.when(ast.ComplementNode)
    def visit(self, node: ast.ComplementNode, scope: Scope):
        pass

    @visitor.when(ast.IsVoidNode)
    def visit(self, node: ast.IsVoidNode, scope: Scope):
        pass

    @visitor.when(ast.PlusNode)
    def visit(self, node: ast.PlusNode, scope: Scope):
        pass

    @visitor.when(ast.MinusNode)
    def visit(self, node: ast.MinusNode, scope: Scope):
        pass

    @visitor.when(ast.StarNode)
    def visit(self, node: ast.StarNode, scope: Scope):
        pass

    @visitor.when(ast.DivNode)
    def visit(self, node: ast.DivNode, scope: Scope):
        pass

    @visitor.when(ast.LessEqualNode)
    def visit(self, node: ast.LessEqualNode, scope: Scope):
        pass

    @visitor.when(ast.LessThanNode)
    def visit(self, node: ast.LessThanNode, scope: Scope):
        pass

    @visitor.when(ast.EqualNode)
    def visit(self, node: ast.EqualNode, scope: Scope):
        pass


class Executor:
    def __init__(self, context: Context, errors: List[str] = []):
        self.context: Context = context
        self.errors: List[str] = errors
        self.current_type: Type = None
        self.current_method: Method = None

    @visitor.on('node')
    def visit(self, node, tabs):
        pass

    @visitor.when(ast.ProgramNode)
    def visit(self, node: ast.ProgramNode, scope: Scope = None):
        pass

    @visitor.when(ast.ClassDeclarationNode)
    def visit(self, node: ast.ClassDeclarationNode, scope: Scope):
        pass

    @visitor.when(ast.AttrDeclarationNode)
    def visit(self, node: ast.AttrDeclarationNode, scope: Scope):
        pass

    @visitor.when(ast.MethodDeclarationNode)
    def visit(self, node: ast.MethodDeclarationNode, scope: Scope):
        pass

    @visitor.when(ast.LetNode)
    def visit(self, node: ast.LetNode, scope: Scope):
        pass

    @visitor.when(ast.VarDeclarationNode)
    def visit(self, node: ast.VarDeclarationNode, scope: Scope):
        pass

    @visitor.when(ast.AssignNode)
    def visit(self, node: ast.AssignNode, scope: Scope):
        pass

    @visitor.when(ast.BlockNode)
    def visit(self, node: ast.BlockNode, scope: Scope):
        pass

    @visitor.when(ast.ConditionalNode)
    def visit(self, node: ast.ConditionalNode, scope: Scope):
        pass

    @visitor.when(ast.WhileNode)
    def visit(self, node: ast.WhileNode, scope: Scope):
        pass

    @visitor.when(ast.SwitchCaseNode)
    def visit(self, node: ast.SwitchCaseNode, scope: Scope):
        pass

    @visitor.when(ast.CaseNode)
    def visit(self, node: ast.CaseNode, scope: Scope):
        pass

    @visitor.when(ast.MethodCallNode)
    def visit(self, node: ast.MethodCallNode, scope: Scope):
        pass

    @visitor.when(ast.IntegerNode)
    def visit(self, node: ast.IntegerNode, scope: Scope):
        pass

    @visitor.when(ast.StringNode)
    def visit(self, node: ast.StringNode, scope: Scope):
        pass

    @visitor.when(ast.BooleanNode)
    def visit(self, node: ast.BooleanNode, scope: Scope):
        pass

    @visitor.when(ast.VariableNode)
    def visit(self, node: ast.VariableNode, scope: Scope):
        pass

    @visitor.when(ast.InstantiateNode)
    def visit(self, node: ast.InstantiateNode, scope: Scope):
        pass

    @visitor.when(ast.NegationNode)
    def visit(self, node: ast.NegationNode, scope: Scope):
        pass

    @visitor.when(ast.ComplementNode)
    def visit(self, node: ast.ComplementNode, scope: Scope):
        pass

    @visitor.when(ast.IsVoidNode)
    def visit(self, node: ast.IsVoidNode, scope: Scope):
        pass

    @visitor.when(ast.PlusNode)
    def visit(self, node: ast.PlusNode, scope: Scope):
        pass

    @visitor.when(ast.MinusNode)
    def visit(self, node: ast.MinusNode, scope: Scope):
        pass

    @visitor.when(ast.StarNode)
    def visit(self, node: ast.StarNode, scope: Scope):
        pass

    @visitor.when(ast.DivNode)
    def visit(self, node: ast.DivNode, scope: Scope):
        pass

    @visitor.when(ast.LessEqualNode)
    def visit(self, node: ast.LessEqualNode, scope: Scope):
        pass

    @visitor.when(ast.LessThanNode)
    def visit(self, node: ast.LessThanNode, scope: Scope):
        pass

    @visitor.when(ast.EqualNode)
    def visit(self, node: ast.EqualNode, scope: Scope):
        pass