# blender modules
import bmesh

# addon modules
from . import main
from .. import fmt
from ... import text
from ... import xray_io
from ... import utils
from ... import log
from ... import version_utils


def _export_sg_new(bmfaces):
    for face in bmfaces:
        sm_group = 0
        for eidx, edge in enumerate(face.edges):
            if not edge.smooth:
                sm_group |= (4, 2, 1)[eidx]
        yield sm_group


def _check_sg_soc(bmedges, sgroups):
    for edge in bmedges:
        if len(edge.link_faces) != 2:
            continue
        sg0 = sgroups[edge.link_faces[0].index]
        sg1 = sgroups[edge.link_faces[1].index]
        if edge.smooth:
            if sg0 != sg1:
                return text.warn.object_sg_smooth
        else:
            if sg0 == sg1:
                return text.warn.object_sg_sharp


def _mark_fsg(face, sgroup, face_sgroup):
    faces = [face]
    for face in faces:
        for edge in face.edges:
            if not edge.smooth:
                continue
            for linked_face in edge.link_faces:
                if face_sgroup.get(linked_face) is None:
                    face_sgroup[linked_face] = sgroup
                    faces.append(linked_face)


def _export_sg_soc(bmfaces):
    face_sgroup = dict()
    sgroup_gen = 0
    for face in bmfaces:
        sgroup = face_sgroup.get(face)
        if sgroup is None:
            face_sgroup[face] = sgroup = sgroup_gen
            sgroup_gen += 1
            _mark_fsg(face, sgroup, face_sgroup)
        yield sgroup


def export_version(cw):
    cw.put(fmt.Chunks.Mesh.VERSION, xray_io.PackedWriter().putf('H', 0x11))


def export_mesh_name(cw, bpy_obj, bpy_root):
    mesh_name = bpy_obj.data.name if bpy_obj == bpy_root else bpy_obj.name
    cw.put(
        fmt.Chunks.Mesh.MESHNAME, xray_io.PackedWriter().puts(mesh_name)
    )


def export_bbox(cw, bm):
    bbox = utils.calculate_mesh_bbox(bm.verts)
    packed_writer = xray_io.PackedWriter()
    packed_writer.putv3f(bbox[0])
    packed_writer.putv3f(bbox[1])
    cw.put(fmt.Chunks.Mesh.BBOX, packed_writer)


def export_flags(cw, bpy_obj):
    if hasattr(bpy_obj.data, 'xray'):
        # MAX sg-format currently unsupported (we use Maya sg-format)
        flags = bpy_obj.data.xray.flags & ~fmt.Chunks.Mesh.Flags.SG_MASK
        cw.put(
            fmt.Chunks.Mesh.FLAGS,
            xray_io.PackedWriter().putf('B', flags)
        )
    else:
        cw.put(fmt.Chunks.Mesh.FLAGS, xray_io.PackedWriter().putf('B', 1))


def remove_bad_geometry(bm, bml, bpy_obj):
    bad_vgroups = [
        vertex_group.name.startswith(utils.BAD_VTX_GROUP_NAME) \
        for vertex_group in bpy_obj.vertex_groups
    ]
    bad_verts = [
        vertex for vertex in bm.verts \
        if any(bad_vgroups[k] for k in vertex[bml].keys())
    ]
    if bad_verts:
        log.warn(text.warn.object_skip_geom.format(utils.BAD_VTX_GROUP_NAME))
        if version_utils.IS_28:
            ops_context = 'VERTS'
        else:
            ops_context = 1
        bmesh.ops.delete(bm, geom=bad_verts, context=ops_context)

    return bad_vgroups


def export_vertices(cw, bm):
    writer = xray_io.PackedWriter()
    writer.putf('I', len(bm.verts))
    for vertex in bm.verts:
        writer.putv3f(vertex.co)
    cw.put(fmt.Chunks.Mesh.VERTS, writer)


def export_faces(cw, bm, bpy_obj):
    uvs = []
    vtx = []
    fcs = []
    uv_layer = bm.loops.layers.uv.active
    if not uv_layer:
        raise utils.AppError(text.error.object_no_uv.format(bpy_obj.name))

    writer = xray_io.PackedWriter()
    writer.putf('I', len(bm.faces))
    for fidx in bm.faces:
        for i in (0, 2, 1):
            writer.putf('II', fidx.verts[i].index, len(uvs))
            uvc = fidx.loops[i][uv_layer].uv
            uvs.append((uvc[0], 1 - uvc[1]))
            vtx.append(fidx.verts[i].index)
            fcs.append(fidx.index)
    cw.put(fmt.Chunks.Mesh.FACES, writer)

    return uvs, vtx, fcs


@log.with_context('export-mesh')
def export_mesh(bpy_obj, bpy_root, cw, context):
    log.update(mesh=bpy_obj.data.name)
    export_version(cw)
    export_mesh_name(cw, bpy_obj, bpy_root)

    if context.smoothing_out_of == 'SHARP_EDGES':
        use_split_normals = False
    else:
        use_split_normals = True
    bm = utils.convert_object_to_space_bmesh(
        bpy_obj, bpy_root.matrix_world, local=False, split_normals=use_split_normals
    )
    bml = bm.verts.layers.deform.verify()

    bad_vgroups = remove_bad_geometry(bm, bml, bpy_obj)

    export_bbox(cw, bm)
    export_flags(cw, bpy_obj)

    bmesh.ops.triangulate(bm, faces=bm.faces)

    export_vertices(cw, bm)

    uvs, vtx, fcs = export_faces(cw, bm, bpy_obj)

    if bpy_root.type == 'ARMATURE':
        bones_names = []
        for bone in bpy_root.data.bones:
            if bone.xray.exportable:
                bones_names.append(bone.name)
    else:
        bones_names = None

    wmaps = []
    wmaps_cnt = 0
    for vertex_group, bad in zip(bpy_obj.vertex_groups, bad_vgroups):
        if bad:
            wmaps.append(None)
            continue
        if not bones_names is None:
            if vertex_group.name not in bones_names:
                wmaps.append(None)
                continue
        wmaps.append(([], wmaps_cnt))
        wmaps_cnt += 1

    wrefs = []
    for vidx, vertex in enumerate(bm.verts):
        wr = []
        wrefs.append(wr)
        vw = vertex[bml]
        for vgi in vw.keys():
            wmap = wmaps[vgi]
            if wmap is None:
                continue
            wr.append((1 + wmap[1], len(wmap[0])))
            wmap[0].append(vidx)

    writer = xray_io.PackedWriter()
    writer.putf('I', len(uvs))
    for i in range(len(uvs)):
        vidx = vtx[i]
        wref = wrefs[vidx]
        writer.putf('B', 1 + len(wref)).putf('II', 0, i)
        for ref in wref:
            writer.putf('II', *ref)
    cw.put(fmt.Chunks.Mesh.VMREFS, writer)

    writer = xray_io.PackedWriter()
    sfaces = {
        (m.name, mi) if m else (None, mi): [
            fidx for fidx, face in enumerate(bm.faces) \
            if face.material_index == mi
        ]
        for mi, m in enumerate(bpy_obj.data.materials)
    }

    materials = {}
    for (mat_name, mat_id), face_ids in sfaces.items():
        if not materials.get(mat_name, None):
            materials[mat_name] = {'materials_ids': [], 'faces_count': []}
        materials[mat_name]['materials_ids'].append(mat_id)
        materials[mat_name]['faces_count'].append(len(face_ids))

    used_material_names = set()
    for (material_name, material_index), faces_indices in sfaces.items():
        if faces_indices:
            if material_name is None:
                raise utils.AppError(
                    text.get_text(text.error.obj_empty_mat),
                    log.props(object=bpy_obj.name)
                )
            used_material_names.add(material_name)

    if not sfaces:
        raise utils.AppError(
            text.get_text(text.error.obj_no_mat),
            log.props(object=bpy_obj.name)
        )
    writer.putf('H', len(used_material_names))
    for mat_name, mat_data in materials.items():
        if mat_name in used_material_names:
            faces_count = sum(mat_data['faces_count'])
            writer.puts(mat_name).putf('I', faces_count)
            for mat_id in mat_data['materials_ids']:
                fidxs = sfaces[(mat_name, mat_id)]
                for fidx in fidxs:
                    writer.putf('I', fidx)
    cw.put(fmt.Chunks.Mesh.SFACE, writer)

    writer = xray_io.PackedWriter()
    sgroups = []
    if context.soc_sgroups:
        sgroups = tuple(_export_sg_soc(bm.faces))
        # check for Maya compatibility
        err = _check_sg_soc(bm.edges, sgroups)
        if err:
            log.warn(err)
    else:
        sgroups = _export_sg_new(bm.faces)
    for sgroup in sgroups:
        writer.putf('I', sgroup)
    cw.put(fmt.Chunks.Mesh.SG, writer)

    writer = xray_io.PackedWriter()
    writer.putf('I', 1 + wmaps_cnt)
    if version_utils.IS_28:
        texture = bpy_obj.data.uv_layers.active
    else:
        texture = bpy_obj.data.uv_textures.active
    writer.puts(texture.name).putf('B', 2).putf('B', 1).putf('B', 0)
    writer.putf('I', len(uvs))
    for uvc in uvs:
        writer.putf('ff', *uvc)
    for vidx in vtx:
        writer.putf('I', vidx)
    for fidx in fcs:
        writer.putf('I', fidx)
    for vgi, vertex_group in enumerate(bpy_obj.vertex_groups):
        wmap = wmaps[vgi]
        if wmap is None:
            continue
        vtx = wmap[0]
        writer.puts(vertex_group.name.lower())
        writer.putf('B', 1).putf('B', 0).putf('B', 1)
        writer.putf('I', len(vtx))
        for vidx in vtx:
            writer.putf('f', bm.verts[vidx][bml][vgi])
        writer.putf(str(len(vtx)) + 'I', *vtx)
    cw.put(fmt.Chunks.Mesh.VMAPS2, writer)
    return used_material_names
