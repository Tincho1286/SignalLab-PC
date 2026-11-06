"""Constant-coefficient initial-value equations, independently of Qt."""
import sympy as sp


def solve(request):
    from .symbolic import T,N,S,Z,W
    from .scalar_expression import exact_constant
    from .expression_definition import prepare
    expression=request["expression"]
    from .procedure import step
    coefficients=[exact_constant(value,parameters=True) for value in request["coefficients"]]
    while coefficients and coefficients[-1] == 0: coefficients.pop()
    if not coefficients:raise ValueError("La ecuación no determina y(t): todos sus coeficientes son cero.")
    initial=[exact_constant(value,parameters=True) for value in request["initial"]]
    order=len(coefficients)-1
    if len(initial)!=order: raise ValueError('La EDO de orden '+str(order)+' requiere '+str(order)+' datos iniciales en 0−, desde y(0−) hasta la derivada de orden '+str(order-1)+'. Se recibieron '+str(len(initial))+'.')
    definition=prepare(expression,T,'continuous',(sp.S.Zero,sp.oo),conditions=request.get('input_conditions',()),support_kind='unilateral_0minus')
    # Algebraic equations hold at the assigned points too. Only actual
    # integral/Laplace paths may ignore isolated ordinary point values.
    forcing_expression=definition.expression if order==0 else definition.integral_expression()
    if forcing_expression.has(N,S,Z,W):raise ValueError('La entrada de la EDO debe estar expresada en t.')
    if order==0:
        result=sp.cancel(forcing_expression/coefficients[0])
        return {'forcing_used':str(forcing_expression),'input_definition':definition.metadata(),'calculation_notes':list(definition.extensions),
            'operation':'Ecuación algebraica sin derivadas','procedure':[step('Despeje sin derivadas','División por el coeficiente a₀',str(coefficients[0])+'*y(t) = '+str(forcing_expression),'y(t) = '+str(result),conditions='t >= 0; '+str(coefficients[0])+' != 0',source='ode_equations.solve')],'order':0,'result':str(result),'output_variable':'t',
            'condition':str(sp.And(T>=0,sp.Ne(coefficients[0],0))),
            'Y(s)':str(sp.LaplaceTransform(forcing_expression,T,S)/coefficients[0]),
            'forcing_convergence':'No es necesaria una transformada para despejar esta ecuación.',
            'scope':'t >= 0. Sin términos de derivadas: y(t)=f(t)/a₀; no hay condiciones iniciales independientes.',
            'evaluated':not result.has(sp.Integral,sp.Limit,sp.nan,sp.zoo,sp.oo)}
    from .impulse_pairs import unilateral_laplace
    forcing, plane, condition=unilateral_laplace(forcing_expression,T,S)
    polynomial=sum(value*S**j for j,value in enumerate(coefficients))
    correction=sum(coefficients[j]*sum(S**(j-1-k)*initial[k] for k in range(j)) for j in range(1,order+1))
    transformed=sp.cancel((forcing+correction)/polynomial)
    result=sp.inverse_laplace_transform(transformed,S,T)
    initial_transform=sp.cancel(correction/polynomial)
    input_transform=sp.cancel(forcing/polynomial)
    steps=[step('Transformada de la entrada','Laplace unilateral desde 0−',forcing_expression,forcing,conditions='Re(s) > '+str(plane)+'; '+str(condition),source='impulse_pairs.unilateral_laplace'),
           step('Incorporar las condiciones iniciales','Identidad de las derivadas unilaterales',str(polynomial)+'*Y(s) - ('+str(correction)+') = '+str(forcing),str(polynomial)+'*Y(s) = '+str(forcing+correction),conditions='Valores iniciales en 0−; '+str(coefficients[-1])+' != 0',source='ode_equations.solve'),
           step('Despejar Y(s)','División por el polinomio del operador',str(polynomial)+'*Y(s) = '+str(forcing+correction),'Y(s) = '+str(transformed),conditions=sp.Ne(polynomial,0),source='ode_equations.solve'),
           step('Volver al tiempo','Laplace inversa causal',transformed,result,conditions='t >= 0',interpretation='Se almacena la salida de la inversa. El motor no registra sus manipulaciones internas.',source='sympy.inverse_laplace_transform')]

    return {"forcing_used":str(forcing_expression),"input_definition":definition.metadata(),"calculation_notes":list(definition.extensions),"operation":"EDO lineal de coeficientes constantes", "procedure":steps,"initial_convention":"0-","initial_transform":str(initial_transform),"input_transform":str(input_transform),"operator_polynomial":str(polynomial),"initial_correction":str(correction),"forcing_transform":str(forcing),"order":order, "result":str(result), "Y(s)":str(transformed),
            "forcing_convergence":f"Re(s) > {plane}; {condition}",
            "scope":"t >= 0; datos iniciales en 0−. Un impulso en el origen puede cambiar los límites en 0+. La historia anterior no se reconstruye; a0*y+a1*y'+...=f(t)",
            "output_variable":"t", "condition":str(sp.And(T>=0,sp.Ne(coefficients[-1],0))),
            "evaluated":not result.has(sp.InverseLaplaceTransform,sp.LaplaceTransform,sp.Integral,sp.Limit,sp.nan,sp.zoo,sp.oo)}
