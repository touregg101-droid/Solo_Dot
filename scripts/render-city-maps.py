"""Render public-domain Natural Earth geography as a deliberately coarse city map.
Run: python3 scripts/render-city-maps.py PATH_TO_NATURAL_EARTH_GEOJSON
Pillow is only used to rasterize vector geographic data (no artwork editing).
"""
import json, math, hashlib, sys
from pathlib import Path
from PIL import Image, ImageDraw
source=Path(sys.argv[1])
output=Path(__file__).resolve().parents[1]/'public/maps'
output.mkdir(exist_ok=True)
layers={name:json.loads((source/(name+'.geojson')).read_text())['features'] for name in ['ne_10m_land','ne_10m_urban_areas','ne_10m_rivers_lake_centerlines']}
# WGS84 display centers and horizontal spans; display choices, never user coordinates.
cities=[('tokyo',139.78,35.67,.62),('seoul',126.985,37.55,.58),('busan',129.04,35.13,.59),('paris',2.34,48.86,.48)]
colors={'water':'#bddce0','land':'#e5edda','urban':'#f3f0df','shore':'#a9c9c5'}
metadata={}
def rings(g):
 if g['type']=='Polygon':return [g['coordinates']]
 if g['type']=='MultiPolygon':return g['coordinates']
 return []
def intersects(coords,b):
 xs=[p[0] for p in coords];ys=[p[1] for p in coords]
 return max(xs)>=b[0] and min(xs)<=b[2] and max(ys)>=b[1] and min(ys)<=b[3]
for slug,lng,lat,span in cities:
 metadata[slug]={}
 for orientation,W,H in [('wide',240,160),('tall',160,200)]:
  # Same east-west distance; vertically show more on a phone, preserving north-up shape.
  height=span*math.cos(math.radians(lat))*H/W
  b=(lng-span/2,lat-height/2,lng+span/2,lat+height/2)
  def project(p):return (round((p[0]-b[0])/span*W),round((b[3]-p[1])/height*H))
  im=Image.new('RGB',(W,H),colors['water']);landmask=Image.new('1',(W,H));d=ImageDraw.Draw(landmask)
  for f in layers['ne_10m_land']:
   for poly in rings(f['geometry']):
    if not intersects(poly[0],b):continue
    d.polygon([project(p) for p in poly[0]],fill=1)
    for hole in poly[1:]:d.polygon([project(p) for p in hole],fill=0)
  im.paste(colors['land'],mask=landmask.convert('L'))
  urbanmask=Image.new('1',(W,H));d=ImageDraw.Draw(urbanmask)
  for f in layers['ne_10m_urban_areas']:
   for poly in rings(f['geometry']):
    if not intersects(poly[0],b):continue
    d.polygon([project(p) for p in poly[0]],fill=1)
    for hole in poly[1:]:d.polygon([project(p) for p in hole],fill=0)
  import PIL.ImageChops
  urbanmask=PIL.ImageChops.logical_and(urbanmask,landmask)
  im.paste(colors['urban'],mask=urbanmask.convert('L'))
  d=ImageDraw.Draw(im);rivers=[]
  for f in layers['ne_10m_rivers_lake_centerlines']:
   g=f['geometry'];lines=g['coordinates'] if g['type']=='MultiLineString' else [g['coordinates']]
   for line in lines:
    if not intersects(line,b):continue
    if f['properties'].get('name') not in ['Han','Seine','Nakdong','Tone']:continue
    d.line([project(p) for p in line],fill=colors['water'],width=3)
    rivers.append(f['properties'].get('name'))
  # Avatar spots are arbitrary dry-land display cells and are never user locations.
  candidates=[(18,25),(48,19),(76,28),(33,46),(64,48),(17,69),(46,75),(79,75),(52,53)]
  points=[]
  for px,py in candidates:
   x,y=round(px*W/100),round(py*H/100)
   allpoints=((xx,yy) for yy in range(18,H-25) for xx in range(15,W-15) if im.getpixel((xx,yy))!=tuple(int(colors['water'][i:i+2],16) for i in (1,3,5)))
   x,y=min(allpoints,key=lambda p:(p[0]-x)**2+(p[1]-y)**2)
   points.append([round(x/W*100,2),round(y/H*100,2)])
  im.save(output/f'{slug}-{orientation}.png',optimize=True)
  # These enlarged copies are QA artifacts, not shipped assets.
  qa=source/f'{slug}-{orientation}-preview.png';im.resize((W*4,H*4),Image.Resampling.NEAREST).save(qa)
  metadata[slug][orientation]={'bbox':list(b),'rivers':sorted(set(rivers)),'dots':points,'size':[W,H]}
  print(slug,orientation,'rivers:',sorted(set(rivers)),'palette:',len(im.getcolors()))
(output/'geography.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
provenance={'source':'Natural Earth','license':'Public domain','website':'https://www.naturalearthdata.com/about/terms-of-use/','rendering':'North-up local equirectangular projection; city-scale, coarse raster; river width exaggerated for readability; not for navigation. Urban areas are built-up areas, not administrative boundaries.','layers':[{ 'url':'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/'+n+'.geojson','sha256':hashlib.sha256((source/(n+'.geojson')).read_bytes()).hexdigest()} for n in layers]}
(output/'sources.json').write_text(json.dumps(provenance,indent=2))
