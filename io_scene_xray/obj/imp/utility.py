# standart modules
import os

# blender modules
import bpy

# addon modules
from ... import log
from ... import contexts


class ImportObjectMeshContext(contexts.ImportMeshContext):
    def __init__(self):
        contexts.ImportMeshContext.__init__(self)
        self.soc_sgroups = None
        self.split_by_materials = None
        self.objects_folder = None

    def before_import_file(self):
        self.loaded_materials = {}


class ImportObjectAnimationContext(contexts.ImportAnimationContext):
    def __init__(self):
        contexts.ImportAnimationContext.__init__(self)


class ImportObjectContext(
        ImportObjectMeshContext, ImportObjectAnimationContext
    ):
    def __init__(self):
        ImportObjectMeshContext.__init__(self)
        ImportObjectAnimationContext.__init__(self)
