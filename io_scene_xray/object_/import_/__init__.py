
import io
import os.path

import bpy

from ... import xray_io
from ... import utils
from ... import log
from .. import format_
from . import main


class ImportContext:
    def __init__(
            self,
            textures,
            soc_sgroups,
            import_motions,
            split_by_materials,
            operator,
            objects=''
        ):

        self.version = utils.plugin_version_number()
        self.textures_folder = textures
        self.objects_folder = objects
        self.soc_sgroups = soc_sgroups
        self.import_motions = import_motions
        self.split_by_materials = split_by_materials
        self.operator = operator
        self.loaded_materials = None

    def before_import_file(self):
        self.loaded_materials = {}

    def image(self, relpath):
        relpath = relpath.lower().replace('\\', os.path.sep)
        if not self.textures_folder:
            result = bpy.data.images.new(os.path.basename(relpath), 0, 0)
            result.source = 'FILE'
            result.filepath = relpath + '.dds'
            return result

        filepath = os.path.abspath(
            os.path.join(self.textures_folder, relpath + '.dds')
        )
        result = None
        for i in bpy.data.images:
            if bpy.path.abspath(i.filepath) == filepath:
                result = i
                break
        if result is None:
            try:
                result = bpy.data.images.load(filepath)
            except RuntimeError as ex:  # e.g. 'Error: Cannot read ...'
                log.warn(ex)
                result = bpy.data.images.new(os.path.basename(relpath), 0, 0)
                result.source = 'FILE'
                result.filepath = filepath
        return result


def _import(fpath, context, reader):
    for (cid, data) in reader:
        if cid == format_.Chunks.Object.MAIN:
            main.import_main(fpath, context, xray_io.ChunkedReader(data))
        else:
            log.debug('unknown chunk', cid=cid)


@log.with_context(name='file')
def import_file(fpath, context):
    log.update(path=fpath)
    with io.open(fpath, 'rb') as file:
        _import(fpath, context, xray_io.ChunkedReader(memoryview(file.read())))
