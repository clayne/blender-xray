# blender modules
import bpy

# addon modules
from .. import fmt
from .... import text
from .... import log
from .... import rw


def _write_glow(glows_writer, glow_obj, level):
    # position
    glows_writer.putf(
        '<3f',
        glow_obj.location[0],
        glow_obj.location[2],
        glow_obj.location[1]
    )
    faces_count = len(glow_obj.data.polygons)
    if not faces_count:
        raise log.AppError(
            text.error.level_bad_glow,
            log.props(
                object=glow_obj.name,
                faces_count=faces_count
            )
        )
    dim_max = max(glow_obj.dimensions)
    glow_radius = dim_max / 2
    if glow_radius < 0.0005:
        raise log.AppError(
            text.error.level_bad_glow_radius,
            log.props(
                object=glow_obj.name,
                radius=glow_radius
            )
        )
    glows_writer.putf('<f', glow_radius)
    if not len(glow_obj.data.materials):
        raise BaseException('glow object "{}" has no material'.format(glow_obj.name))
    material = glow_obj.data.materials[0]
    if level.materials.get(material, None) is None:
        level.materials[material] = level.active_material_index
        shader_index = level.active_material_index
        level.active_material_index += 1
    else:
        shader_index = level.materials[material]
    # shader index
    # +1 - skip first empty shader
    glows_writer.putf('<H', shader_index + 1)


def write_glows(level_writer, level_object, level):
    glows_writer = rw.write.PackedWriter()
    glows_count = 0

    for child_name in level.visuals_cache.children[level_object.name]:
        child_obj = bpy.data.objects[child_name]
        if child_obj.name.startswith('glows'):

            for glow_name in level.visuals_cache.children[child_obj.name]:
                glow_obj = bpy.data.objects[glow_name]
                _write_glow(glows_writer, glow_obj, level)
                glows_count += 1

    if not glows_count:
        raise log.AppError(
            text.error.level_no_glow,
            log.props(object=level_object.name)
        )

    level_writer.put(fmt.Chunks13.GLOWS, glows_writer)
