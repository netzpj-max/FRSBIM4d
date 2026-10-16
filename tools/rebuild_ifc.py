"""Dependency-free IFC2x3 STEP authoring; validate with a separate IFC reader."""
import json,uuid,time,math,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT;els=json.loads((OUT/'data/elements.json').read_text(encoding='utf8'));p=json.loads((OUT/'data/project.json').read_text(encoding='utf8'));drawing_map={d['id']:d for d in json.loads((OUT/'data/drawings.json').read_text(encoding='utf8'))}
lines=[]
def st(s):return "'"+''.join(c if 32<=ord(c)<=126 else '\\X2\\'+c.encode('utf-16-be').hex().upper()+'\\X0\\' for c in str(s).replace("'","''").replace('\\','\\\\'))+"'"
def num(x):return f'{float(x):.6f}'.rstrip('0').rstrip('.')+'.' if float(x).is_integer() else f'{float(x):.6f}'.rstrip('0')
def add(typ,*args):lines.append(f'#{len(lines)+1}={typ.upper()}('+','.join(args)+');');return '#'+str(len(lines))
def refs(xs):return '('+','.join(xs)+')'
def guid(key):
 n=uuid.uuid5(uuid.NAMESPACE_URL,'FSR/R01/'+key).int;s='';alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$'
 for _ in range(22):s=alphabet[n&63]+s;n>>=6
 return st(s)
def point(x,y,z=None):return add('IfcCartesianPoint',refs([num(x),num(y)]+([] if z is None else [num(z)])))
zero=point(0,0,0);zdir=add('IfcDirection','(0.,0.,1.)');xdir=add('IfcDirection','(1.,0.,0.)');axis=add('IfcAxis2Placement3D',zero,zdir,xdir)
person=add('IfcPerson','$',st('BIM 4D Creator'),'$','$','$','$','$','$');org=add('IfcOrganization','$',st(p['name']),'$','$','$');personorg=add('IfcPersonAndOrganization',person,org,'$');app=add('IfcApplication',org,st('R01'),st('BIM 4D Creator - Four Seasons Residences'),st('FSR-BIM4D'));owner=add('IfcOwnerHistory',personorg,app,'$','.ADDED.','$','$','$',str(int(time.time())))
units=add('IfcUnitAssignment',refs([add('IfcSIUnit','*','.LENGTHUNIT.','$','.METRE.'),add('IfcSIUnit','*','.AREAUNIT.','$','.SQUARE_METRE.'),add('IfcSIUnit','*','.VOLUMEUNIT.','$','.CUBIC_METRE.')]))
context=add('IfcGeometricRepresentationContext','$',st('Model'),'3','0.00001',axis,'$')
project=add('IfcProject',guid('project'),owner,st(p['name']),st('R01 - DWG-derived review model with explicit assumptions'),'$','$','$',refs([context]),units)
sitepl=add('IfcLocalPlacement','$',axis);site=add('IfcSite',guid('site'),owner,st(p['name']+' Site'),'$','$',sitepl,'$','$','.ELEMENT.','$','$','$','$','$')
bldpl=add('IfcLocalPlacement',sitepl,axis);bld=add('IfcBuilding',guid('building'),owner,st(p['name']),st('Review model. Vertical datum conflicts unresolved.'),'$',bldpl,'$','$','.ELEMENT.','$','$','$')
add('IfcRelAggregates',guid('project-site'),owner,'$','$',project,refs([site]));add('IfcRelAggregates',guid('site-building'),owner,'$','$',site,refs([bld]))
leveldata=json.loads((OUT/'data/levels.json').read_text(encoding='utf8'))['chosenTemporary'];storeys={};groups={};mats={};catgroups={};category_reps={}
for fl in p['modeledFloors']:
 name=fl if fl=='ROOF' else str(int(fl[1:]));elev=leveldata[name];ax=add('IfcAxis2Placement3D',point(0,0,elev),zdir,xdir);pl=add('IfcLocalPlacement',bldpl,ax);sto=add('IfcBuildingStorey',guid('storey/'+fl),owner,st(fl),st('Temporary Section BB FFL; see levels.json'),'$',pl,'$','$','.ELEMENT.',num(elev));storeys[fl]=(sto,pl,elev);groups[fl]=[]
add('IfcRelAggregates',guid('building-storeys'),owner,'$','$',bld,refs([v[0] for v in storeys.values()]))
palette={'เสา/คอนกรีต':(.84,.80,.66),'ผนังโครงสร้าง':(.60,.69,.57),'ผนังภายใน':(.72,.77,.68),'พื้น':(.50,.65,.43),'หน้าต่าง':(.30,.59,.62),'ประตู':(.68,.49,.33),'บันได/ชานพัก':(.71,.62,.43),'หลังคา':(.66,.78,.52)}
styles={}
for cat,rgb in palette.items():
 col=add('IfcColourRgb','$',*[num(v) for v in rgb])
 shade=add('IfcSurfaceStyleShading',col);surface=add('IfcSurfaceStyle','$','.BOTH.',refs([shade]));styles[cat]=add('IfcPresentationStyleAssignment',refs([surface]))
for idx,e in enumerate(els):
 sto,storeypl,elev=storeys[e['floor']];pts=[point(x,y) for x,y in e['poly']];pts.append(pts[0]);poly=add('IfcPolyline',refs(pts));profile=add('IfcArbitraryClosedProfileDef','.AREA.','$',poly);pos=add('IfcAxis2Placement3D',point(0,0,e['z']-elev),zdir,xdir);solid=add('IfcExtrudedAreaSolid',profile,pos,zdir,num(e['height']));add('IfcStyledItem',solid,refs([styles[e['category']]]),'$');rep=add('IfcShapeRepresentation',context,st('Body'),st('SweptSolid'),refs([solid]));shape=add('IfcProductDefinitionShape','$','$',refs([rep]));pl=add('IfcLocalPlacement',storeypl,axis)
 category_reps.setdefault(e['category'],[]).append(rep)
 args=[st(e['ifcGuid']),owner,st(e['name']),st(e['assumption']),st(e['category']),pl,shape,st(e['id'])];cls=e['ifcClass']
 if cls=='IfcSlab':args+=['.ROOF.' if e['category']=='หลังคา' else '.LANDING.' if e['category']=='บันได/ชานพัก' else '.FLOOR.']
 if cls in ('IfcDoor','IfcWindow'):args += [num(e['height']),num(e['dimensions']['orientedWidth'])]
 product=add(cls,*args);groups[e['floor']].append(product);catgroups.setdefault(e['category'],[]).append(product)
 props=[]
 for key,val in {'ElementID':e['id'],'Revision':'R01','Category':e['category'],'Storey':e['floor'],'SourceDWG':drawing_map[e['sourceId']]['filename'],'SourceDrawingID':e['sourceId'],'SourceLayer':e['sourceLayer'],'Confidence':e['confidence'],'GeometryEvidence':e['geometryEvidence'],'Assumption':e['assumption'],'ActivityID':e['activityId'],'QuantityBasis':p['quantityBasis'],'Unit':e['unit']}.items():props.append(add('IfcPropertySingleValue',st(key),'$',f'IFCTEXT({st(val)})','$'))
 props.append(add('IfcPropertySingleValue',st('Quantity'),'$',f'IFCREAL({num(e["quantity"])})','$'))
 pset=add('IfcPropertySet',guid(e['id']+'/properties'),owner,st('Pset_FourSeasons_R01_Review'),'$',refs(props));add('IfcRelDefinesByProperties',guid(e['id']+'/relprops'),owner,'$','$',refs([product]),pset)
 qa=add('IfcQuantityArea',st('GrossFootprintArea'),'$','$',num(e['footprintArea']));qv=add('IfcQuantityVolume',st('GrossModelVolume'),'$','$',num(e['grossVolume']));q=add('IfcElementQuantity',guid(e['id']+'/quantities'),owner,st('ReviewGeometryQuantities'),st('No opening deductions'),st('Gross model extrusion'),refs([qa,qv]));add('IfcRelDefinesByProperties',guid(e['id']+'/relquantities'),owner,'$','$',refs([product]),q)
 if e['material'] not in mats:mats[e['material']]=[add('IfcMaterial',st(e['material'])),[]]
 mats[e['material']][1].append(product)
 if idx%1000==0:print('IFC element',idx,'/',len(els),flush=True)
for fl,products in groups.items():add('IfcRelContainedInSpatialStructure',guid('contain/'+fl),owner,'$','$',refs(products),storeys[fl][0])
for name,(mat,products) in mats.items():add('IfcRelAssociatesMaterial',guid('material/'+name),owner,'$','$',refs(products),mat)
for name,reps in category_reps.items():add('IfcPresentationLayerAssignment',st(name),st('DWG-derived review category'),refs(reps),'$')
file=OUT/'model/Four-Seasons-Residences_R01.ifc'
import datetime
header="ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('ViewDefinition [CoordinationView_V2.0]','R01 review: assumptions and unresolved vertical datum'),'2;1');\nFILE_NAME('Four-Seasons-Residences_R01.ifc','"+datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')+"',('BIM 4D Creator'),('Four Seasons Residences'),'BIM 4D Creator R01','BIM 4D Creator','');\nFILE_SCHEMA(('IFC2X3'));\nENDSEC;\nDATA;\n"
import shutil
if file.exists():shutil.copy2(file,file.with_suffix('.ifc.bak'))
file.write_text(header+'\n'.join(lines)+'\nENDSEC;\nEND-ISO-10303-21;\n',encoding='ascii');print('IFC',file.stat().st_size,'bytes',len(lines),'STEP entities',flush=True)
