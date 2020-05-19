import semantics.utils.astnodes as ast
import semantics.visitor as visitor


class CodeBuilder:
    @visitor.on('node')
    def visit(self, node, tabs):
        pass

    @visitor.when(ast.ProgramNode)
    def visit(self, node: ast.ProgramNode, tabs: int = 0):
        return '\n\n'.join(self.visit(child, tabs) for child in node.declarations)

    @visitor.when(ast.ClassDeclarationNode)
    def visit(self, node: ast.ClassDeclarationNode, tabs: int = 0):
        parent = '' if node.parent is None else f"inherits {node.parent} "
        return (f'class {node.id} {parent}{{\n' +
                '\n\n'.join(self.visit(child, tabs + 1) for child in node.features) +
                '\n}')

    @visitor.when(ast.AttrDeclarationNode)
    def visit(self, node: ast.AttrDeclarationNode, tabs: int = 0):
        expr = f' <- {self.visit(node.expr, tabs)}' if node.expr is not None else ''
        return '\t' * tabs + f'{node.id}: {node.type}{expr};'

    @visitor.when(ast.MethodDeclarationNode)
    def visit(self, node: ast.MethodDeclarationNode, tabs: int = 0):
        params = ', '.join(': '.join(param) for param in node.params)
        ans = '\t' * tabs + f'{node.id} ({params}): {node.return_type}'
        body = self.visit(node.body, tabs + 1)
        return f'{ans} {{\n{body}\n\t}};'

    @visitor.when(ast.LetNode)
    def visit(self, node: ast.LetNode, tabs: int = 0):
        declarations = '\n'.join(self.visit(declaration, 0) for declaration in node.declarations)
        return '\t' * tabs + f'let {declarations} in \n{self.visit(node.expr, tabs + 1)}'

    @visitor.when(ast.VarDeclarationNode)
    def visit(self, node: ast.VarDeclarationNode, tabs: int = 0):
        if node.expr is not None:
            return f'{node.id}: {node.type} <- {self.visit(node.expr)}'
        else:
            return f'{node.id} : {node.type}'

    @visitor.when(ast.AssignNode)
    def visit(self, node: ast.AssignNode, tabs: int = 0):
        return '\t' * tabs + f'{node.id} <- {self.visit(node.expr)}'

    @visitor.when(ast.BlockNode)
    def visit(self, node: ast.BlockNode, tabs: int = 0):
        body = ';\n'.join(self.visit(child, tabs + 1) for child in node.expressions)
        return '\t' * tabs + f'{{\n{body};\n' + '\t' * tabs + '}'

    @visitor.when(ast.ConditionalNode)
    def visit(self, node: ast.ConditionalNode, tabs: int = 0):
        ifx = self.visit(node.if_expr)
        then = self.visit(node.then_expr, tabs + 1)
        elsex = self.visit(node.else_expr, tabs + 1)

        return ('\t' * tabs + f'if {ifx}\n' +
                '\t' * tabs + f'then\n{then}\n' +
                '\t' * tabs + f'else\n{elsex}\n' +
                '\t' * tabs + 'fi')

    @visitor.when(ast.WhileNode)
    def visit(self, node: ast.WhileNode, tabs: int = 0):
        condition = self.visit(node.condition, 0)
        body = self.visit(node.body, tabs + 1)

        return '\t' * tabs + f'while {condition} loop\n {body}\n' + '\t' * tabs + 'pool'

    @visitor.when(ast.SwitchCaseNode)
    def visit(self, node: ast.SwitchCaseNode, tabs: int = 0):
        expr = self.visit(node.expr)
        cases = '\n'.join(self.visit(case, tabs + 1) for case in node.cases)

        return '\t' * tabs + f'case {expr} of \n{cases}\n' + '\t' * tabs + 'esac'

    @visitor.when(ast.CaseNode)
    def visit(self, node: ast.CaseNode, tabs: int = 0):
        expr = self.visit(node.expr, tabs + 1)
        return '\t' * tabs + f'{node.id} : {node.type} =>\n{expr};'

    @visitor.when(ast.MethodCallNode)
    def visit(self, node: ast.MethodCallNode, tabs: int = 0):
        obj = f'{self.visit(node.obj, 0)}.' if node.obj is not None else ''
        return '\t' * tabs + f'{obj}{node.id}({", ".join(self.visit(arg, 0) for arg in node.args)})'

    @visitor.when(ast.BinaryNode)
    def visit(self, node: ast.BinaryNode, tabs: int = 0):
        left = self.visit(node.left) if isinstance(node.left, ast.BinaryNode) else self.visit(node.left, tabs)
        right = self.visit(node.right)
        return f'{left} {node.operation} {right}'

    @visitor.when(ast.AtomicNode)
    def visit(self, node: ast.AtomicNode, tabs: int = 0):
        return '\t' * tabs + f'{node.lex}'

    @visitor.when(ast.InstantiateNode)
    def visit(self, node: ast.InstantiateNode, tabs: int = 0):
        return '\t' * tabs + f'new {node.lex}'


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
        ans = '\t' * tabs + f'\\__FuncDeclarationNode: {node.id}({params}) : {node.return_type} -> <body>'
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
