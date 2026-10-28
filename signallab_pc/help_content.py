"""Library articles with explicit authorship for each public calculation route."""
from .navigation import MENUS,RETIRED_KEYS
from .tool_catalog import detail_for,AREA_BY_ID
from .library_articles import article_blocks

def sections():
    result=[]
    for category,items in MENUS.items():
        for item in items:
            title,kind,task,_=item
            if (kind,task) in RETIRED_KEYS or kind in ('tool_group','filter_lab'):continue
            entry=detail_for(item);blocks=article_blocks(item)
            location=AREA_BY_ID[entry['area']][1]+' › '+entry['section'] if entry else category
            result.append(dict(title=entry['title'] if entry else title,category=location,legacy_category=category,route=tuple(item),purpose=blocks[0][1],usage=blocks[1][1],blocks=blocks,field_reference=True))
    return result
