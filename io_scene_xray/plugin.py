import os.path
import re

import bpy
import bpy.utils.previews
from bpy_extras import io_utils

from . import xray_io, ops, ui
from .ui import base
from .utils import (
    AppError, ObjectsInitializer, logger,
    execute_require_filepath, FilenameExtHelper
)
from . import plugin_prefs, prefs, edit_helpers, hotkeys, props
from . import details
from .details import ops as det_ops
from .dm import ops as dm_ops
from .err import ops as err_ops
from .scene import ops as scene_ops
from .obj.exp import ops as object_exp_ops
from .obj.imp import ops as object_imp_ops
from .anm import ops as anm_ops
from .skl import ops as skl_ops
from .bones import ops as bones_ops
from .ogf import ops as ogf_ops
from .level import ops as level_ops
from .omf import ops as omf_ops
from . import skls_browser
from .version_utils import (
    get_import_export_menus, get_scene_update_post, assign_props, IS_28
)


xray_io.ENCODE_ERROR = AppError


class XRayImportMenu(bpy.types.Menu):
    bl_idname = 'INFO_MT_xray_import'
    bl_label = base.build_label()

    def draw(self, context):
        layout = self.layout
        enabled_import_operators = get_enabled_operators(
            import_draw_functions, import_draw_functions_28
        )
        for id_name, text in enabled_import_operators:
            layout.operator(id_name, text=text)


def get_enabled_operators(draw_functions, draw_functions_28):
    preferences = prefs.utils.get_preferences()
    funct_list = []
    funct_list.extend(draw_functions)

    if IS_28:
        funct_list.extend(draw_functions_28)

    operators = []
    for _, enable_prop, id_name, text in funct_list:
        enable = getattr(preferences, enable_prop)
        if enable:
            operators.append((id_name, text))
    return operators


class XRayExportMenu(bpy.types.Menu):
    bl_idname = 'INFO_MT_xray_export'
    bl_label = base.build_label()

    def draw(self, context):
        layout = self.layout
        enabled_export_operators = get_enabled_operators(
            export_draw_functions, export_draw_functions_28
        )
        for id_name, text in enabled_export_operators:
            layout.operator(id_name, text=text)


def overlay_view_3d():
    def try_draw(base_obj, obj):
        if not hasattr(obj, 'xray'):
            return
        xray = obj.xray
        if hasattr(xray, 'ondraw_postview'):
            xray.ondraw_postview(base_obj, obj)
        if hasattr(obj, 'type'):
            if obj.type == 'ARMATURE':
                for bone in obj.data.bones:
                    try_draw(base_obj, bone)

    for obj in bpy.data.objects:
        try_draw(obj, obj)


_INITIALIZER = ObjectsInitializer([
    'objects',
    'materials',
])

@bpy.app.handlers.persistent
def load_post(_):
    _INITIALIZER.sync('LOADED', bpy.data)

@bpy.app.handlers.persistent
def scene_update_post(_):
    _INITIALIZER.sync('CREATED', bpy.data)


def menu_func_xray_import(self, _context):
    icon = get_stalker_icon()
    self.layout.menu(XRayImportMenu.bl_idname, icon_value=icon)


def menu_func_xray_export(self, _context):
    icon = get_stalker_icon()
    self.layout.menu(XRayExportMenu.bl_idname, icon_value=icon)


# import draw functions
import_draw_functions = [
    (
        object_imp_ops.menu_func_import,
        'enable_object_import',
        object_imp_ops.OpImportObject.bl_idname,
        'Source Object (.object)'
    ),
    (
        anm_ops.menu_func_import,
        'enable_anm_import',
        anm_ops.OpImportAnm.bl_idname,
        'Animation (.anm)'
    ),
    (
        skl_ops.menu_func_import,
        'enable_skls_import',
        skl_ops.OpImportSkl.bl_idname,
        'Skeletal Animation (.skls)'
    ),
    (
        bones_ops.menu_func_import,
        'enable_bones_import',
        bones_ops.IMPORT_OT_xray_bones.bl_idname,
        'Bones Data (.bones)'
    ),
    (
        err_ops.menu_func_import,
        'enable_err_import',
        err_ops.OpImportERR.bl_idname,
        'Error List (.err)'
    ),
    (
        det_ops.menu_func_import,
        'enable_details_import',
        det_ops.OpImportDetails.bl_idname,
        'Level Details (.details)'
    ),
    (
        dm_ops.menu_func_import,
        'enable_dm_import',
        dm_ops.OpImportDM.bl_idname,
        'Detail Model (.dm)'
    ),
    (
        scene_ops.menu_func_import,
        'enable_level_import',
        scene_ops.OpImportLevelScene.bl_idname,
        'Scene Selection (.level)'
    ),
    (
        omf_ops.menu_func_import,
        'enable_omf_import',
        omf_ops.IMPORT_OT_xray_omf.bl_idname,
        'Game Motion (.omf)'
    )
]
import_draw_functions_28 = [
    (
        level_ops.menu_func_import,
        'enable_game_level_import',
        level_ops.IMPORT_OT_xray_level.bl_idname,
        'Game Level (level)'
    ),
]
# export draw functions
export_draw_functions = [
    (
        object_exp_ops.menu_func_export,
        'enable_object_export',
        object_exp_ops.OpExportObjects.bl_idname,
        'Source Object (.object)'
    ),
    (
        anm_ops.menu_func_export,
        'enable_anm_export',
        anm_ops.OpExportAnm.bl_idname,
        'Animation (.anm)'
    ),
    (
        skl_ops.menu_func_export,
        'enable_skls_export',
        skl_ops.OpExportSkls.bl_idname,
        'Skeletal Animation (.skls)'
    ),
    (
        bones_ops.menu_func_export,
        'enable_bones_export',
        bones_ops.EXPORT_OT_xray_bones_batch.bl_idname,
        'Bones Data (.bones)'
    ),
    (
        ogf_ops.menu_func_export,
        'enable_ogf_export',
        ogf_ops.OpExportOgf.bl_idname,
        'Game Object (.ogf)'
    ),
    (
        det_ops.menu_func_export,
        'enable_details_export',
        det_ops.OpExportDetails.bl_idname,
        'Level Details (.details)'
    ),
    (
        dm_ops.menu_func_export,
        'enable_dm_export',
        dm_ops.OpExportDMs.bl_idname,
        'Detail Model (.dm)'
    ),
    (
        scene_ops.menu_func_export,
        'enable_level_export',
        scene_ops.OpExportLevelScene.bl_idname,
        'Scene Selection (.level)'
    ),
    (
        omf_ops.menu_func_export,
        'enable_omf_export',
        omf_ops.EXPORT_OT_xray_omf.bl_idname,
        'Game Motion (.omf)'
    )
]
export_draw_functions_28 = [
    (
        level_ops.menu_func_export,
        'enable_game_level_export',
        level_ops.EXPORT_OT_xray_level.bl_idname,
        'Game Level (level)'
    ),
]


def remove_draw_functions(funct_list, menu):
    for draw_function, _, _, _ in funct_list:
        menu.remove(draw_function)


def append_draw_functions(funct_list, menu):
    preferences = prefs.utils.get_preferences()
    for draw_function, enable_prop, _, _ in funct_list:
        enable = getattr(preferences, enable_prop)
        if enable:
            menu.append(draw_function)


def append_menu_func():
    preferences = prefs.utils.get_preferences()
    import_menu, export_menu = get_import_export_menus()
    funct_imp_list = []
    funct_imp_list.extend(import_draw_functions)
    funct_exp_list = []
    funct_exp_list.extend(export_draw_functions)

    if IS_28:
        funct_imp_list.extend(import_draw_functions_28)
        funct_exp_list.extend(export_draw_functions_28)

    # remove import menus
    remove_draw_functions(funct_imp_list, import_menu)
    # remove export menus
    remove_draw_functions(funct_exp_list, export_menu)
    # remove compact menus
    import_menu.remove(menu_func_xray_import)
    export_menu.remove(menu_func_xray_export)

    if preferences.compact_menus:
        # create compact menus
        # import
        enabled_import_operators = get_enabled_operators(
            import_draw_functions, import_draw_functions_28
        )
        if enabled_import_operators:
            import_menu.prepend(menu_func_xray_import)
        # export
        enabled_export_operators = get_enabled_operators(
            export_draw_functions, export_draw_functions_28
        )
        if enabled_export_operators:
            export_menu.prepend(menu_func_xray_export)
    else:
        # create standart import menus
        append_draw_functions(funct_imp_list, import_menu)
        # create standart export menus
        append_draw_functions(funct_exp_list, export_menu)


preview_collections = {}
STALKER_ICON_NAME = 'stalker'


def get_stalker_icon():
    pcoll = preview_collections['main']
    icon = pcoll[STALKER_ICON_NAME]
    # without this line in some cases the icon is not visible
    len(icon.icon_pixels)
    return icon.icon_id


classes = (
    XRayImportMenu,
    XRayExportMenu
)


def register():
    details.register()
    skls_browser.register()
    props.register()

    for clas in classes:
        bpy.utils.register_class(clas)
    plugin_prefs.register()

    # load icon
    pcoll = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
    pcoll.load(STALKER_ICON_NAME, os.path.join(icons_dir, 'stalker.png'), 'IMAGE')
    preview_collections['main'] = pcoll

    object_imp_ops.register()
    object_exp_ops.register()
    anm_ops.register()
    dm_ops.register()
    bones_ops.register()
    ogf_ops.register()
    skl_ops.register()
    omf_ops.register()
    scene_ops.register()
    if IS_28:
        level_ops.register()
    err_ops.register()
    append_menu_func()
    overlay_view_3d.__handle = bpy.types.SpaceView3D.draw_handler_add(
        overlay_view_3d, (),
        'WINDOW', 'POST_VIEW'
    )
    bpy.app.handlers.load_post.append(load_post)
    get_scene_update_post().append(scene_update_post)
    hotkeys.register_hotkeys()
    edit_helpers.register()
    ops.register()
    ui.register()


def unregister():
    ui.unregister()
    ops.unregister()
    edit_helpers.unregister()
    hotkeys.unregister_hotkeys()
    err_ops.unregister()
    dm_ops.unregister()
    bones_ops.unregister()
    ogf_ops.unregister()
    if IS_28:
        level_ops.unregister()
    scene_ops.unregister()
    omf_ops.unregister()
    skl_ops.unregister()
    anm_ops.unregister()
    object_exp_ops.unregister()
    object_imp_ops.unregister()

    get_scene_update_post().remove(scene_update_post)
    bpy.app.handlers.load_post.remove(load_post)
    bpy.types.SpaceView3D.draw_handler_remove(overlay_view_3d.__handle, 'WINDOW')

    funct_imp_list = []
    funct_imp_list.extend(import_draw_functions)
    funct_exp_list = []
    funct_exp_list.extend(export_draw_functions)

    if IS_28:
        funct_imp_list.extend(import_draw_functions_28)
        funct_exp_list.extend(export_draw_functions_28)

    import_menu, export_menu = get_import_export_menus()

    # remove import menus
    remove_draw_functions(funct_imp_list, import_menu)
    # remove export menus
    remove_draw_functions(funct_exp_list, export_menu)
    # remove compact menus
    import_menu.remove(menu_func_xray_import)
    export_menu.remove(menu_func_xray_export)

    # remove icon
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

    plugin_prefs.unregister()
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)

    props.unregister()
    skls_browser.unregister()
    details.unregister()
