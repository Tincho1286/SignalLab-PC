"""Generated reference cases: exact laws, original definitions and known solutions."""
import random

SEED=20261103


def catalog(seed=SEED):
    rng=random.Random(seed);cases=[]
    def add(group,**parameters):cases.append({'id':group+'-'+str(sum(c['group']==group for c in cases)+1).zfill(3),'group':group,'parameters':parameters})
    for exponent in (16,20,40,80):
        add('exact_scalars',exponent=exponent,offset=rng.randint(1,9),divisor=rng.randint(2,9))
        add('exact_scalars',exponent=exponent,offset=-rng.randint(1,9),divisor=rng.randint(2,9))
    widths=['3/10',*rng.sample(['1/5','2/7','3/8','5/7','3/2','-2/5'],2)]
    delays=['4','1/2',*rng.sample(['-5','-3','-1','0','2','7','7/3'],2)]
    for width in widths:
        for delay in delays:add('sampled_formulas',width=width,delay=delay,gain=rng.choice(['-2','1/3','1+i']))
    for delay in (-2,3):
        for power in (0,1,2):add('z_properties',delay=delay,power=power,ratio=rng.choice(['1/2','-1/3','2/3']))
    for delay in (-2,0,4):
        for power in (1,2,3):add('dtft_convergence',delay=delay,power=power,gain=rng.choice([-2,1,3]))
    for sign in (-1,1):
        for order in (1,2):add('filter_limits',domain='digital',sign=sign,order=order,base=rng.choice([.25,.5,-.5,.75]))
    for order in (1,2,3):add('filter_limits',domain='analog',sign=0,order=order,base=rng.choice([.5,2.,3.]))
    for origin in (-4,2,7):
        for size in (3,5):add('fourier_definitions',origin=origin,real=[rng.randint(-4,4) for _ in range(size)],imag=[rng.randint(-3,3) for _ in range(size)])
    for start in (-2,3):
        for ratio in ('1/2','-1/4'):add('equation_solution',start=start,ratio=ratio,a0=rng.choice([2,3]),initial=rng.choice([-2,2,3]))
    for mode in ('factor_roots','domains','euler','matrix'):
        add('cas_algebra',mode=mode,a=rng.randint(2,5),b=rng.randint(1,3),left=rng.randint(-4,0),right=rng.randint(1,5))
    return cases


def check(case):
    import numpy as np
    import sympy as sp
    from numpy.testing import assert_allclose
    from signallab_pc.symbolic import execute,parse,N,Z,W
    from signallab_pc.cas_engine import restore
    from signallab_pc.model import Signal
    p=case['parameters'];group=case['group']
    def formula(result):
        assert result.get('evaluated'),('Expected a calculated expression',result.get('calculation_status'),result.get('result'))
        return parse(result['branches'][0]['expression'] if result.get('branches') else result['result'])
    if group=='exact_scalars':
        from signallab_pc.scalar_expression import exact_constant
        q,k,d=p['exponent'],p['offset'],p['divisor']
        for text in (f'(10^{q}+({k}))-10^{q}',f'(({k})/{d})*{d}',f'(({k})*pi)/pi'):
            assert sp.simplify(exact_constant(text)-k)==0,text
        return 'Exact cancellation, rational arithmetic and constant equivalence'
    if group=='sampled_formulas':
        from signallab_pc.engine import evaluate_expression
        a,d,g=p['width'],p['delay'],p['gain'];axis=np.arange(-5,9)
        sources=[f'({g})*sin(({a})*pi*(n-({d})))/(pi*(n-({d})))',f'({g})*({a})*sinc(({a})*(n-({d})))']
        expected=complex(sp.N(parse(g)))*float(sp.Rational(a))*np.sinc(float(sp.Rational(a))*(axis-float(sp.Rational(d))))
        for source in sources:assert_allclose(evaluate_expression(source,axis),expected,atol=3e-14,rtol=2e-13)
        return 'Equivalent normalized sinc and completed samples against direct numerical definition'
    if group=='z_properties':
        d,k,r=p['delay'],p['power'],p['ratio'];source=f'(n-({d}))^{k}*({r})^(n-({d}))'
        result=execute(dict(operation='z_expression',expression=source,lower=str(d),upper='oo'));actual=formula(result)
        q=sp.Rational(r)/Z;moments=[1/(1-q),q/(1-q)**2,q*(1+q)/(1-q)**3];want=Z**(-d)*moments[k]
        for z in (2+sp.I/3,-2+sp.I/2):assert_allclose(complex(actual.subs(Z,z).evalf(18)),complex(want.subs(Z,z).evalf(18)),atol=2e-13,rtol=3e-13)
        return 'Shift and polynomial-weight laws against geometric moments'
    if group=='dtft_convergence':
        d,k,g=p['delay'],p['power'],p['gain'];source=f'({g})/(n-({d}))^{k}'
        result=execute(dict(operation='dtft_expression',expression=source,lower=str(d+1),upper='oo'));actual=formula(result)
        q=sp.exp(-sp.I*W);want=g*sp.exp(-sp.I*W*d)*(-sp.log(1-q) if k==1 else sp.polylog(k,q))
        for w in (sp.pi/4,sp.pi/2,-sp.pi/2):assert_allclose(complex(actual.subs(W,w).evalf(18)),complex(want.subs(W,w).evalf(18)),atol=3e-13,rtol=3e-13)
        condition=sp.simplify(parse(result.get('condition','True')).subs(W,0))
        assert condition is (sp.false if k==1 else sp.true),(source,result.get('condition'))
        if k>1:assert_allclose(complex(actual.subs(W,0).evalf(18)),complex((g*sp.zeta(k)).evalf(18)),atol=1e-13)
        return 'Ordinary Fourier convergence: harmonic versus absolutely summable tails and shifted phase'
    if group=='filter_limits':
        from signallab_pc.filters import Transfer
        common=np.array([1.])
        for _ in range(p['order']):common=np.polymul(common,[1,p['sign']])
        domain=p['domain'];parameter=p['base'];denominator=[1,-parameter] if domain=='digital' else [1,parameter]
        full=Transfer(common,np.polymul(common,denominator),domain);w=np.array([0.,.2,.8,np.pi])
        if domain=='digital':
            q=np.exp(-1j*w);response=1/(1-parameter*q);delay=(parameter*q/(1-parameter*q)).real
        else:response=1/(parameter+1j*w);delay=parameter/(parameter**2+w**2)
        assert_allclose(full.response(w),response,atol=3e-13,rtol=3e-13)
        assert_allclose(full.group_delay(w),delay,atol=3e-12,rtol=3e-12)
        return 'Equivalent transfer functions: response and analytic group-delay limits with repeated common factors'
    if group=='fourier_definitions':
        from signallab_pc.fourier import dtft_with_dft
        from signallab_pc.operations import dft
        values=np.array(p['real'])+1j*np.array(p['imag']);x=Signal(values,p['origin']);s,(w,bins)=dtft_with_dft(x,-np.pi,np.pi,17)
        indices=np.arange(len(values))+p['origin']
        def direct(f):return np.array([sum(v*np.exp(-1j*omega*n) for n,v in zip(indices,values)) for omega in f])
        assert_allclose(s.values,direct(s.axis),atol=5e-13,rtol=3e-13);assert_allclose(bins,direct(w),atol=5e-13,rtol=3e-13)
        transformed=dft(x).values;assert_allclose(np.sum(abs(transformed)**2)/len(values),np.sum(abs(values)**2),atol=2e-13)
        return 'DTFT and DFT overlays against defining sums; Parseval for generated complex records'
    if group=='equation_solution':
        from signallab_pc.difference_equations import solve
        a0=sp.Integer(p['a0']);r=sp.Rational(p['ratio']);initial=sp.Integer(p['initial']);start=p['start']
        result=solve(dict(expression='1/3',coefficients=[str(a0),str(-a0*r)],rest=False,initial=[str(initial)],start=start,count=7))
        y=restore(result['cas_encoded']);steady=1/(3*a0*(1-r));want=steady+(initial-steady)*r**(N-start+1)
        assert sp.simplify(y-want)==0,(y,want)
        expected=[float(want.subs(N,n)) for n in range(start,start+7)];samples=np.array(result['numeric_samples'])[:,0]
        assert_allclose(samples,expected,atol=1e-13,rtol=2e-13)
        return 'Known forced recurrence solution with nonunit leading coefficient and shifted initial history'
    if group=='cas_algebra':
        from signallab_pc.cas_engine import calculate,empty_state,restore
        state=empty_state();cell=0
        def cas(source):
            nonlocal state,cell
            cell+=1;result=calculate(dict(source=source,state=state,cell=cell));state=result['state']
            return restore(state['results'][str(cell)])
        a,b,left,right=p['a'],p['b'],p['left'],p['right'];x=sp.Symbol('x')
        if p['mode']=='factor_roots':
            expression=f'(x-({left}))*(x-({right}))';expanded=cas('expand('+expression+')')
            assert sp.expand(expanded-(x-left)*(x-right))==0
            assert cas('solve('+expression+',x)')==sp.FiniteSet(left,right)
            assert sp.simplify(cas('factor('+str(expanded)+')')-(x-left)*(x-right))==0
        elif p['mode']=='domains':
            assert cas('sqrt(x^2)')!=x
            cas('assume(x>0)');positive=cas('x');assert cas('sqrt(x^2)')==positive
            cas('purge(x)');assert cas('sqrt(x^2)')!=x
            cas('assume(n,integer)');assert cas('solve(n^2=2,n)')==sp.EmptySet
        elif p['mode']=='euler':
            angle=f'({a})*x+({left})';value=cas('exp2trig(exp(i*('+angle+')))')
            assert sp.simplify(value-(sp.cos(a*x+left)+sp.I*sp.sin(a*x+left)))==0
            value=cas('trig2exp(sin('+angle+'))');assert sp.simplify(value-sp.sin(a*x+left).rewrite(sp.exp))==0
        else:
            cas(f'A:=matrix([[{a},{b}],[1,{a+1}]])');assert cas('det(A)')==a*(a+1)-b;assert cas('inv(A)*A')==sp.eye(2)
        return 'CAS algebraic identities, root substitution, domains, exact matrices or Euler conversion'
    raise ValueError('Unknown audit group: '+group)
