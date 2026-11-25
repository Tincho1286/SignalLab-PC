"""Display labels for the concrete variants of a tool."""


def values_for(entry,key):
    return next((values for candidate,values in entry['variants'] if candidate==key),entry['variants'][0][1])


def variant_title(entry, key, *, omit_group=False):
    values = values_for(entry, key)
    if not values:
        return ''
    if len(entry['dimensions']) == 1:
        return values[0]
    group = values[0]
    tail = entry.get('variant_titles', {}).get(key, ' · '.join(dict.fromkeys(values[1:])))
    if not tail or tail == group:
        return group
    return tail if omit_group else f'{group} · {tail}'
