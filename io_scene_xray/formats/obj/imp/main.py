# standart modules
import os

# blender modules
import bpy
import mathutils

# addon modules
from . import bone
from . import mesh
from .. import fmt
from ... import skl
from ... import motions
from .... import text
from .... import log
from .... import utils
from .... import rw


def import_main(file_path, context, chunked_reader):
    object_name = os.path.basename(file_path.lower())

    bpy_arm_obj = None
    unread_chunks = []
    renamemap = {}

    for (chunk_id, chunk_data) in chunked_reader:
        # version
        if chunk_id == fmt.Chunks.Object.VERSION:
            reader = rw.read.PackedReader(chunk_data)
            ver = reader.getf('<H')[0]
            if ver != fmt.CURRENT_OBJECT_VERSION:
                raise log.AppError(
                    text.error.object_unsupport_format_ver,
                    log.props(version=ver)
                )

        # meshes
        elif chunk_id == fmt.Chunks.Object.MESHES:
            meshes_data = chunk_data

        # surfaces
        elif chunk_id in (
                fmt.Chunks.Object.SURFACES,
                fmt.Chunks.Object.SURFACES1,
                fmt.Chunks.Object.SURFACES2
            ):

            reader = rw.read.PackedReader(chunk_data)
            surfaces_count = reader.int()

            if chunk_id == fmt.Chunks.Object.SURFACES:
                try:
                    xrlc_reader = rw.read.PackedReader(
                        chunked_reader.next(fmt.Chunks.Object.SURFACES_XRLC)
                    )
                    xrlc_shaders = [
                        xrlc_reader.gets() for _ in range(surfaces_count)
                    ]
                except:
                    xrlc_shaders = ['default' for _ in range(surfaces_count)]

            for surface_index in range(surfaces_count):
                if chunk_id == fmt.Chunks.Object.SURFACES:
                    name = reader.gets()
                    eshader = reader.gets()
                    flags = reader.getf('<B')[0]
                    reader.skip(4 + 4)    # fvf and TCs count
                    texture = reader.gets()
                    vmap = reader.gets()
                    gamemtl = 'default'
                    cshader = xrlc_shaders[surface_index]
                    if texture != vmap or not (texture and vmap):
                        renamemap[vmap.lower()] = vmap
                    else:    # old format (Objects\Rainbow\lest.object)
                        vmap = 'Texture'

                else:
                    name = reader.gets()
                    eshader = reader.gets()
                    cshader = reader.gets()
                    if chunk_id == fmt.Chunks.Object.SURFACES2:
                        gamemtl = reader.gets()
                    else:
                        gamemtl = 'default'
                    texture = reader.gets()
                    vmap = reader.gets()
                    flags = reader.int()
                    reader.skip(4 + 4)    # fvf and ?
                    if texture != vmap or not (texture and vmap):
                        renamemap[vmap.lower()] = vmap
                    else:    # old format (Objects\corps\corp_BYAKA.object)
                        vmap = 'Texture'
                    renamemap[vmap.lower()] = vmap

                # create material
                bpy_material, bpy_image = utils.material.get_material(
                    context,
                    name,
                    texture,
                    eshader,
                    cshader,
                    gamemtl,
                    flags,
                    vmap
                )
                context.loaded_materials[name] = bpy_material

        # bones
        elif chunk_id in (
                fmt.Chunks.Object.BONES,
                fmt.Chunks.Object.BONES1
            ):
            if chunk_id == fmt.Chunks.Object.BONES:
                reader = rw.read.PackedReader(chunk_data)
                bones_count = reader.int()
                if not bones_count:
                    continue    # Do not create an armature if zero bones
            if bpy and (bpy_arm_obj is None):
                bpy_armature = bpy.data.armatures.new(object_name)
                utils.version.set_arm_display_type(bpy_armature)
                bpy_arm_obj = bpy.data.objects.new(object_name, bpy_armature)
                bpy_armature.xray.joint_limits_type = 'XRAY'
                utils.version.set_object_show_xray(bpy_arm_obj, True)
                if not utils.version.IS_28:
                    bpy_armature.use_auto_ik = True
                utils.version.link_object(bpy_arm_obj)
                utils.version.set_active_object(bpy_arm_obj)
            if chunk_id == fmt.Chunks.Object.BONES:
                for _ in range(bones_count):
                    name = reader.gets()
                    parent = reader.gets()
                    vmap = reader.gets()
                    offset = reader.getv3fp()
                    rotate = reader.getv3fp()
                    length = reader.getf('<f')[0]
                    rotate = rotate[2], rotate[1], rotate[0]
                    bpy_bone = bone.create_bone(
                        context, bpy_arm_obj,
                        name, parent, vmap,
                        offset, rotate, length,
                        renamemap
                    )
                    xray = bpy_bone.xray
                    xray.mass.gamemtl = 'default_object'
                    xray.mass.value = 10
                    ik = xray.ikjoint

                    ik.lim_x_min, ik.lim_x_max = 0, 0
                    ik.lim_x_spr, ik.lim_x_dmp = 1, 1

                    ik.lim_y_min, ik.lim_y_max = 0, 0
                    ik.lim_y_spr, ik.lim_y_dmp = 1, 1

                    ik.lim_z_min, ik.lim_z_max = 0, 0
                    ik.lim_z_spr, ik.lim_z_dmp = 1, 1

                    ik.spring = 1
                    ik.damping = 1
            else:
                bones_chunks = []
                bone_id_by_name = {}
                bones_reader = rw.read.ChunkedReader(chunk_data)
                for index, (_, bone_data) in enumerate(bones_reader):
                    bone_chunks = rw.utils.get_chunks(bone_data)
                    def_data = bone_chunks[fmt.Chunks.Bone.DEF]
                    def_reader = rw.read.PackedReader(def_data)
                    bone_name = def_reader.gets()
                    bones_chunks.append(bone_chunks)
                    bone_id_by_name[bone_name] = index
                imported_bones = set()
                for bone_chunks in bones_chunks:
                    bone.import_bone(
                        context,
                        bone_chunks,
                        bpy_arm_obj,
                        renamemap,
                        imported_bones,
                        bones_chunks,
                        bone_id_by_name
                    )
            for bone_ in bpy_arm_obj.pose.bones:
                bone_.rotation_mode = 'ZXY'

        # bones partitions
        elif chunk_id in (
                fmt.Chunks.Object.PARTITIONS0,
                fmt.Chunks.Object.PARTITIONS1
            ):
            reader = rw.read.PackedReader(chunk_data)
            parts_count = reader.int()
            utils.version.set_active_object(bpy_arm_obj)
            bpy.ops.object.mode_set(mode='POSE')
            obj_pose = bpy_arm_obj.pose
            try:
                for part_id in range(parts_count):
                    part_name = reader.gets()
                    bone_group = obj_pose.bone_groups.new(name=part_name)
                    bones_count = reader.int()
                    for bone_id in range(bones_count):
                        if chunk_id == fmt.Chunks.Object.PARTITIONS1:
                            bone_key = reader.gets()
                        else:
                            bone_key = reader.int()
                        obj_pose.bones[bone_key].bone_group = bone_group
            finally:
                bpy.ops.object.mode_set(mode='OBJECT')

        # motions
        elif chunk_id == fmt.Chunks.Object.MOTIONS and context.import_motions:
            reader = rw.read.PackedReader(chunk_data)
            skl_context = skl.imp.ImportSklContext()
            skl_context.bpy_arm_obj = bpy_arm_obj
            skl_context.motions_filter = motions.utilites.MOTIONS_FILTER_ALL
            skl_context.add_actions_to_motion_list = True
            skl_context.filename = object_name
            motions.imp.import_motions(reader, skl_context)

        # lib version
        elif chunk_id == fmt.Chunks.Object.LIB_VERSION:
            pass  # skip obsolete chunk

        # other chunks
        else:
            unread_chunks.append((chunk_id, chunk_data))

    # import meshes
    mesh_objects = []
    for mesh_id, mesh_data in rw.read.ChunkedReader(meshes_data):
        mesh_reader = rw.read.ChunkedReader(mesh_data)
        mesh_obj = mesh.import_mesh(context, mesh_reader, renamemap)
        utils.version.link_object(mesh_obj)
        mesh_objects.append(mesh_obj)

        if bpy_arm_obj:
            arm_mod = mesh_obj.modifiers.new(name='Armature', type='ARMATURE')
            arm_mod.object = bpy_arm_obj
            mesh_obj.parent = bpy_arm_obj

    # search root-object
    bpy_obj = bpy_arm_obj
    if bpy_obj is None:
        if len(mesh_objects) == 1:
            bpy_obj = mesh_objects[0]
            bpy_obj.name = object_name
        else:
            bpy_obj = bpy.data.objects.new(object_name, None)
            utils.version.link_object(bpy_obj)
            for mesh_obj in mesh_objects:
                mesh_obj.parent = bpy_obj

    xray = bpy_obj.xray
    xray.version = context.version
    xray.isroot = True

    # set export path
    if context.objects_folder:
        path_lower = file_path.lower()
        objs_lower = context.objects_folder.lower()
        if path_lower.startswith(objs_lower):
            length = len(objs_lower)
            xray.export_path = os.path.dirname(path_lower)[length : ]

    for (chunk_id, chunk_data) in unread_chunks:
        reader = rw.read.PackedReader(chunk_data)

        # transform
        if chunk_id == fmt.Chunks.Object.TRANSFORM:
            pos = reader.getv3fp()
            rot = reader.getv3fp()
            bpy_obj.matrix_basis = context.multiply(
                bpy_obj.matrix_basis,
                mathutils.Matrix.Translation(pos),
                mathutils.Euler(rot, 'YXZ').to_matrix().to_4x4()
            )

        # flags
        elif chunk_id == fmt.Chunks.Object.FLAGS:
            length_data = reader.get_size()
            if length_data == 4:
                flags_fmt = 'I'
            elif length_data == 1:    # old object format
                flags_fmt = 'B'
            xray.flags = reader.getf('<' + flags_fmt)[0]

        # userdata
        elif chunk_id == fmt.Chunks.Object.USERDATA:
            xray.userdata = reader.gets(
                onerror=lambda e: log.warn(
                    text.warn.object_bad_userdata,
                    error=str(e),
                    file=file_path
                )
            )

        # LOD reference
        elif chunk_id == fmt.Chunks.Object.LOD_REF:
            xray.lodref = reader.gets()

        # revision
        elif chunk_id == fmt.Chunks.Object.REVISION:
            xray.revision.owner = reader.gets()
            xray.revision.ctime = reader.getf('<i')[0]
            xray.revision.moder = reader.gets()
            xray.revision.mtime = reader.getf('<i')[0]

        # motion references for soc
        elif chunk_id == fmt.Chunks.Object.MOTION_REFS:
            mrefs = xray.motionrefs_collection
            for mref in reader.gets().split(','):
                mrefs.add().name = mref

        # motion references for cs/cop
        elif chunk_id == fmt.Chunks.Object.SMOTIONS3:
            mrefs = xray.motionrefs_collection
            count = reader.int()
            for _ in range(count):
                mrefs.add().name = reader.gets()

        # unknown chunk
        else:
            log.debug(
                'unknown chunk',
                chunk_id=chunk_id,
                chunk_size=len(chunk_data)
            )

    return bpy_obj
