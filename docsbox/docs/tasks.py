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


def create_temp_file(original_file_data):
    with NamedTemporaryFile(delete=False, prefix=app.config["MEDIA_PATH"]) as tmp_file:
        for chunk in original_file_data.iter_content(chunk_size=128):
            tmp_file.write(chunk)
        tmp_file.flush()
        tmp_file.close()
        job = remove_file.schedule(
            datetime.timedelta(seconds=app.config["ORIGINAL_FILE_TTL"]), tmp_file.name)
        return tmp_file, job


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
                    file_name = "{0}.{1}".format(current_task.id, fmt)
                    output_path = os.path.join(app.config["MEDIA_PATH"], file_name)
                    original_document.saveAs(output_path, fmt=fmt, options="-eSelectPdfVersion=1")
                    
                if app.config["GENERATE_THUMBNAILS"] and options.get("thumbnails", None): # generate thumbnails
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
                    image = Image(filename=pdf_path, resolution=app.config["THUMBNAILS_DPI"])
                    if is_created:
                        pdf_tmp_file.close()
                    thumbnails = make_thumbnails(image, tmp_dir, options["thumbnails"]["size"])
                    output_path, file_name = make_zip_archive(current_task.id, tmp_dir)                                  
        file_remove_task = remove_file.schedule(datetime.timedelta(
            seconds=app.config["RESULT_FILE_TTL"]), output_path)
        current_task.meta["tmp_file_remove_task"] = file_remove_task.id
        current_task.save_meta()
    return {"fileName": file_name, "fileType": options["content-type"] }

