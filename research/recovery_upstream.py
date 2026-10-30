"""Run pinned author preprocessing/postprocessing without installing Capybara.

Only reviewed AST functions/classes are loaded. This tests the normal BGR,
non-centre-crop numerical path, not the entire upstream package installation.
"""
import ast
import copy
import enum
import hashlib
import types
import typing
import zipfile
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import JOIN_STYLE,MultiPolygon
from shapely.geometry import Polygon as ShapelyPolygon

CACHE=Path(__file__).resolve().parent/'cache/upstream'
CAPY_SHA='0872a0c21c128e66f4efc595d36bafca6b22a01c462c5329ce59d387c961ad06'


class _Interpolation(enum.Enum):
    BILINEAR=cv2.INTER_LINEAR
    @classmethod
    def obj_to_enum(cls,value):return value if isinstance(value,cls) else cls(value)


def selected(source,names,namespace,classes=False):
    tree=ast.parse(source)
    nodes=[node for node in tree.body if isinstance(node,ast.ClassDef if classes else ast.FunctionDef) and node.name in names]
    if not nodes:raise ValueError('Expected author source definitions unavailable')
    module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]+nodes,type_ignores=[])
    exec(compile(ast.fix_missing_locations(module),'<pinned-author-functions>','exec'),namespace)


@lru_cache(1)
def native():
    wheel=CACHE/'capybara-1.0.1.whl'
    if hashlib.sha256(wheel.read_bytes()).hexdigest()!=CAPY_SHA:raise ValueError('Pinned Capybara source changed')
    with zipfile.ZipFile(wheel) as z:
        polygon=z.read('capybara/structures/polygons.py').decode()
        geometric=z.read('capybara/vision/geometric.py').decode()
        functional=z.read('capybara/vision/functionals.py').decode()
    ns=dict(np=np,cv2=cv2,copy=copy,deepcopy=copy.deepcopy,overload=typing.overload,INTER=_Interpolation,
            JOIN_STYLE=JOIN_STYLE,MultiPolygon=MultiPolygon,_Polygon_shapely=ShapelyPolygon)
    selected(polygon,{'Polygon','Polygons'},ns,classes=True)
    # Keep only the implemented overload, not typing-only stubs.
    tree=ast.parse(geometric);functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='imresize' and len(n.body)>1]
    selected(ast.unparse(ast.Module(body=functions,type_ignores=[])),{'imresize'},ns)
    selected(functional,{'imbinarize'},ns)
    cb=types.SimpleNamespace(Polygons=ns['Polygons'],imresize=ns['imresize'],imbinarize=ns['imbinarize'],
        is_numpy_img=lambda im:isinstance(im,np.ndarray) and im.ndim==3)
    infer=(CACHE/'docaligner_heatmap_reg_infer.py').read_text(encoding='utf-8')
    author=dict(np=np,cb=cb)
    selected(infer,{'preprocess','postprocess'},author)
    return author


def decode_native(heatmap,height,width):
    reference=native()['postprocess'];points=[]
    for i in range(4):
        values=reference(heatmap[:,i:i+1].copy(),(height,width))
        points.append(values[0] if len(values)==1 else None)
    return points
