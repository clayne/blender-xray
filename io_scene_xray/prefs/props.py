import os

import bpy

from .. import xray_ltx, version_utils
from ..obj import props as general_obj_props
from ..obj.imp import props as obj_imp_props
from ..obj.exp import props as obj_exp_props
from ..anm import props as anm_props
from ..skl import props as skl_props
from ..omf import props as omf_props
from ..bones import props as bones_props
from ..details import props as details_props


def update_menu_func(self, context):
    from .. import plugin
    plugin.append_menu_func()


def build_auto_id(prop):
    return prop + '_auto'


__AUTO_PROPS__ = [
    'gamedata_folder',
    'textures_folder',
    'gamemtl_file',
    'eshader_file',
    'cshader_file',
    'objects_folder'
]

fs_props = {
    'gamedata_folder': ('$game_data$', None),
    'textures_folder': ('$game_textures$', None),
    'gamemtl_file': ('$game_data$', 'gamemtl.xr'),
    'eshader_file': ('$game_data$', 'shaders.xr'),
    'cshader_file': ('$game_data$', 'shaders_xrlc.xr'),
    'objects_folder': ('$objects$', None)
}


def _auto_path(prefs, self_name, path_suffix, checker):
    if prefs.fs_ltx_file:
        if not os.path.exists(prefs.fs_ltx_file):
            return ''
        try:
            fs = xray_ltx.StalkerLtxParser(prefs.fs_ltx_file)
        except:
            print('Invalid fs.ltx syntax')
            return ''
        prop_key, file_name = fs_props[self_name]
        dir_path = fs.values[prop_key]
        if file_name:
            result = os.path.join(dir_path, file_name)
        else:
            result = dir_path
        return result
    for prop in __AUTO_PROPS__:
        if prop == self_name:
            continue
        value = getattr(prefs, prop)
        if not value:
            continue
        if prop == 'objects_folder':
            continue
        result = os.path.normpath(value)
        if prop != 'gamedata_folder':
            dirname = os.path.dirname(result)
            if dirname == result:
                continue  # path.dirname('T:') == 'T:'
            result = dirname
        if path_suffix:
            result = os.path.join(result, path_suffix)
            if self_name == 'objects_folder':
                result = os.path.abspath(result)
        if checker(result):
            return result
    return ''


path_props_suffix_values = {
    'gamedata_folder': '',
    'textures_folder': 'textures',
    'gamemtl_file': 'gamemtl.xr',
    'eshader_file': 'shaders.xr',
    'cshader_file': 'shaders_xrlc.xr',
    'objects_folder': os.path.join('..', 'rawdata', 'objects')
}

FILE = 'FILE'
DIRECTORY = 'DIRECTORY'
path_props_types = {
    'gamedata_folder': DIRECTORY,
    'textures_folder': DIRECTORY,
    'gamemtl_file': FILE,
    'eshader_file': FILE,
    'cshader_file': FILE,
    'objects_folder': DIRECTORY
}


def update_paths(prefs, context):
    for path_prop, suffix in path_props_suffix_values.items():
        if getattr(prefs, path_prop):
            setattr(prefs, build_auto_id(path_prop), getattr(prefs, path_prop))
            continue
        prop_type = path_props_types[path_prop]
        if prop_type == DIRECTORY:
            cheker_function = os.path.isdir
        elif prop_type == FILE:
            cheker_function = os.path.isfile
        path_value = _auto_path(prefs, path_prop, suffix, cheker_function)
        setattr(prefs, build_auto_id(path_prop), path_value)


def update_keymap(self, context):
    from .. import hotkeys
    keymaps, keymap_item = hotkeys.io_scene_xray_keymaps[hotkeys.obj_imp_keymap.operator_id]
    keymap_item.type = self.import_object_key
    keymap_item.shift = self.import_object_shift

    keymaps, keymap_item = hotkeys.io_scene_xray_keymaps[hotkeys.obj_exp_keymap.operator_id]
    keymap_item.type = self.export_object_key
    keymap_item.shift = self.export_object_shift


custom_props_category_items = (
    ('OBJECT', 'Object', ''),
    ('MESH', 'Mesh', ''),
    ('MATERIAL', 'Material', ''),
    ('BONE', 'Bone', ''),
    ('ACTION', 'Action', '')
)

custom_props_bone_category_items = (
    ('MAIN', 'Main', ''),
    ('SHAPE', 'Shape', ''),
    ('IK', 'IK', '')
)

xray_custom_properties = {
    'category': bpy.props.EnumProperty(
        name='Custom Property Category',
        default='OBJECT',
        items=custom_props_category_items
    ),
    'bone_category': bpy.props.EnumProperty(
        name='Custom Property Bone Category',
        default='MAIN',
        items=custom_props_bone_category_items
    ),
    # object custom properties names
    'object_flags': bpy.props.StringProperty(
        name='Flags', default='flags'
    ),
    'object_userdata': bpy.props.StringProperty(
        name='Userdata', default='userdata'
    ),
    'object_lod_reference': bpy.props.StringProperty(
        name='LOD Reference', default='lod_reference'
    ),
    'object_owner_name': bpy.props.StringProperty(
        name='Owner Name', default='owner_name'
    ),
    'object_creation_time': bpy.props.StringProperty(
        name='Creation Time', default='creation_time'
    ),
    'object_modif_name': bpy.props.StringProperty(
        name='Modif Name', default='modif_name'
    ),
    'object_modified_time': bpy.props.StringProperty(
        name='Modified Time', default='modified_time'
    ),
    'object_motion_references': bpy.props.StringProperty(
        name='Motion References', default='motion_references'
    ),
    # mesh custom properties names
    'mesh_flags': bpy.props.StringProperty(
        name='Flags', default='flags'
    ),
    # material custom properties names
    'material_two_sided': bpy.props.StringProperty(
        name='Two Sided', default='two_sided'
    ),
    'material_shader': bpy.props.StringProperty(
        name='Shader', default='shader'
    ),
    'material_compile': bpy.props.StringProperty(
        name='Compile', default='compile'
    ),
    'material_game_mtl': bpy.props.StringProperty(
        name='Game Mtl', default='game_mtl'
    ),
    # bone custom properties names
    'bone_game_mtl': bpy.props.StringProperty(
        name='Game Mtl', default='game_mtl'
    ),
    'bone_length': bpy.props.StringProperty(
        name='Length', default='length'
    ),
    'bone_shape_flags': bpy.props.StringProperty(
        name='Shape Flags', default='shape_flags'
    ),
    'bone_shape_type': bpy.props.StringProperty(
        name='Shape Type', default='shape_type'
    ),
    'bone_part': bpy.props.StringProperty(
        name='Bone Part', default='bone_part'
    ),
    # box shape
    'bone_box_shape_rotation': bpy.props.StringProperty(
        name='Box Shape Rotation', default='box_shape_rotation'
    ),
    'bone_box_shape_translate': bpy.props.StringProperty(
        name='Box Shape Translate', default='box_shape_translate'
    ),
    'bone_box_shape_half_size': bpy.props.StringProperty(
        name='Box Shape Half Size', default='box_shape_half_size'
    ),
    # sphere shape
    'bone_sphere_shape_position': bpy.props.StringProperty(
        name='Sphere Shape Position', default='sphere_shape_position'
    ),
    'bone_sphere_shape_radius': bpy.props.StringProperty(
        name='Sphere Shape Radius', default='sphere_shape_radius'
    ),
    # cylinder shape
    'bone_cylinder_shape_position': bpy.props.StringProperty(
        name='Cylinder Shape Position', default='cylinder_shape_position'
    ),
    'bone_cylinder_shape_direction': bpy.props.StringProperty(
        name='Cylinder Shape Direction', default='cylinder_shape_direction'
    ),
    'bone_cylinder_shape_hight': bpy.props.StringProperty(
        name='Cylinder Shape Hight', default='cylinder_shape_hight'
    ),
    'bone_cylinder_shape_radius': bpy.props.StringProperty(
        name='Cylinder Shape Radius', default='cylinder_shape_radius'
    ),
    # ik joint type
    'bone_ik_joint_type': bpy.props.StringProperty(
        name='IK Joint Type', default='ik_joint_type'
    ),
    # limit
    'bone_limit_x_min': bpy.props.StringProperty(
        name='Limit X Min', default='limit_x_min'
    ),
    'bone_limit_x_max': bpy.props.StringProperty(
        name='Limit X Max', default='limit_x_max'
    ),
    'bone_limit_y_min': bpy.props.StringProperty(
        name='Limit Y Min', default='limit_y_min'
    ),
    'bone_limit_y_max': bpy.props.StringProperty(
        name='Limit Y Max', default='limit_y_max'
    ),
    'bone_limit_z_min': bpy.props.StringProperty(
        name='Limit Z Min', default='limit_z_min'
    ),
    'bone_limit_z_max': bpy.props.StringProperty(
        name='Limit Z Max', default='limit_z_max'
    ),
    # spring limit
    'bone_limit_x_spring': bpy.props.StringProperty(
        name='Limit X Spring', default='limit_x_spring'
    ),
    'bone_limit_y_spring': bpy.props.StringProperty(
        name='Limit Y Spring', default='limit_y_spring'
    ),
    'bone_limit_z_spring': bpy.props.StringProperty(
        name='Limit Z Spring', default='limit_z_spring'
    ),
    # damping limit
    'bone_limit_x_damping': bpy.props.StringProperty(
        name='Limit X Damping', default='limit_x_damping'
    ),
    'bone_limit_y_damping': bpy.props.StringProperty(
        name='Limit Y Damping', default='limit_y_damping'
    ),
    'bone_limit_z_damping': bpy.props.StringProperty(
        name='Limit Z Damping', default='limit_z_damping'
    ),
    # spring and damping
    'bone_spring': bpy.props.StringProperty(
        name='Spring', default='spring'
    ),
    'bone_damping': bpy.props.StringProperty(
        name='Damping', default='damping'
    ),
    # mass
    'bone_mass': bpy.props.StringProperty(
        name='Mass', default='mass'
    ),
    'bone_center_of_mass': bpy.props.StringProperty(
        name='Center of Mass', default='center_of_mass'
    ),
    # other
    'bone_ik_flags': bpy.props.StringProperty(
        name='IK Flags', default='ik_flags'
    ),
    'bone_breakable_force': bpy.props.StringProperty(
        name='Breakable Force', default='breakable_force'
    ),
    'bone_breakable_torque': bpy.props.StringProperty(
        name='Breakable Torque', default='breakable_torque'
    ),
    'bone_friction': bpy.props.StringProperty(
        name='Friction', default='friction'
    ),
    # action custom properties names
    'action_fps': bpy.props.StringProperty(
        name='FPS', default='fps'
    ),
    'action_speed': bpy.props.StringProperty(
        name='Speed', default='speed'
    ),
    'action_accrue': bpy.props.StringProperty(
        name='Accrue', default='accrue'
    ),
    'action_falloff': bpy.props.StringProperty(
        name='Falloff', default='falloff'
    ),
    'action_bone_part': bpy.props.StringProperty(
        name='Bone Part', default='bone_part'
    ),
    'action_flags': bpy.props.StringProperty(
        name='Flags', default='flags'
    ),
    'action_power': bpy.props.StringProperty(
        name='Power', default='power'
    )
}


class XRayPrefsCustomProperties(bpy.types.PropertyGroup):
    if not version_utils.IS_28:
        for prop_name, prop_value in xray_custom_properties.items():
            exec('{0} = xray_custom_properties.get("{0}")'.format(prop_name))


key_items = (
    ('F5', 'F5', ''),
    ('F6', 'F6', ''),
    ('F7', 'F7', ''),
    ('F8', 'F8', ''),
    ('F9', 'F9', ''),
)

defaults_category_items = (
    ('OBJECT', 'Object', ''),
    ('ANM', 'Anm', ''),
    ('SKLS', 'Skls', ''),
    ('BONES', 'Bones', ''),
    ('DETAILS', 'Details', ''),
    ('DM', 'Dm', ''),
    ('OMF', 'Omf', ''),
    ('SCENE', 'Scene', '')
)

category_items = (
    ('PATHS', 'Paths', ''),
    ('DEFAULTS', 'Defaults', ''),
    ('PLUGINS', 'Plugins', ''),
    ('KEYMAP', 'Keymap', ''),
    ('CUSTOM_PROPS', 'Custom Props', ''),
    ('OTHERS', 'Others', '')
)

plugin_preferences_props = {
    # path props
    'fs_ltx_file': bpy.props.StringProperty(
        subtype='FILE_PATH', name='fs.ltx File', update=update_paths
    ),
    'gamedata_folder': bpy.props.StringProperty(subtype='DIR_PATH', update=update_paths),
    'textures_folder': bpy.props.StringProperty(subtype='DIR_PATH', update=update_paths),
    'gamemtl_file': bpy.props.StringProperty(subtype='FILE_PATH', update=update_paths),
    'eshader_file': bpy.props.StringProperty(subtype='FILE_PATH', update=update_paths),
    'cshader_file': bpy.props.StringProperty(subtype='FILE_PATH', update=update_paths),
    'objects_folder': bpy.props.StringProperty(subtype='DIR_PATH', update=update_paths),
    # path auto props
    'gamedata_folder_auto': bpy.props.StringProperty(),
    'textures_folder_auto': bpy.props.StringProperty(),
    'gamemtl_file_auto': bpy.props.StringProperty(),
    'eshader_file_auto': bpy.props.StringProperty(),
    'cshader_file_auto': bpy.props.StringProperty(),
    'objects_folder_auto': bpy.props.StringProperty(),

    'expert_mode': bpy.props.BoolProperty(
        name='Expert Mode', description='Show additional properties/controls'
    ),
    'compact_menus': bpy.props.BoolProperty(
        name='Compact Import/Export Menus', update=update_menu_func
    ),

    # defaults
    'defaults_category': bpy.props.EnumProperty(
        default='OBJECT', items=defaults_category_items
    ),

    # object import props
    'sdk_version': general_obj_props.PropSDKVersion(),
    'object_motions_import': obj_imp_props.PropObjectMotionsImport(),
    'use_motion_prefix_name': obj_imp_props.PropObjectUseMotionPrefixName(),
    'object_mesh_split_by_mat': obj_imp_props.PropObjectMeshSplitByMaterials(),
    'object_bones_custom_shapes': obj_imp_props.PropObjectBonesCustomShapes(),
    # object export props
    'export_object_sdk_version': general_obj_props.PropSDKVersion(),
    'smoothing_out_of': obj_exp_props.prop_smoothing_out_of(),
    'object_motions_export': obj_exp_props.PropObjectMotionsExport(),
    'object_texture_names_from_path': obj_exp_props.PropObjectTextureNamesFromPath(),
    'export_object_use_export_paths': obj_exp_props.PropUseExportPaths(),
    # anm import props
    'anm_create_camera': anm_props.PropAnmCameraAnimation(),
    # skl/skls import props
    'skls_use_motion_prefix_name': obj_imp_props.PropObjectUseMotionPrefixName(),
    'add_actions_to_motion_list': skl_props.prop_skl_add_actions_to_motion_list(),
    # bones import props
    'bones_import_bone_parts': omf_props.prop_import_bone_parts(),
    'bones_import_bone_properties': bones_props.prop_import_bone_properties(),
    # bones export props
    'bones_export_bone_parts': omf_props.prop_export_bone_parts(),
    'bones_export_bone_properties': bones_props.prop_export_bone_properties(),
    # details import props
    'details_models_in_a_row': details_props.prop_details_models_in_a_row(),
    'load_slots': details_props.prop_details_load_slots(),
    'details_format': details_props.prop_details_format(),
    # details export props
    'details_texture_names_from_path': obj_exp_props.PropObjectTextureNamesFromPath(),
    'format_version': details_props.prop_details_format_version(),
    # dm export props
    'dm_texture_names_from_path': obj_exp_props.PropObjectTextureNamesFromPath(),
    # omf import props
    'omf_import_motions': obj_imp_props.PropObjectMotionsImport(),
    'import_bone_parts': omf_props.prop_import_bone_parts(),
    'omf_add_actions_to_motion_list': skl_props.prop_skl_add_actions_to_motion_list(),
    # omf export props
    'omf_export_bone_parts': omf_props.prop_export_bone_parts(),
    'omf_export_mode': omf_props.prop_omf_export_mode(),
    'omf_motions_export': obj_exp_props.PropObjectMotionsExport(),
    # scene selection import props
    'scene_selection_sdk_version': general_obj_props.PropSDKVersion(),
    'scene_selection_mesh_split_by_mat': obj_imp_props.PropObjectMeshSplitByMaterials(),
    'scene_selection_shaped_bones': obj_imp_props.PropObjectBonesCustomShapes(),

    # keymap
    'import_object_key': bpy.props.EnumProperty(
        default='F8', update=update_keymap, items=key_items,
        name='Import Object Key'
    ),
    'import_object_shift': bpy.props.BoolProperty(
        default=False, update=update_keymap
    ),
    'export_object_key': bpy.props.EnumProperty(
        default='F8', update=update_keymap, items=key_items,
        name='Export Object Key'
    ),
    'export_object_shift': bpy.props.BoolProperty(
        default=True, update=update_keymap
    ),
    # enable import plugins
    'enable_object_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_anm_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_dm_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_details_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_skls_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_bones_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_err_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_level_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_game_level_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_omf_import': bpy.props.BoolProperty(default=True, update=update_menu_func),
    # enable export plugins
    'enable_object_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_anm_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_dm_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_details_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_skls_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_bones_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_level_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_game_level_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_omf_export': bpy.props.BoolProperty(default=True, update=update_menu_func),
    'enable_ogf_export': bpy.props.BoolProperty(default=True, update=update_menu_func),

    'category': bpy.props.EnumProperty(default='PATHS', items=category_items),
    'custom_props': bpy.props.PointerProperty(type=XRayPrefsCustomProperties)
}


def register():
    version_utils.assign_props([
        (xray_custom_properties, XRayPrefsCustomProperties),
    ])
    bpy.utils.register_class(XRayPrefsCustomProperties)


def unregister():
    bpy.utils.unregister_class(XRayPrefsCustomProperties)