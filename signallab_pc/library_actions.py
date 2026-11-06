"""Load a library example through existing tools; never calculate automatically."""
def apply_example(window,example):
    from .workspaces import ROUTES
    route=ROUTES[tuple(example['tool'])];request=example['request']
    if 'system' in example:
        from .filters import Transfer
        window.send_system(Transfer(**example['system']),None,route)
        return
    window.open_tool(route);panel=window.pages[route].panel;operation=request['operation']
    if operation=='ode':
        panel.operation.setCurrentIndex(4);panel.coefficients.setText(', '.join(request['coefficients']));panel.initial.setText(', '.join(request['initial']))
    elif operation=='difference_equation':
        panel.coefficients.setText(', '.join(request['coefficients']));panel.rest.setChecked(request.get('rest',True));panel.initial.setText(', '.join(request.get('initial',[])));panel.start.setText(str(request.get('start',0)));panel.count.setText(str(request.get('count',24)))
    elif route[1]=='transform_lab':
        panel.mode.setCurrentIndex(1 if operation in ('z_inverse_expression','inverse_laplace') else 0)
        if route[2]=='laplace':panel.load_laplace_context(request)
        else:
            panel.roc.setCurrentIndex({'right':0,'left':1,'radius':2}[request.get('roc','right')]);panel.include_samples.setChecked(request.get('include_samples',False))
    panel.expression.setText(request['expression'])
    window.statusBar().showMessage('Datos del ejemplo cargados. Revisá las entradas y presioná Calcular.')
