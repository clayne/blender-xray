import bpy, mathutils, bmesh

from .. import xray_io
from ..level import swi as imp_swi
from . import fmt


class Visual(object):
    def __init__(self):
        self.format_version = None
        self.model_type = None
        self.shader_id = None
        self.name = None
        self.vertices = None
        self.uvs = None
        self.uvs_lmap = None
        self.triangles = None
        self.indices_count = None
        self.indices = None


def assign_material(bpy_object, shader_id, materials):
    bpy_object.data.materials.append(materials[shader_id])


def create_object(name, bpy_mesh):
    bpy_object = bpy.data.objects.new(name, bpy_mesh)
    bpy.context.scene.collection.objects.link(bpy_object)
    return bpy_object


def create_visual(bpy_mesh, visual, level, geometry_key):

    if not bpy_mesh:
        mesh = bmesh.new()

        # import vertices
        for vertex_coord in visual.vertices:
            mesh.verts.new(vertex_coord)

        mesh.verts.ensure_lookup_table()
        mesh.verts.index_update()

        # import triangles
        for triangle in visual.triangles:
            mesh.faces.new((
                mesh.verts[triangle[0]],
                mesh.verts[triangle[1]],
                mesh.verts[triangle[2]]
            ))

        mesh.faces.ensure_lookup_table()

        # import uvs
        uv_layer = mesh.loops.layers.uv.new('Texture')
        if visual.uvs_lmap:
            lmap_uv_layer = mesh.loops.layers.uv.new('Light Map')
            for face in mesh.faces:
                for loop in face.loops:
                    loop[uv_layer].uv = visual.uvs[loop.vert.index]
                    loop[lmap_uv_layer].uv = visual.uvs_lmap[loop.vert.index]
        else:
            for face in mesh.faces:
                for loop in face.loops:
                    loop[uv_layer].uv = visual.uvs[loop.vert.index]

        # normals
        mesh.normal_update()

        # create mesh
        bpy_mesh = bpy.data.meshes.new(visual.name)
        mesh.to_mesh(bpy_mesh)
        del mesh
        level.loaded_geometry[geometry_key] = bpy_mesh

    else:
        bpy_mesh = level.loaded_geometry[geometry_key]

    bpy_object = create_object(visual.name, bpy_mesh)
    return bpy_object


def import_gcontainer(data, visual, level):
    packed_reader = xray_io.PackedReader(data)

    vb_index = packed_reader.getf('<I')[0]
    vb_offset = packed_reader.getf('<I')[0]
    vb_size = packed_reader.getf('<I')[0]
    ib_index = packed_reader.getf('<I')[0]
    ib_offset = packed_reader.getf('<I')[0]
    ib_size = packed_reader.getf('<I')[0]

    vb_slice = slice(vb_offset, vb_offset + vb_size)
    geometry_key = (vb_index, vb_offset, vb_size, ib_index, ib_offset, ib_size)
    bpy_mesh = level.loaded_geometry.get(geometry_key, None)
    if bpy_mesh:
        return bpy_mesh, geometry_key
    visual.vertices = level.vertex_buffers[vb_index].position[vb_slice]
    visual.uvs = level.vertex_buffers[vb_index].uv[vb_slice]
    visual.uvs_lmap = level.vertex_buffers[vb_index].uv_lmap[vb_slice]
    visual.indices = level.indices_buffers[ib_index][
        ib_offset : ib_offset + ib_size
    ]
    visual.indices_count = ib_size

    return bpy_mesh, geometry_key


def import_vcontainer(data):
    pass


def import_indices(data):
    pass


def import_vertices(data):
    pass


def import_texture(data):
    pass


def import_fastpath(data):
    pass


def check_unread_chunks(chunks):
    chunks_ids = list(chunks.keys())
    chunks_ids.sort()
    if chunks:
        raise BaseException('There are unread chunks: {}'.format(chunks_ids))


def import_children_l(data):
    packed_reader = xray_io.PackedReader(data)
    children_count = packed_reader.getf('I')[0]

    for child_index in range(children_count):
        child = packed_reader.getf('I')[0]


def import_hierrarhy_visual(chunks):
    children_l_data = chunks.pop(fmt.Chunks.CHILDREN_L)
    import_children_l(children_l_data)
    del children_l_data

    check_unread_chunks(chunks)


def import_geometry(chunks, visual, level):
    gcontainer_data = chunks.pop(fmt.Chunks.GCONTAINER)
    bpy_mesh, geometry_key = import_gcontainer(gcontainer_data, visual, level)
    del gcontainer_data

    fastpath_data = chunks.pop(fmt.Chunks.FASTPATH, None)    # optional chunk
    if fastpath_data:
        import_fastpath(fastpath_data)
    del fastpath_data
    return bpy_mesh, geometry_key


def convert_indices_to_triangles(visual):
    visual.triangles = []
    for index in range(0, visual.indices_count, 3):
        visual.triangles.append((
            visual.indices[index],
            visual.indices[index + 2],
            visual.indices[index + 1]
        ))
    del visual.indices
    del visual.indices_count


def import_normal_visual(chunks, visual, level):
    visual.name = 'NORMAL'
    bpy_mesh, geometry_key = import_geometry(chunks, visual, level)
    check_unread_chunks(chunks)

    if not bpy_mesh:
        convert_indices_to_triangles(visual)
        bpy_object = create_visual(bpy_mesh, visual, level, geometry_key)
        assign_material(bpy_object, visual.shader_id, level.materials)
    else:
        bpy_object = create_object('NORMAL', bpy_mesh)


def ogf_color(packed_reader):
    rgb = packed_reader.getf('3f')
    hemi = packed_reader.getf('f')[0]
    sun = packed_reader.getf('f')[0]


def import_tree_def_2(chunks):
    tree_def_2_data = chunks.pop(fmt.Chunks.TREEDEF2)
    packed_reader = xray_io.PackedReader(tree_def_2_data)
    del tree_def_2_data

    tree_xform = packed_reader.getf('16f')
    ogf_color(packed_reader)    # c_scale
    ogf_color(packed_reader)    # c_bias

    return tree_xform


def set_tree_transforms(bpy_object, xform):
    transform_matrix = mathutils.Matrix((
        (xform[0], xform[1], xform[2], xform[3]),
        (xform[4], xform[5], xform[6], xform[7]),
        (xform[8], xform[9], xform[10], xform[11]),
        (xform[12], xform[13], xform[14], xform[15])
        ))
    transform_matrix.transpose()
    translate, rotate, scale = transform_matrix.decompose()
    bpy_object.location = translate[0], translate[2], translate[1]
    bpy_object.scale = scale[0], scale[2], scale[1]
    rotate = rotate.to_euler('ZXY')
    bpy_object.rotation_euler = -rotate[0], -rotate[2], -rotate[1]


def import_tree_st_visual(chunks, visual, level):
    visual.name = 'TREE_ST'
    bpy_mesh, geometry_key = import_geometry(chunks, visual, level)
    tree_xform = import_tree_def_2(chunks)
    if not bpy_mesh:
        convert_indices_to_triangles(visual)
        bpy_object = create_visual(bpy_mesh, visual, level, geometry_key)
        assign_material(bpy_object, visual.shader_id, level.materials)
    else:
        bpy_object = create_object('TREE_ST', bpy_mesh)
    set_tree_transforms(bpy_object, tree_xform)
    check_unread_chunks(chunks)


def import_swidata(chunks, visual, level):
    swi_data = chunks.pop(fmt.Chunks.SWIDATA)
    packed_reader = xray_io.PackedReader(swi_data)
    del swi_data
    swi = imp_swi.import_slide_window_item(packed_reader)
    del packed_reader
    return swi


def import_progressive_visual(chunks, visual, level):
    visual.name = 'PROGRESSIVE'
    bpy_mesh, geometry_key = import_geometry(chunks, visual, level)
    swi = import_swidata(chunks, visual, level)

    visual.indices = visual.indices[swi[0].offset : ]
    visual.indices_count = swi[0].triangles_count * 3
    convert_indices_to_triangles(visual)

    check_unread_chunks(chunks)

    if not bpy_mesh:
        bpy_object = create_visual(bpy_mesh, visual, level, geometry_key)
        assign_material(bpy_object, visual.shader_id, level.materials)
    else:
        bpy_object = create_object('PROGRESSIVE', bpy_mesh)


def import_swicontainer(chunks):
    swicontainer_data = chunks.pop(fmt.Chunks.SWICONTAINER)
    packed_reader = xray_io.PackedReader(swicontainer_data)
    del swicontainer_data
    swi_index = packed_reader.getf('I')[0]
    return swi_index


def import_lod_def_2(data):
    packed_reader = xray_io.PackedReader(data)
    for i in range(8):
        for j in range(4):
            coord_x, coord_y, coord_z = packed_reader.getf('3f')
            coord_u, coord_v = packed_reader.getf('2f')
            hemi = packed_reader.getf('I')[0]
            sun = packed_reader.getf('B')[0]
            pad = packed_reader.getf('3B')


def import_lod_visual(chunks, visual, level):

    children_l_data = chunks.pop(fmt.Chunks.CHILDREN_L)
    import_children_l(children_l_data)
    del children_l_data

    lod_def_2_data = chunks.pop(fmt.Chunks.LODDEF2)
    import_lod_def_2(lod_def_2_data)
    del lod_def_2_data

    check_unread_chunks(chunks)


def import_tree_pm_visual(chunks, visual, level):
    visual.name = 'TREE_PM'
    bpy_mesh, geometry_key = import_geometry(chunks, visual, level)
    swi_index = import_swicontainer(chunks)
    tree_xform = import_tree_def_2(chunks)

    if not bpy_mesh:
        swi = level.swis[swi_index]
        visual.indices = visual.indices[swi[0].offset : ]
        visual.indices_count = swi[0].triangles_count * 3
        convert_indices_to_triangles(visual)

        bpy_object = create_visual(bpy_mesh, visual, level, geometry_key)
        assign_material(bpy_object, visual.shader_id, level.materials)
    else:
        bpy_object = create_object('TREE_PM', bpy_mesh)
    set_tree_transforms(bpy_object, tree_xform)
    check_unread_chunks(chunks)


def import_model(chunks, visual, level):

    if visual.model_type == fmt.ModelType.NORMAL:
        import_normal_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType.HIERRARHY:
        bpy_obj = import_hierrarhy_visual(chunks)

    elif visual.model_type == fmt.ModelType.PROGRESSIVE:
        bpy_obj = import_progressive_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType.TREE_ST:
        bpy_obj = import_tree_st_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType.TREE_PM:
        bpy_obj = import_tree_pm_visual(chunks, visual, level)

    elif visual.model_type == fmt.ModelType.LOD:
        bpy_obj = import_lod_visual(chunks, visual, level)

    else:
        raise BaseException('unsupported model type: {:x}'.format(
            visual.model_type
        ))


def import_bounding_sphere(packed_reader):
    center = packed_reader.getf('<3f')[0]
    redius = packed_reader.getf('<f')[0]


def import_bounding_box(packed_reader):
    bbox_min = packed_reader.getf('<3f')[0]
    bbox_max = packed_reader.getf('<3f')[0]


def check_version(visual):
    if visual.format_version not in fmt.SUPPORT_FORMAT_VERSIONS:
        raise BaseException(
            'Unsupported ogf format version: {}'.format(visual.format_version)
        )


def import_header(data, visual):
    packed_reader = xray_io.PackedReader(data)
    visual.format_version = packed_reader.getf('<B')[0]
    check_version(visual)
    visual.model_type = packed_reader.getf('<B')[0]
    visual.shader_id = packed_reader.getf('<H')[0]
    import_bounding_box(packed_reader)
    import_bounding_sphere(packed_reader)


def import_main(chunks, visual, level):
    header_chunk_data = chunks.pop(fmt.Chunks.HEADER)
    import_header(header_chunk_data, visual)
    import_model(chunks, visual, level)


def get_ogf_chunks(data):
    chunked_reader = xray_io.ChunkedReader(data)
    del data
    chunks = {}
    chunks_ids = set()
    for chunk_id, chunkd_data in chunked_reader:
        chunks[chunk_id] = chunkd_data
        chunks_ids.add(hex(chunk_id))
    del chunked_reader
    return chunks, chunks_ids


def import_(data, level, chunks):
    chunks, visual_chunks_ids = get_ogf_chunks(data)
    visual = Visual()
    import_main(chunks, visual, level)
