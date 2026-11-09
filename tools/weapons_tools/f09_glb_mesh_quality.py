"""Reject non-finite normals and collapsed triangles in baked F09 GLB exports.

The ratchet thin head lid previously had a 1.7mm bevel on a 3mm cap,
producing zero-area triangles and Godot's non-finite LOD normals warning.
"""
import json
import struct
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"build"/"f09_integration_fixture"
IDS=("ll_tools_adjustable_wrench","ll_tools_socket_handle","ll_tools_hand_saw")
DT={5126:"<f4",5123:"<u2",5125:"<u4",5121:"u1",5122:"<i2"}
SHAPE={"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4}

def get_gltf(path):
    content=path.read_bytes()
    assert content[:4]==b"glTF"
    assert struct.unpack_from("<I",content,8)[0]==len(content)
    length,kind=struct.unpack_from("<II",content,12)
    assert kind==0x4e4f534a
    data=json.loads(content[20:20+length])
    off=20+length
    binary_len,binary_kind=struct.unpack_from("<II",content,off)
    assert binary_kind==0x004e4942
    return data,content[off+8:off+8+binary_len]

def accessor(g,b,idx):
    ac=g["accessors"][idx]
    view=g["bufferViews"][ac["bufferView"]]
    count=ac["count"]
    width=SHAPE[ac["type"]]
    dtype=np.dtype(DT[ac["componentType"]])
    start=view.get("byteOffset",0)+ac.get("byteOffset",0)
    stride=view.get("byteStride",dtype.itemsize*width)
    assert start+(count-1)*stride+width*dtype.itemsize<=len(b)
    if stride==dtype.itemsize*width:
        return np.frombuffer(b,dtype=dtype,count=count*width,offset=start).reshape(count,width)
    return np.array([np.frombuffer(b,dtype=dtype,count=width,offset=start+i*stride)
                     for i in range(count)])

def main():
    results=[]
    for ident in IDS:
        glb=BASE/ident/"preview_albedo_baked.glb"
        g,b=get_gltf(glb)
        tri_count=0
        for mesh in g.get("meshes",[]):
            for primitive in mesh.get("primitives",[]):
                attributes=primitive["attributes"]
                pos=accessor(g,b,attributes["POSITION"]).astype(np.float64)
                normals=accessor(g,b,attributes["NORMAL"]).astype(np.float64)
                assert np.isfinite(pos).all(),(ident,"nonfinite positions")
                assert np.isfinite(normals).all(),(ident,"nonfinite normals")
                assert (np.linalg.norm(normals,axis=1)>.1).all(),(ident,"zero normals")
                if primitive.get("mode",4)!=4:continue
                ids=(accessor(g,b,primitive["indices"]).ravel() if "indices" in primitive
                     else np.arange(len(pos)))
                assert len(ids)%3==0
                assert int(ids.max())<len(pos)
                coords=pos[ids].reshape(-1,3,3)
                areas=np.linalg.norm(np.cross(coords[:,1]-coords[:,0],
                                               coords[:,2]-coords[:,0]),axis=1)
                assert (areas>1e-13).all(),(ident,"degenerate GLB triangles",
                                              int((areas<=1e-13).sum()),len(areas))
                tri_count+=len(areas)
        assert tri_count>100,(ident,tri_count)
        results.append({"asset_id":ident,"triangles":tri_count,
                        "invalid_normals":0,"degenerate_triangles":0})
    (BASE/"glb_mesh_quality.json").write_text(json.dumps({
        "status":"SOURCE_GLTF_GEOMETRY_QA_NOT_GOLDEN_APPROVED",
        "records":results},indent=2)+"\n")
    print("F09_GLB_NO_DEGENERATE_MESH_PASS",len(results),flush=True)

if __name__=="__main__":main()
