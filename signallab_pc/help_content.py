"""Library articles with explicit authorship for each public calculation route."""
from .navigation import MENUS,RETIRED_KEYS
from .tool_catalog import detail_for,AREA_BY_ID
from .library_articles import article_blocks
from .desktop_help import LIMITS_ID, LIMITS_HEADING

def sections():
    result=[]
    for category,items in MENUS.items():
        for item in items:
            title,kind,task,_=item
            if (kind,task) in RETIRED_KEYS or kind in ('tool_group','filter_lab'):continue
            entry=detail_for(item);blocks=article_blocks(item)
            location=AREA_BY_ID[entry['area']][1]+' › '+entry['section'] if entry else category
            related=[]
            if any(heading==LIMITS_HEADING for heading,_ in blocks):
                related.append((LIMITS_ID,'Valores por continuidad'))
                blocks=[(heading,body) for heading,body in blocks if heading!=LIMITS_HEADING]
            result.append(dict(title=entry['title'] if entry else title,category=location,legacy_category=category,route=tuple(item),purpose=blocks[0][1],usage=blocks[1][1],blocks=blocks,field_reference=True,related=related))
    return result
