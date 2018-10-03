from flask import Flask
from flask_rq2 import RQ
from flask_restful import Api
# from flask_cors import CORS
from flask_env_settings import Settings


app = Flask(__name__)
app.config.from_object("docsbox.settings")

Settings(app, rules={
    "REDIS_JOB_TIMEOUT": (int, 60 * 10),
    "ORIGINAL_FILE_TTL": (int, 60),
    "RESULT_FILE_TTL": (int, 60 * 60 * 24),

    "LIBREOFFICE_PATH": (str, "/usr/lib/libreoffice/program/"),

    "THUMBNAILS_DPI": (int, 90),
    "THUMBNAILS_QUANTIZE": (bool, False),
    "THUMBNAILS_QUANTIZE_COLORS": (int, 128),
    "THUMBNAILS_QUANTIZE_COLORSPACE": (str, "rgb"),
})

api = Api(app)
rq = RQ(app)
# cors = CORS(app, resourses={r"/api/*": {"origins":"*"}})

from docsbox.docs.views import *
    
api.add_resource(DocumentTypeView, "/conversion-service/get-file-type/<file_id>")
api.add_resource(DocumentConvertView, "/conversion-service/convert/<file_id>")
api.add_resource(DocumentStatusView, "/conversion-service/status/<task_id>")
api.add_resource(DocumentDownloadView, "/conversion-service/get-converted-file/<task_id>")
api.add_resource(DeleteTmpFiles, "/conversion-service/delete-tmp-file/<task_id>")


if __name__ == "__main__":
    app.run()
