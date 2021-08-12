# standart modules
import os

# blender modules
import bpy
import bpy_extras

# addon modules
from . import imp
from . import exp
from . import props
from .. import icons
from .. import utils
from .. import version_utils


filename_ext = '.anm'

op_import_anm_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(subtype='DIR_PATH'),
    'files': bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement),
    'camera_animation': props.PropAnmCameraAnimation()
}


class XRAY_OT_import_anm(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = 'xray_import.anm'
    bl_label = 'Import .anm'
    bl_description = 'Imports X-Ray animation'
    bl_options = {'UNDO', 'PRESET'}

    if not version_utils.IS_28:
        for prop_name, prop_value in op_import_anm_props.items():
            exec('{0} = op_import_anm_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, _context):
        if not self.files[0].name:
            self.report({'ERROR'}, 'No files selected!')
            return {'CANCELLED'}
        import_context = imp.ImportAnmContext()
        import_context.camera_animation = self.camera_animation
        for file in self.files:
            ext = os.path.splitext(file.name)[-1].lower()
            file_path = os.path.join(self.directory, file.name)
            if ext == '.anm':
                if not os.path.exists(file_path):
                    self.report(
                        {'ERROR'},
                        'File not found: "{}"'.format(file_path)
                    )
                    return {'CANCELLED'}
                try:
                    imp.import_file(file_path, import_context)
                except utils.AppError as err:
                    self.report({'ERROR'}, str(err))
            else:
                self.report(
                    {'ERROR'},
                    'Not recognised format of file: "{}"'.format(file_path)
                )
                return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        preferences = version_utils.get_preferences()
        self.camera_animation = preferences.anm_create_camera
        return super().invoke(context, event)


op_export_anm_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext,
        options={'HIDDEN'}),
}


class XRAY_OT_export_anm(bpy.types.Operator, utils.FilenameExtHelper):
    bl_idname = 'xray_export.anm'
    bl_label = 'Export .anm'
    bl_description = 'Exports X-Ray animation'

    filename_ext = filename_ext

    if not version_utils.IS_28:
        for prop_name, prop_value in op_export_anm_props.items():
            exec('{0} = op_export_anm_props.get("{0}")'.format(prop_name))

    @utils.execute_with_logger
    @utils.set_cursor_state
    def export(self, context):
        obj = context.active_object
        if not obj.animation_data:
            self.report(
                {'ERROR'},
                'Object "{}" has no animation data.'.format(obj.name)
            )
            return {'CANCELLED'}
        exp.export_file(obj, self.filepath)


def menu_func_import(self, _context):
    icon = icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_import_anm.bl_idname,
        text='X-Ray Animation (.anm)',
        icon_value=icon
    )


def menu_func_export(self, _context):
    icon = icons.get_stalker_icon()
    self.layout.operator(
        XRAY_OT_export_anm.bl_idname,
        text='X-Ray Animation (.anm)',
        icon_value=icon
    )


classes = (
    (XRAY_OT_import_anm, op_import_anm_props),
    (XRAY_OT_export_anm, op_export_anm_props)
)


def register():
    for operator, properties in classes:
        version_utils.assign_props([(properties, operator), ])
        bpy.utils.register_class(operator)


def unregister():
    for operator, properties in reversed(classes):
        bpy.utils.unregister_class(operator)
