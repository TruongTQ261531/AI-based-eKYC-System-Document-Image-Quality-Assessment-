"""Explicit evidence realizations: OR across sources, AND across components.

Ground-truth construction uses author annotations. Online TD3 parsing takes
only recognized text. It does not verify identity or document authenticity.
"""
import re
import random
import cv2
import numpy as np
from research.v2_common import seed
from research.v2_data import mapped_fields

def check_digit(text):
    def value(c):
        if c=='<':return 0
        if '0'<=c<='9':return ord(c)-48
        if 'A'<=c<='Z':return ord(c)-55
        raise ValueError('Non-MRZ character')
    return str(sum(value(c)*[7,3,1][i%3] for i,c in enumerate(text))%10)

def parse_td3(first,second):
    """Exact44-character lines only; no guessed/OCR-corrected characters."""
    if len(first)!=44 or len(second)!=44 or not first.startswith('P') or not re.fullmatch('[A-Z<]{44}',first) or not re.fullmatch('[A-Z0-9<]{44}',second):return None
    if not re.fullmatch('[A-Z<]{3}',second[10:13]) or second[20] not in 'MF<' or not re.fullmatch('[0-9<]{6}',second[13:19]) or not re.fullmatch('[0-9<]{6}',second[21:27]):return None
    checks={}
    for key,start,end,position in [('id_number',0,9,9),('dob',13,19,19),('expiry_date',21,27,27),('optional',28,42,42)]:
        checks[key]=second[position]==check_digit(second[start:end]) or key=='optional' and set(second[start:end])=={'<'} and second[position] in '<0'
    checks['composite']=second[43]==check_digit(second[:10]+second[13:20]+second[21:43])
    spans=[]
    def add(key,line,start,end,value,kind='text',checked=True):
        if value and value.strip('< '):spans.append(dict(key=key,line=line,start=start,end=end,value=value,kind=kind,checksum_valid=checked))
    names=first[5:];sep=names.find('<<')
    if sep>=0:
        last=names[:sep].strip('<').replace('<',' ');given=names[sep+2:]
        # A terminal filler establishes that the given-name string is not
        # visibly truncated at the44-character limit. Otherwise do not guess.
        if given.endswith('<'):
            add('last_name',0,5,5+sep,' '.join(last.split()),checked=None)
            add('first_name',0,7+sep,7+sep+len(given.rstrip('<')),' '.join(given.strip('<').replace('<',' ').split()),checked=None)
    add('id_number',1,0,9,second[:9].rstrip('<'),checked=checks['id_number'])
    add('nationality',1,10,13,second[10:13].replace('<',''),checked=None)
    if second[13:19].isdigit():add('dob',1,13,19,second[13:19],'date_yymmdd',checks['dob'])
    if second[20] in 'MF':add('gender',1,20,21,second[20],checked=None)
    if second[21:27].isdigit():add('expiry_date',1,21,27,second[21:27],'date_yymmdd',checks['expiry_date'])
    return dict(spans=spans,optional=second[28:42],checks=checks)

def span_quad(quad,start,end):
    # A homography from the monospaced44-cell strip preserves projective
    # spacing, unlike linear interpolation directly in photographed pixels.
    H=cv2.getPerspectiveTransform(np.float32([[0,0],[44,0],[44,1],[0,1]]),np.float32(quad))
    return cv2.perspectiveTransform(np.float32([[[start,0],[end,0],[end,1],[start,1]]]),H)[0].tolist()

def body_sources(source):
    native=mapped_fields(source);by_key={f['author_key']:f for f in source['fields']};nodes=[]
    for f in native:
        parts=f['author_key'].split('+')
        regions=[by_key[k]['quad'] for k in parts]
        nodes.append(dict(key=f['key'],value=f['value'],components=regions,kind='body',priority=0 if '_eng' not in f['author_key'] else 1,
                          author_source=f['author_key']))
    # Additional exact repeated body values (e.g. number2/number3) are evidence
    # only when an unambiguous existing semantic field establishes the link.
    used={f['author_key'] for f in native}
    for f in source['fields']:
        if f['author_key'] not in ('number2','number3') or f['author_key'] in used or len(f['value'])<4:continue
        matches={n['key'] for n in nodes if n['value']==f['value']}
        if len(matches)==1:nodes.append(dict(key=matches.pop(),value=f['value'],components=[f['quad']],kind='body_duplicate',priority=2,author_source=f['author_key']))
    return nodes

def source_graph(source):
    nodes=body_sources(source);keys={n['key'] for n in nodes};by_key={f['author_key']:f for f in source['fields']}
    if not all('mrz_line'+str(i) in by_key for i in (0,1)):return nodes,dict(mrz_present=False,mrz_parsed=False)
    lines=[by_key['mrz_line'+str(i)] for i in (0,1)];parsed=parse_td3(lines[0]['value'],lines[1]['value'])
    if parsed is None:return nodes,dict(mrz_present=True,mrz_parsed=False)
    for span in parsed['spans']:
        if span['key'] not in keys:continue  # bounded17-key author-body task
        nodes.append(dict(key=span['key'],value=span['value'],components=[span_quad(lines[span['line']]['quad'],span['start'],span['end'])],
            kind=span['kind'],priority=10,author_source='mrz_line'+str(span['line'])+f":{span['start']}:{span['end']}",checksum_valid=span['checksum_valid']))
    # Optional data is not universally a personal number. Require the author's
    # explicit personal number to occur there before associating its span.
    for n in list(nodes):
        if n['key']!='personal_number' or n['kind'] not in ('body','body_duplicate'):continue
        value=n['value'];start=parsed['optional'].find(value)
        if start>=0:
            nodes.append(dict(key='personal_number',value=value,components=[span_quad(lines[1]['quad'],28+start,28+start+len(value))],
                              kind='mrz_personal_link',priority=10,author_source='mrz_line1:author_personal_match',checksum_valid=parsed['checks']['optional']))
            break
    return nodes,dict(mrz_present=True,mrz_parsed=True,checks=parsed['checks'])

def capture_geometry(source,row,full_shape):
    h,w=full_shape;kind=row['capture'];H=np.eye(3);masks=[]
    original=mapped_fields(source)
    if kind=='perspective':
        H=cv2.getPerspectiveTransform(np.float32([[0,0],[w-1,0],[w-1,h-1],[0,h-1]]),np.float32([[.08*w,.10*h],[.94*w,.04*h],[.98*w,.94*h],[.04*w,.98*h]]))
    elif kind=='field_clip':
        delta=float(row['fields'][0]['quad'][0][1])-float(original[0]['quad'][0][1]);H[1,2]=delta
        if abs(delta-round(delta))>1e-4:raise ValueError('Unexpected crop translation')
    elif kind=='value_mask':
        rng=random.Random(seed(row['physical_id']+'/'+kind));chosen=rng.sample(range(len(original)),rng.randrange(1,len(original)+1))
        for i in chosen:
            q=np.float32(original[i]['quad']);center=q.mean(axis=0);masks.append((q-center)*1.04+center)
    return H,masks

def visible_realizations(nodes,H,masks,width,height):
    accepted={};evidence=[];occluded_keys=set()
    for node in sorted(nodes,key=lambda n:n['priority']):
        components=[cv2.perspectiveTransform(np.float32([q]),H)[0] for q in node['components']]
        whole=all(bool((q[:,0]>=0).all() and (q[:,0]<=width).all() and (q[:,1]>=0).all() and (q[:,1]<=height).all()) for q in components)
        hidden=any(cv2.intersectConvexConvex(q,np.float32(m))[0]>.05 for q in components for m in masks)
        if hidden:occluded_keys.add(node['key'])
        if whole and not hidden:
            entries=accepted.setdefault(node['key'],[])
            entry=dict(value=node['value'],kind=node['kind'],source=node['author_source'],priority=node['priority'])
            if not any(e['value']==entry['value'] and e['kind']==entry['kind'] for e in entries):entries.append(entry)
            evidence.append(dict(key=node['key'],source=node['author_source'],kind=node['kind']))
    return accepted,evidence,occluded_keys
