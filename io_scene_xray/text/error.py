# general
mat_no_img = 'material has no image'
mat_many_img = 'material has more the one image'
mat_many_tex = 'material has more than one texture'
obj_many_uv = 'object has more than one UV-map'
mat_not_use_nodes = 'material does not use nodes'
obj_empty_mat = 'object use empty material slot'
obj_no_mat = 'object has no material'
img_bad_image_path = 'image is not in the textures folder'
file_another_prog = 'unable to write file. The file is open in another program'
# anm export
anm_no_keys = 'action has keys not for all channels'
# anm import
anm_unsupport_ver = 'file has unsupported format version'
# details convert
details_light_1569 = 'object has incorrect light format: "Builds 1096-1558". Must be "Builds 1569-CoP"'
details_light_1096 = 'object has incorrect light format: "Builds 1569-CoP". Must be "Builds 1096-1558"'
details_slots_size = '"Slots Base Object" size not equal "Slots Top Object" size'
details_poly_count = 'slots object has an incorrect number of polygons'
details_img_size = 'image has incorrect size'
# details import
details_bad_header = 'bad details file. HEADER chunk size not equal 24'
details_unsupport_ver = 'unsupported details format version'
details_no_header = 'bad details file. Cannot find HEADER chunk'
details_no_meshes = 'bad details file. Cannot find MESHES chunk'
details_no_slots = 'bad details file. Cannot find SLOTS chunk'
# details utility
details_has_no_prop = 'object "{0}" has no "{1}"'
details_has_no_image = 'cannot find "{0}" image: "{1}"'
details_cannot_find = 'cannot find "{0}": "{1}"'
details_must_be_type = '"{0}" must be of type "{1}"'
# details write
details_no_children = 'Meshes Object "{}" has no children'
details_many_children = 'Meshes Object "{0}" has too many children: {1}. Not more than {2}.'
details_not_mesh = 'Meshes Object "{0}" has incorrect child object type: {1}. Child object type must be "MESH"'
details_bad_detail_index = 'Meshes Object "{0}" has incorrect "Detail Index": {1}. Must be less than {2}'
details_no_model_index = 'not detail model with index {0}'
details_duplicate_model = 'duplicated index {0} in detail models'
# dm create
dm_bad_indices = 'bad dm triangle indices'
# dm export
dm_many_verts = 'mesh "{0}" has too many vertices: {1}. Must be no more than {2}'
# dm validate
dm_no_uv = 'mesh "{}" has no UV-map'
dm_many_uv = 'mesh "{}" has more than one UV-map'
dm_many_mat = 'mesh "{}" has more than one material'
dm_no_tex = 'material "{}" has no texture'
dm_tex_type = 'texture "{0}" has an incorrect type: {1}'
# level cform import
cform_unsupport_ver = 'Unsupported cform version: {}'
# level export
level_no_lmap = 'Cannot find light map image "{0}" in "{1}" material!'
level_many_children = 'Object "{}" has more than one children'
# level import
level_unsupport_ver = 'Unsupported level version: {}'
# object export main
object_ungroupped_verts = 'Mesh "{0}" has {1} vertices that are not tied to any exportable bones'
object_duplicate_bones = 'The object has duplicate bones'
object_many_arms = 'Root object "{}" has more than one armature'
object_no_meshes = 'Root object "{}" has no meshes'
object_skel_many_meshes = 'Skeletal object "{}" has more than one mesh'
object_bad_boneparts = 'Invalid bone parts: not all bones are tied to the Bone Part'
object_many_parents = 'Invalid armature object "{}". Has more than one parent: {}'
object_bad_scale = 'Armature object "{}" has incorrect scale. The scale must be (1.0, 1.0, 1.0).'
# object export mesh
object_no_uv = 'UV-map is required, but not found on the "{0}" object'
# object import bone
object_unsupport_bone_ver = 'unsupported BONE format version'
# object import main
object_unsupport_format_ver = 'unsupported OBJECT format version'
object_main_chunk = 'file does not have main chunk'
# object import mesh
object_unsupport_mesh_ver = 'unsupported MESH format version'
object_bad_vmap = 'unknown vmap type'
object_many_duplicated_faces = 'too many duplicated polygons'
# ogf export
ogf_no_bone = 'bone "{0}" not found in armature "{1}" (for object "{2}")'
# ogf import
ogf_bad_ver = 'Unsupported ogf format version: {}'
ogf_bad_vertex_fmt = 'Unsupported ogf vertex format: 0x{:x}'
ogf_bad_color_mode = 'Unknown ogf color mode: {}'
ogf_bad_model_type = 'Unsupported ogf model type: 0x{:x}'
# omf export
omf_empty = 'This OMF file is empty. Use a different export mode.'
omf_no_anims = 'The OMF file does not have an animation block.'
omf_no_params = 'The OMF file does not have an parameters block.'
omf_bone_no_group = 'Bone "{}" of "{}" armature does not have a bone group'
omf_empty_bone_group = 'Armature "{}" has an empty bone group'
# omf import
omf_no_bone = 'Cannot find bone: {}'
omf_nothing = 'Nothing was imported. Change the import settings.'
# scene import
scene_bad_file = 'Bad scene selection file. Cannot find "scene version" chunk.'
scene_obj_tool_ver = 'Unsupported object tools version: {}.'
scene_obj_count = 'Bad scene selection file. Cannot find "scene objects count" chunk.'
scene_scn_objs = 'Bad scene selection file. Cannot find "scene objects" chunk.'
scene_objs = 'Bad scene selection file. Cannot find "objects" chunk.'
scene_no_ver = 'Bad scene selection file. Cannot find "version" chunk.'
scene_ver_size = 'Bad scene selection file. "version" chunk size is not equal to 4.'
scene_ver = 'Unsupported format version: {}.'
# motion
motion_shape = 'Unsupported keyframe shape: {}'
motion_ver = 'unsupported motions version'
