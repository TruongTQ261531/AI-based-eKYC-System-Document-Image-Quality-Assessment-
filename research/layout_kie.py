"""Prediction-only printed-label/value assignment in a rectified OCR frame."""
import hashlib
import re
import time

import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment

from ekyc.document_fields import LABELS,PATTERNS,fold,observed_information
from research.recovery_runtime import RecoveryEngine,semantic,make_view


def label(text):
    text=' '.join(text.split());plain=fold(text);matches=[]
    for key,pattern in PATTERNS.items():
        match=re.match(pattern,plain)
        if match:matches.append((match.end(),key))
    for key,title in LABELS.items():
        alias=fold(title)
        if plain==alias or plain.startswith(alias+':'):matches.append((len(alias),key))
    if matches:
        end,key=max(matches);value=text[end:].strip(' :：/.-')
        return key,LABELS.get(key,key),value
    custom=re.fullmatch(r'([^:：]{2,60})[:：]\s*(.*)',text)
    if custom:
        title,value=custom.groups();key='extra_'+hashlib.sha256(fold(title).encode()).hexdigest()[:12]
        return key,title,value.strip()
    return None


def geometry(prediction):
    q=np.asarray(prediction['box'],float);x1,y1=q.min(axis=0);x2,y2=q.max(axis=0)
    return float(x1),float(y1),float(x2),float(y2)


def extract(predictions):
    base=semantic(predictions);labels=dict(LABELS);nodes=[];values=[];candidates={}
    for item in predictions:
        text=item['text'].strip();found=label(text)
        if not text:continue
        if found:
            key,title,inline=found;labels[key]=title
            if inline:
                cleaned,_,_=observed_information([], {key:inline})
                if key in cleaned:candidates[key]=cleaned[key]
            else:nodes.append(dict(key=key,box=geometry(item)))
        else:values.append(dict(value=text,box=geometry(item)))
    if nodes and values:
        costs=np.full((len(nodes),len(values)+len(nodes)),6.0)
        for i,node in enumerate(nodes):
            x1,y1,x2,y2=node['box'];h=max(5.,y2-y1)
            for j,value in enumerate(values):
                a,b,c,d=value['box'];vh=max(5.,d-b);dy=abs((b+d-y1-y2)/2)
                right=a-x2>=-.2*h and dy<=.65*max(h,vh)
                down=-.1*h<=b-y2<=3.5*h and -h<=a-x1<=3*h
                if not right and not down:continue
                cleaned,_,_=observed_information([], {node['key']:value['value']})
                if node['key'] not in cleaned:continue
                right_cost=max(0.,a-x2)/h+2*dy/h if right else 1e6
                down_cost=2+max(0.,b-y2)/h+abs(a-x1)/(2*h) if down else 1e6
                costs[i,j]=min(right_cost,down_cost)
        rr,cc=linear_sum_assignment(costs)
        for i,j in zip(rr,cc):
            if j<len(values) and costs[i,j]<6:
                candidates.setdefault(nodes[i]['key'],values[j]['value'])
    # An explicitly associated observed value supersedes the row-concatenation
    # alternative. No missing mandatory fields are manufactured.
    fields={**base,**candidates};fields,_,_=observed_information([],fields)
    return fields,labels,dict(printed_labels=len(nodes)+len(candidates),candidate_value_boxes=len(values))


def to_view(predictions,inverse):
    matrix=np.linalg.inv(inverse);result=[]
    for pred in predictions:
        box=cv2.perspectiveTransform(np.asarray(pred['box'],np.float32)[None],matrix)[0]
        result.append(dict(pred,box=box.tolist()))
    return result


class LayoutKIEEngine(RecoveryEngine):
    def locate(self,image,key='fastvit'):
        result=super().locate(image,key)
        self._request_locations[key]=result
        return result

    def online(self,image,locked,reader='rapid_latin_v5'):
        self._request_locations={};answer=super().online(image,locked,reader)
        wall=time.perf_counter();cpu=time.process_time()
        _,inverse,_,_=make_view(image,self._request_locations['fastvit'],answer['selected_policy'],lcnet=self._request_locations.get('lcnet'))
        fields,labels,_=extract(to_view(answer['predictions'],inverse))
        answer['fields']=fields;answer['field_labels']=labels;answer['kie_method']='layout_assignment_v1_exploratory'
        answer['kie_additional_wall_seconds']=time.perf_counter()-wall
        answer['actual_wall_seconds']+=answer['kie_additional_wall_seconds']
        answer['actual_cpu_seconds']+=time.process_time()-cpu
        return answer
