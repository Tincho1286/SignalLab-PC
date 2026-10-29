"""Select compatible variants by ordered intent, then remember a branch's mode."""


def values_for(entry,key):
    return next((values for candidate,values in entry['variants'] if candidate==key),entry['variants'][0][1])


def remember_variant(history,entry,key):
    values=values_for(entry,key)
    for size in range(1,len(values)+1):history[(entry['key'],values[:size])]=key


def choose_variant(entry,current_key,index,value,history):
    old=values_for(entry,current_key);prefix=old[:index]+(value,)
    candidates=[(key,values) for key,values in entry['variants'] if values[:index+1]==prefix]
    if not candidates:raise ValueError('La opción no corresponde a una variante de esta herramienta.')
    def score(candidate):
        return tuple(a==b for a,b in zip(candidate[1][index+1:],old[index+1:]))
    best=max(map(score,candidates));pool=[candidate for candidate in candidates if score(candidate)==best]
    common=[]
    for position in range(len(old)):
        options={values[position] for _,values in pool}
        if len(options)!=1:break
        common.append(next(iter(options)))
    remembered=history.get((entry['key'],tuple(common)))
    return next((key for key,_ in pool if key==remembered),pool[0][0])


def dimension_label(entry,index,values):
    return entry.get('dimension_labels',{}).get((index,*values[:index]),entry['dimensions'][index])


def choice_hint(entry,value):
    defaults={
        'Numérico':'Evalúa un registro finito; sus muestras pueden definirse mediante una fórmula.',
        'Algebraico':'Trabaja con una expresión y su soporte; conserva las condiciones del cálculo.',
    }
    return entry.get('choice_hints',{}).get(value,defaults.get(value,value))
