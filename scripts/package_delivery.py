"""Package source-declared, immutable HTML versions and a stable latest entry."""
import argparse,json,hashlib,os,shutil,re
from pathlib import Path

def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp');tmp.write_bytes(data);os.replace(tmp,path)
def package(config,out):
 cfg=json.loads(config.read_text());out.mkdir(parents=True,exist_ok=True);records=[];previous=json.loads((out/'delivery.json').read_text()) if (out/'delivery.json').exists() else {};old={v['id']:v for v in previous.get('versions',[])}
 assert re.fullmatch(r'[a-z0-9-]+',cfg['projectId'])
 for v in cfg['versions']:
  assert re.fullmatch(r'[a-z0-9-]+',v['id'])
  source=Path(v['source']);source=source if source.is_absolute() else config.parent/source
  data=source.read_bytes();digest=hashlib.sha256(data).hexdigest();assert v['id'] not in old or old[v['id']]['sha256']==digest, 'Version ID already published locally with different bytes; use a new revision ID.';rel=f"versions/{v['id']}-{digest[:12]}/index.html";dest=out/rel
  if dest.exists():assert dest.read_bytes()==data
  else:atomic(dest,data)
  record={k:x for k,x in v.items() if k not in ['source','presentationSource']}|{'url':rel,'sha256':digest}
  if v.get('presentationSource'):
   display=Path(v['presentationSource']);display=display if display.is_absolute() else config.parent/display;body=display.read_bytes();view=f"views/{v['id']}-{hashlib.sha256(body).hexdigest()[:12]}.html";atomic(out/view,body);record['presentationUrl']=view
  records.append(record)
 current=next(v for v in records if v['id']==cfg['currentVersion'])
 # Stable project URL keeps hash (view and node) while resolving current immutable artifact.
 landing='<!doctype html><meta charset="utf-8"><title>'+cfg['title']+'</title><script>location.replace('+json.dumps(current['url'])+'+location.search+location.hash)</script><a href="'+current['url']+'">打开项目</a>'
 atomic(out/'index.html',landing.encode());manifest={'schemaVersion':1,'projectId':cfg['projectId'],'title':cfg['title'],'currentVersion':cfg['currentVersion'],'figma':cfg['figma'],'versions':records,'nodes':cfg.get('nodes',[]),'baseUrl':cfg.get('baseUrl'),'publicationStatus':'prepared'}
 atomic(out/'delivery.json',(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode());return manifest
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('manifest',type=Path);a.add_argument('--out',type=Path,required=True);args=a.parse_args();m=package(args.manifest,args.out);print(json.dumps({'project':m['projectId'],'versions':len(m['versions']),'out':str(args.out),'publicationStatus':'prepared'},ensure_ascii=False))
