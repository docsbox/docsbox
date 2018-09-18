import ujson
import datetime

from flask import request, send_from_directory
from flask_restful import Resource, abort

from docsbox import app, rq
from docsbox.docs.tasks import process_document_convertion, upload_document, create_temp_file
from docsbox.docs.utils import get_file_mimetype

class DocumentStateView(Resource):

    def get(self, task_id):
        """
        Returns information about task status.
        """
        queue = rq.get_queue()
        task = queue.fetch_job(task_id)
        if task:
            return {
                "id": task.id,
                "status": task.status
            }
        else:
            return abort(404, message="Unknown task_id")


class DocumentTypeView(Resource):

    def get(self):
        """
            Returns the File Type
        """
        if "file" not in request.files:
            return abort(400, message="file field is required")
        else:
            tmp_file = create_temp_file(request.files["file"])
            mimetype = get_file_mimetype(tmp_file)
        return {
                "mimetype": mimetype
            }


class DocumentConvertView(Resource):

    def post(self):
        """
            Validates options and creates converting task
        """
        if "file" not in request.files:
            return abort(400, message="file field is required")
        else:
            tmp_file = create_temp_file(request.files["file"])
            mimetype = get_file_mimetype(tmp_file)
            if mimetype in app.config["ACCEPTED_MIMETYPES"]:
                return {
                    "message": "File does not need to be converted."
                }
            else:
                if mimetype not in app.config["CONVERTABLE_MIMETYPES"]:
                    return abort(400, message="Not supported mimetype: '{0}'".format(mimetype))

                options = request.form.get("options", None)
                if options:  # options validation
                    options = ujson.loads(options)
                    formats = options.get("formats", None)
                    if not isinstance(formats, list) or not formats:
                        return abort(400, message="Invalid 'formats' value")
                    else:
                        for fmt in formats:
                            supported = (
                                fmt in app.config["CONVERTABLE_MIMETYPES"][mimetype]["formats"])
                            if not supported:
                                message = "'{0}' mimetype can't be converted to '{1}'"
                                return abort(400, message=message.format(mimetype, fmt))

                    thumbnails = options.get("thumbnails", None) # check for thumbnails options on request and if they are valid
                    if app.config["GENERATE_THUMBNAILS"] and thumbnails: # GENERATE_THUMBNAILS is configured as False
                        if not isinstance(thumbnails, dict):
                            return abort(400, message="Invalid 'thumbnails' value")
                        else:
                            thumbnails_size = thumbnails.get("size", None)
                            if not isinstance(thumbnails_size, str) or not thumbnails_size:
                                return abort(400, message="Invalid 'size' value")
                            else:
                                try:
                                    (width, height) = map(
                                        int, thumbnails_size.split("x"))
                                except ValueError:
                                    return abort(400, message="Invalid 'size' value")
                                else:
                                    options["thumbnails"]["size"] = (width, height)

                else:
                    options = app.config["DEFAULT_OPTIONS"]
            task = process_document_convertion.queue(tmp_file.name, options, {
                "mimetype": mimetype,
            })
        return {
            "id": task.id,
            "status": task.status,
        }


class DocumentUploadView(Resource):

    def post(self):
        """
            Recieves file, checks file mimetype and saves original document
        """
        if "file" not in request.files:
            return abort(400, message="file field is required")
        else:
            tmp_file = create_temp_file(request.files["file"])
            mimetype = get_file_mimetype(tmp_file)
            if mimetype not in app.config["ACCEPTED_MIMETYPES"]:
                if mimetype not in app.config["CONVERTABLE_MIMETYPES"]:
                    return abort(400, message="Not supported mimetype: '{0}'".format(mimetype))
                return {
                    "message": "File cannot be uploaded needs to be converted"
                }
                
            task = upload_document.queue(tmp_file.name, app.config["ACCEPTED_MIMETYPES"][mimetype]["format"])
        return {
            "id": task.id,
            "status": task.status
        }


class DocumentDownloadView(Resource):

    def get(self, task_id):
        """
            Returns the Converted File
        """
        queue = rq.get_queue()
        task = queue.fetch_job(task_id)
        if task:
            if task.status == "finished":
                return send_from_directory(app.config["MEDIA_PATH"], task.result, as_attachment=True)
            else:
                return abort(400, message="Task is still queued")
        else:
            return abort(404, message="Unknown task_id")
