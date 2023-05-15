# addon modules
from .. import fmt
from ... import level


def get_level_material(lvl, visual):
    material_key = (visual.shader_id, visual.texture_id)
    bpy_material = lvl.materials.get(material_key, None)

    if bpy_material:
        return bpy_material

    if lvl.shaders and lvl.textures:
        shader_raw = lvl.shaders[visual.shader_id]
        texture_raw = lvl.textures[visual.texture_id]

    else:
        shader_raw = lvl.shaders_or_textures[visual.shader_id]
        texture_raw = lvl.shaders_or_textures[visual.texture_id]

    shader_data = shader_raw + '/' + texture_raw
    bpy_material, bpy_image = level.imp.shaders.import_shader(
        lvl,
        lvl.context,
        shader_data
    )
    lvl.materials[material_key] = bpy_material
    lvl.images[visual.texture_id] = bpy_image

    return bpy_material


def assign_level_material(bpy_mesh, visual, lvl):
    if (
            visual.format_version == fmt.FORMAT_VERSION_4 or
            lvl.xrlc_version >= level.fmt.VERSION_12
        ):
        shader_id = visual.shader_id
        bpy_material = lvl.materials[shader_id]

        if visual.format_version == fmt.FORMAT_VERSION_4:
            trees = (fmt.ModelType_v4.TREE_ST, fmt.ModelType_v4.TREE_PM)

            if visual.model_type in trees:
                bpy_material.xray.light_vert_color = ''
                bpy_material.xray.sun_vert_color = ''

    else:
        bpy_material = get_level_material(
            lvl,
            visual.shader_id,
            visual.texture_id
        )
    bpy_mesh.materials.append(bpy_material)
