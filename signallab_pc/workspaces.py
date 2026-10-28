"""One explorer entry per coherent workflow, retaining legacy result routes."""
from .navigation import MENUS,FILTER_KEYS,FILTER_ROUTE,TRANSFORM_ALIASES,Z_ROUTE
from .tool_groups import GROUPS,GROUP_ROUTES,GROUP_FOR
ROUTES={item[1:3]:item for items in MENUS.values() for item in items}
STATIONS=[(area,title,symbol,[GROUP_ROUTES[key][1:3]]) for key,(area,title,symbol,_) in GROUPS.items()]
STATIONS += [('Sistemas','Filtros','design',[FILTER_ROUTE[1:3]]),('Sistemas','Conectar sistemas','blocks',[('interconnection',0)]),('Transformadas','Transformada Z','zplane',[Z_ROUTE[1:3]])]
# Keep categories together in the explorer and the menu bar.
_order=['Señales','Sistemas','Espectros','Muestreo','Transformadas','Aleatorias']
STATIONS.sort(key=lambda station:_order.index(station[0]))
STATION_FOR={key:index for index,(_,_,_,keys) in enumerate(STATIONS) for key in keys}
for key,route in GROUP_FOR.items():STATION_FOR[key]=STATION_FOR[route[1:3]]
for key in FILTER_KEYS:STATION_FOR[key]=STATION_FOR[FILTER_ROUTE[1:3]]
for key,route in TRANSFORM_ALIASES.items():STATION_FOR[key]=STATION_FOR[route[1:3]]
STATION_FOR['systems',10]=STATION_FOR['interconnection',0]
if set(STATION_FOR)!=set(ROUTES):raise RuntimeError('La navegación no cubre todas las herramientas: '+str(set(ROUTES)^set(STATION_FOR)))
