import ast

def verify_allocated(st, code, registers, sources):
    statements = []
    carried = [f'i{j}' for j in range(st.n)]
    for source in sources:
        fn = ast.parse(source).body[0]
        assert isinstance(fn, ast.FunctionDef)
        assert [a.arg for a in fn.args.args] == carried
        assert isinstance(fn.body[-1], ast.Return) and isinstance(fn.body[-1].value, ast.Tuple)
        statements.extend(fn.body[:-1])
        carried = [e.id for e in fn.body[-1].value.elts]
    assert carried == st.outs and len(statements) == len(code) == st.ops
    held = {j: f'i{j}' for j in range(st.n)}
    for syntax, named, allocated in zip(statements, st.lines, code):
        name, *operands = named
        assigned, destination, *register_operands = allocated
        assert assigned == name and len(operands) == len(register_operands)
        assert isinstance(syntax, ast.Assign) and len(syntax.targets) == 1 and (syntax.targets[0].id == name)
        op, immediate = st.opsym[name]
        assert not immediate
        if op == '?':
            assert len(operands) == 3
            s, a, b = operands
            expression = f'{b}^({s}&({a}^{b}))'
        else:
            assert op in ('^', '&', '|') and len(operands) == 2
            expression = operands[0] + op + operands[1]
        assert ast.dump(syntax.value) == ast.dump(ast.parse(expression, mode='eval').body)
        for operand, register in zip(operands, register_operands):
            assert operand == '0' and register == -1 or held.get(register) == operand
        assert 0 <= destination < registers
        held[destination] = name
    assert [held[j] for j in range(st.n)] == st.outs
    return len(code)
