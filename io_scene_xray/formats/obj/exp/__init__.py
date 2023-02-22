# addon modules
from . import ops
from . import main
from .. import fmt
from .... import rw
from .... import utils
from .... import log


def _export(bpy_obj, chunked_writer, context):
    writer = rw.write.ChunkedWriter()
    main.export_main(bpy_obj, writer, context)
    chunked_writer.put(fmt.Chunks.Object.MAIN, writer)


@log.with_context('export-object')
def export_file(bpy_obj, file_path, context):
    log.update(object=bpy_obj.name)
    writer = rw.write.ChunkedWriter()
    _export(bpy_obj, writer, context)
    rw.utils.save_file(file_path, writer)
