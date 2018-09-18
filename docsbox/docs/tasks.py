import os
import shutil
import datetime

from pylokit import Office
from wand.image import Image
from tempfile import NamedTemporaryFile, TemporaryDirectory

from rq import get_current_job

from docsbox import app, rq
from docsbox.docs.utils import make_zip_archive, make_thumbnails


@rq.job(timeout=app.config["REDIS_JOB_TIMEOUT"])
def remove_file(path):
    """
    Just removes a file.
    Used for deleting original files (uploaded by user) and result files (result of converting)
    """
    return os.remove(path)


def create_temp_file(original_file):
    with NamedTemporaryFile(delete=False, prefix=app.config["MEDIA_PATH"]) as tmp_file:
        original_file.save(tmp_file)
        tmp_file.flush()
        tmp_file.close()
        remove_file.schedule(
            datetime.timedelta(seconds=app.config["ORIGINAL_FILE_TTL"]), tmp_file.name)
        return tmp_file


@rq.job(timeout=app.config["REDIS_JOB_TIMEOUT"])
def upload_document(path, original_fmt):
    current_task = get_current_job()
    with Office(app.config["LIBREOFFICE_PATH"]) as office:  # acquire libreoffice lock
        with office.documentLoad(path) as original_document:  # open original document
            file_name = "{0}.{1}".format(current_task.id, original_fmt)
            output_path = os.path.join(app.config["MEDIA_PATH"], file_name)
            original_document.saveAs(output_path, fmt=original_fmt)
        remove_file.schedule(
            datetime.timedelta(seconds=app.config["RESULT_FILE_TTL"]),
            output_path
        )
    return file_name


@rq.job(timeout=app.config["REDIS_JOB_TIMEOUT"])
def process_document_convertion(path, options, meta):
    current_task = get_current_job()
    with Office(app.config["LIBREOFFICE_PATH"]) as office:  # acquire libreoffice lock
        with office.documentLoad(path) as original_document:  # open original document
            with TemporaryDirectory() as tmp_dir:  # create temp dir where output'll be stored
                for fmt in options["formats"]: # iterate over requested formats
                    output_path = os.path.join(tmp_dir, fmt)
                    original_document.saveAs(output_path, fmt=fmt)

                # generate thumbnails
                if app.config["GENERATE_THUMBNAILS"] and options.get("thumbnails", None):
                    is_created = False
                    if meta["mimetype"] == "application/pdf":
                        pdf_path = path
                    elif "pdf" in options["formats"]:
                        pdf_path = os.path.join(tmp_dir, "pdf")
                    else:
                        pdf_tmp_file = NamedTemporaryFile()
                        pdf_path = pdf_tmp_file.name
                        original_document.saveAs(pdf_tmp_file.name, fmt="pdf")
                        is_created = True
                        image = Image(filename=pdf_path,
                                    resolution=app.config["THUMBNAILS_DPI"])
                        if is_created:
                            pdf_tmp_file.close()
                            thumbnails = make_thumbnails(image, tmp_dir, options["thumbnails"]["size"])

                result_path, result = make_zip_archive(current_task.id, tmp_dir)
        remove_file.schedule(datetime.timedelta(
            seconds=app.config["RESULT_FILE_TTL"]), result_path)
    return result
