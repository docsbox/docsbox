import ujson
import datetime
from requests import get, post

from flask import request, send_from_directory
from flask_restful import Resource, abort

from docsbox import app, rq
from docsbox.docs.tasks import process_document_convertion, upload_document, create_temp_file
from docsbox.docs.utils import get_file_mimetype 

def set_options(options, mimetype):
    """
    Validates options
    """
    if options:  # options validation
        options = ujson.loads(options)
        formats = options.get("formats", None)
        if not isinstance(formats, list) or not formats:
            return abort(400, message="Invalid 'formats' value")
        else:
            for fmt in formats:
                supported = (fmt in app.config["CONVERTABLE_MIMETYPES"][mimetype]["formats"])
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
    return options

class DocumentStatusView(Resource):

    def get(self, task_id):
        """
        Returns information about task status.
        """
        queue = rq.get_queue()
        task = queue.fetch_job(task_id)
        if task:
            if task.result:
                return {
                    "taskId": task.id,
                    "status": task.status,
                    "fileType": task.result["fileType"]
                }
            else: 
                return {
                    "taskId": task.id,
                    "status": task.status
                }
        else:
            return abort(404, message="Unknown task_id")


class DocumentTypeView(Resource):

    def get(self, file_id):
        """
        Requests from VIA fileservice the file with given id.
        Returns the File Mimetype
        """

        r = get("{0}/{1}".format(app.config["VIA_URL"], file_id), cert=app.config["VIA_CERT_PATH"], stream=True)

        if r.status_code == 200:
            tmp_file = create_temp_file(r)
            mimetype = get_file_mimetype(tmp_file)
            isConvertable = mimetype not in app.config["ACCEPTED_MIMETYPES"] and mimetype in app.config["CONVERTABLE_MIMETYPES"]
            return { "convertable": isConvertable, "fileType": mimetype }
        else: 
            return abort(r.status_code, message=r.json()["message"])


class DocumentConvertView(Resource):

    def post(self, file_id):
        """
            Requests from VIA fileservice the file with given id.
            Checks file mimetype and creates converting task.
        """

        r = get("{0}/{1}".format(app.config["VIA_URL"], file_id), cert=app.config["VIA_CERT_PATH"], stream=True)

        if r.status_code == 200:
            tmp_file, del_orig_job = create_temp_file(r)
            mimetype = get_file_mimetype(tmp_file)
            if mimetype in app.config["ACCEPTED_MIMETYPES"]:
                return abort(400, message="File does not need to be converted.")
            if mimetype not in app.config["CONVERTABLE_MIMETYPES"]:
                return abort(415, message="Not supported mimetype: '{0}'".format(mimetype))

            options = set_options(request.form.get("options", None), mimetype)
                
            task = process_document_convertion.queue(tmp_file.name, options, {"mimetype": mimetype})
            return { "taskId": task.id, "status": task.status}
        else: 
            return abort(r.status_code, message=r.json()["message"])


class DocumentDownloadView(Resource):

    def get(self, task_id):
        """
            If task with given id is finished saves the new converted file to Via fileservice
            and returns the respective file id
        """
        queue = rq.get_queue()
        task = queue.fetch_job(task_id)
        if task:
            if task.status == "finished":
                data = open(app.config["MEDIA_PATH"]+ "/"+ task.result["fileName"], "rb")
                headers = {'VIA_ALLOWED_USERS': app.config["VIA_ALLOWED_USERS"], 'Content-type': task.result["fileType"]}
                r = post(app.config["VIA_URL"], data=data, headers=headers)

                if r.status_code == 201:
                    return { 
                        "taskId": task.id,
                        "status": task.status,
                        "convertable": True,
                        "fileId": r.headers.get("Document-id"),
                        "fileType": task.result["fileType"]
                    }
                else:
                    return abort(r.status_code, message=r.json()["message"])
            else:
                return abort(400, message="Task is still queued")
        else:
            return abort(404, message="Unknown task_id")


class DeleteTmpFiles(Resource):

    def delete(self, task_id):
        """
            If task with given id is finished get the task if
            for deleting the temp file.
        """
        queue = rq.get_queue()
        task = queue.fetch_job(task_id)
        if task and task.status == "finished":
            id = task.meta["tmp_file_remove_task"]
            tmptask = queue.fetch_job(id)
            tmptask = queue.run_job(tmptask)
            return tmptask.status
        else:
            return abort(404, message="Unknown task_id")