# blender modules
import bpy

# addon modules
from .. import ui
from .. import version_utils
from .. import skl
from .. import ops


class XRAY_PT_ActionPanel(ui.base.XRayPanel):
    bl_category = 'F-Curve'
    bl_space_type = 'DOPESHEET_EDITOR' if bpy.app.version >= (2, 78, 0) else 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_context = 'object'
    bl_label = ui.base.build_label('Action')

    @classmethod
    def poll(cls, context):
        preferences = version_utils.get_preferences()
        panel_used = (
            # import plugins
            preferences.enable_object_import or
            preferences.enable_anm_import or
            preferences.enable_skls_import or
            preferences.enable_omf_import or
            # export plugins
            preferences.enable_object_export or
            preferences.enable_anm_export or
            preferences.enable_skls_export or
            preferences.enable_omf_export
        )
        return (
            context.active_object and
            context.active_object.animation_data and
            context.active_object.animation_data.action and
            panel_used
        )

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        action = obj.animation_data.action
        data = action.xray

        # bake properties
        col = layout.column(align=True)
        col.label(text='Bake Mode:')
        row = col.row(align=True)
        row.prop(data, 'autobake', expand=True)
        col = col.column(align=True)
        col.active = data.autobake != 'off'
        col.prop(data, 'autobake_custom_refine', toggle=True)
        col = col.column(align=True)
        col.active = data.autobake_custom_refine
        col.prop(data, 'autobake_refine_location', text='Location Threshold')
        col.prop(data, 'autobake_refine_rotation', text='Rotation Threshold')

        layout.prop(data, 'fps', text='FPS')
        if obj.type != 'ARMATURE':
            return
        layout.prop(data, 'speed', text='Speed')
        layout.prop(data, 'accrue', text='Accrue')
        layout.prop(data, 'falloff', text='Falloff')
        layout.prop(data, 'flags_fx', text='Type FX', toggle=True)
        if data.flags_fx:
            row = layout.row(align=True)
            row.label(text='Start Bone:')
            row.prop_search(data, 'bonestart_name', obj.pose, 'bones', text='')
            layout.prop(data, 'power', text='Power')
        else:
            row = layout.row(align=True)
            row.label(text='Bone Part:')
            row.prop_search(data, 'bonepart_name', obj.pose, 'bone_groups', text='')
            row = layout.row(align=True)
            row.prop(data, 'flags_stopatend', text='Stop', toggle=True)
            row.prop(data, 'flags_nomix', text='No Mix', toggle=True)
            row.prop(data, 'flags_syncpart', text='Sync', toggle=True)
            row = layout.row(align=True)
            row.prop(data, 'flags_footsteps', text='Foot Steps', toggle=True)
            row.prop(data, 'flags_movexform', text='Move XForm', toggle=True)
            row = layout.row(align=True)
            row.prop(data, 'flags_idle', text='Idle', toggle=True)
            row.prop(data, 'flags_weaponbone', text='Weapon Bone', toggle=True)
        layout.context_pointer_set(skl.ops.XRAY_OT_export_skl.bl_idname + '.action', action)
        layout.operator(skl.ops.XRAY_OT_export_skl.bl_idname, icon='EXPORT')
        layout.label(text='Settings:')
        row = layout.row(align=True)
        row.operator(ops.action_utils.XRAY_OT_CopyActionSettings.bl_idname)
        row.operator(ops.action_utils.XRAY_OT_PasteActionSettings.bl_idname)


def register():
    bpy.utils.register_class(XRAY_PT_ActionPanel)


def unregister():
    bpy.utils.unregister_class(XRAY_PT_ActionPanel)