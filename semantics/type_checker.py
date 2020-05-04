from typing import List

import semantics.astnodes as ast
import semantics.semantic_errors as err
import semantics.visitor as visitor
from semantics.scope import Context, SemanticError, Type, Method, Scope, ErrorType


class TypeChecker:
    def __init__(self, context: Context, errors: List[str]):
        self.context: Context = context
        self.errors: List[str] = errors
        self.current_type: Type = None
        self.current_method: Method = None

    @visitor.on('node')
    def visit(self, node, scope):
        pass

    @visitor.when(ast.ProgramNode)
    def visit(self, node: ast.ProgramNode, scope: Scope = None):
        if scope is None:
            scope = Scope()

        for elem in node.declarations:
            self.visit(elem, scope.create_child())

        return scope

    @visitor.when(ast.ClassDeclarationNode)
    def visit(self, node: ast.ClassDeclarationNode, scope: Scope):
        self.current_type = self.context.get_type(node.id)

        attrs = [feature for feature in node.features if isinstance(feature, ast.AttrDeclarationNode)]
        methods = [feature for feature in node.features if isinstance(feature, ast.MethodDeclarationNode)]

        for attr in attrs:
            self.visit(attr, scope)

        for method in methods:
            self.visit(method, scope.create_child())

    @visitor.when(ast.AttrDeclarationNode)
    def visit(self, node: ast.AttrDeclarationNode, scope: Scope):
        if node.id == 'self':
            self.errors.append(err.SELF_INVALID_ATTRIBUTE_ID)

        attr_type = self.context.get_type(node.type)

        if node.expr is not None:
            expr_type = self.visit(node.expr, scope.create_child())
            if not expr_type.conforms_to(attr_type):
                self.errors.append(err.INCOMPATIBLE_TYPES % (expr_type.name, attr_type.name))

        scope.define_variable(node.id, attr_type)

    @visitor.when(ast.MethodDeclarationNode)
    def visit(self, node: ast.MethodDeclarationNode, scope: Scope):
        self.current_method = self.current_type.get_method(node.id)

        # Defining parameters in the scope. Parameters can hide the attribute declaration, that's why we are not
        # checking  if there is defined, instead we are checking for local declaration
        for i, (name, expr_body_type) in enumerate(node.params):
            if not scope.is_local(name):
                scope.define_variable(name, self.context.get_type(expr_body_type))
            else:
                self.errors.append(err.LOCAL_ALREADY_DEFINED % (name, self.current_method.name))

        return_type = self.context.get_type(node.return_type)

        expr_body_type = self.visit(node.body, scope)

        if not expr_body_type.conforms_to(return_type):
            self.errors.append(err.INCOMPATIBLE_TYPES % (expr_body_type.name, return_type.name))

    @visitor.when(ast.LetNode)
    def visit(self, node: ast.LetNode, scope: Scope):
        for elem in node.declarations:
            self.visit(elem, scope)
        return self.visit(node.expr, scope.create_child())

    @visitor.when(ast.VarDeclarationNode)
    def visit(self, node: ast.VarDeclarationNode, scope: Scope):
        try:
            var_static_type = self.context.get_type(node.type)
        except SemanticError as e:
            var_static_type = ErrorType()
            self.errors.append(e.text)

        if scope.is_local(node.id):
            self.errors.append(err.LOCAL_ALREADY_DEFINED % (node.id, self.current_method.name))
        else:
            scope.define_variable(node.id, var_static_type)

        if node.expr is not None:
            expr_type = self.visit(node.expr, scope)
            if not (expr_type.conforms_to(var_static_type)):
                self.errors.append(err.INCOMPATIBLE_TYPES % (expr_type.name, var_static_type.name))

        return var_static_type

    @visitor.when(ast.AssignNode)
    def visit(self, node: ast.AssignNode, scope: Scope):
        expr_type = self.visit(node.expr, scope)
        var_info = scope.find_variable(node.id)
        if var_info is None:
            self.errors.append(err.VARIABLE_NOT_DEFINED % (node.id, self.current_method.name))
            return ErrorType()
        else:
            if not expr_type.conforms_to(var_info.type):
                self.errors.append(err.INCOMPATIBLE_TYPES % (expr_type.name, var_info.type.name))
            return var_info.type

    @visitor.when(ast.BlockNode)
    def visit(self, node: ast.BlockNode, scope: Scope):
        return_type = ErrorType()
        for expr in node.expressions:
            return_type = self.visit(expr, scope)
        return return_type

    @visitor.when(ast.ConditionalNode)
    def visit(self, node: ast.ConditionalNode, scope: Scope):
        if_type = self.visit(node.if_expr, scope)
        then_type = self.visit(node.then_expr, scope)
        else_type = self.visit(node.else_expr, scope)
        if if_type != self.context.get_type('Bool'):
            self.errors.append(err.INCOMPATIBLE_TYPES % (if_type.name, 'Bool'))
        return then_type.join(else_type)

    @visitor.when(ast.WhileNode)
    def visit(self, node: ast.WhileNode, scope: Scope):
        condition = self.visit(node.condition, scope)
        if condition != self.context.get_type('Bool'):
            self.errors.append(err.INCOMPATIBLE_TYPES % (condition.name, 'Bool'))

        self.visit(node.body)
        return self.context.get_type('Object')

    @visitor.when(ast.SwitchCaseNode)
    def visit(self, node: ast.SwitchCaseNode, scope: Scope):
        self.visit(node.expr, scope)
        return Type.multi_join([self.visit(case, scope.create_child()) for case in node.cases])

    @visitor.when(ast.CaseNode)
    def visit(self, node: ast.CaseNode, scope: Scope):
        try:
            scope.define_variable(node.id, self.context.get_type(node.type))
        except SemanticError as e:
            scope.define_variable(node.id, ErrorType())
            self.errors.append(e.text)

        return self.visit(node.expr, scope)

    @visitor.when(ast.MethodCallNode)
    def visit(self, node: ast.MethodCallNode, scope: Scope):
        obj_type = self.visit(node.obj, scope)

        if node.type is not None:
            try:
                ancestor_type = self.context.get_type(node.type)
            except SemanticError as e:
                ancestor_type = ErrorType()
                self.errors.append(e.text)

            if not obj_type.conforms_to(ancestor_type):
                self.errors.append(err.INVALID_ANCESTOR % (obj_type.name, ancestor_type.name))
        else:
            ancestor_type = obj_type

        try:
            method = ancestor_type.get_method(node.id)
        except SemanticError as e:
            self.errors.append(e.text)
            for arg in node.args:
                self.visit(arg, scope)
            return ErrorType()

        if len(node.args) + 1 != len(method.param_names):
            self.errors.append(err.WRONG_SIGNATURE % (method.name, obj_type.name))

        if not obj_type.conforms_to(method.param_types[0]):
            self.errors.append(err.INCOMPATIBLE_TYPES % (obj_type.name, method.param_types[0].name))

        for i, arg in enumerate(node.args, 1):
            arg_type = self.visit(arg, scope)
            if not arg_type.conforms_to(method.param_types[i]):
                self.errors.append(err.INCOMPATIBLE_TYPES % (arg_type.name, method.param_types[i].name))

        return method.return_type

    @visitor.when(ast.IntegerNode)
    def visit(self, node: ast.IntegerNode, scope: Scope):
        return self.context.get_type('Int')

    @visitor.when(ast.StringNode)
    def visit(self, node: ast.StringNode, scope: Scope):
        return self.context.get_type('String')

    @visitor.when(ast.BooleanNode)
    def visit(self, node: ast.BooleanNode, scope: Scope):
        return self.context.get_type('Bool')

    @visitor.when(ast.VariableNode)
    def visit(self, node: ast.VariableNode, scope: Scope):
        variable = scope.find_variable(node.lex)
        if variable is None:
            self.errors.append(err.VARIABLE_NOT_DEFINED % (node.lex, self.current_method.name))
            return ErrorType()
        return variable.type

    @visitor.when(ast.InstantiateNode)
    def visit(self, node: ast.InstantiateNode, scope: Scope):
        try:
            return self.context.get_type(node.lex)
        except SemanticError as e:
            self.errors.append(e.text)
            return ErrorType()

    @visitor.when(ast.NegationNode)
    def visit(self, node: ast.NegationNode, scope: Scope):
        return self._check_unary_operation(node, scope, 'not', self.context.get_type('Bool'))

    @visitor.when(ast.ComplementNode)
    def visit(self, node: ast.ComplementNode, scope: Scope):
        return self._check_unary_operation(node, scope, '~', self.context.get_type('Int'))

    @visitor.when(ast.IsVoidNode)
    def visit(self, node: ast.IsVoidNode, scope: Scope):
        self.visit(node.expr, scope)
        return self.context.get_type('Bool')

    @visitor.when(ast.PlusNode)
    def visit(self, node: ast.PlusNode, scope: Scope):
        return self._check_int_binary_operation(node, scope, '+', self.context.get_type('Int'))

    @visitor.when(ast.MinusNode)
    def visit(self, node: ast.MinusNode, scope: Scope):
        return self._check_int_binary_operation(node, scope, '-', self.context.get_type('Int'))

    @visitor.when(ast.StarNode)
    def visit(self, node: ast.StarNode, scope: Scope):
        return self._check_int_binary_operation(node, scope, '*', self.context.get_type('Int'))

    @visitor.when(ast.DivNode)
    def visit(self, node: ast.DivNode, scope: Scope):
        return self._check_int_binary_operation(node, scope, '/', self.context.get_type('Int'))

    @visitor.when(ast.LessEqualNode)
    def visit(self, node: ast.LessEqualNode, scope: Scope):
        return self._check_int_binary_operation(node, scope, '<=', self.context.get_type('Bool'))

    @visitor.when(ast.LessThanNode)
    def visit(self, node: ast.LessThanNode, scope: Scope):
        return self._check_int_binary_operation(node, scope, '<', self.context.get_type('Bool'))

    @visitor.when(ast.EqualNode)
    def visit(self, node: ast.EqualNode, scope: Scope):
        self.visit(node.left, scope)
        self.visit(node.right, scope)
        return self.context.get_type('Bool')

    def _check_int_binary_operation(self, node: ast.BinaryNode, scope: Scope, operation: str, return_type: Type):
        left_type = self.visit(node.left, scope)
        right_type = self.visit(node.right, scope)

        if left_type == right_type == self.context.get_type('Int'):
            return return_type
        self.errors.append(err.INVALID_BINARY_OPERATION % (operation, left_type.name, right_type.name))
        return ErrorType()

    def _check_unary_operation(self, node: ast.UnaryNode, scope: Scope, operation: str, expected_type: Type):
        typex = self.visit(node.expr, scope)
        if typex == expected_type:
            return typex
        self.errors.append(err.INVALID_UNARY_OPERATION % (operation, typex.name))
        return ErrorType()