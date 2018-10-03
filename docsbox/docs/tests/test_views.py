import os
import ujson
import unittest
import docsbox
import time

# SetUp/EndPoints
class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.app = docsbox.app
        self.app.config["TESTING"] = True
        self.app.config["RQ_ASYNC"] = False
        self.inputs = os.path.join(
            self.app.config["BASE_DIR"],
            "docs/tests/inputs/"
        )
        self.client = docsbox.app.test_client()

    def convert_file(self, filename, options):
        with open(filename, "rb") as source:
            response = self.client.post("/api/document/convert", data={
                "file": source,
                "options": ujson.dumps(options),
            })
        return response

    def detection_file(self, filename):
        with open(filename, "rb") as source:
            response = self.client.get("/api/document", data={
                "file": source,
            })
        return response
    
    def upload_file(self, filename):
        with open(filename, "rb") as source:
            response = self.client.post("/api/document/upload", data={
                "file": source,
            })
            print(response)
        return response

# Group of tests that test valid or invalid UUID
class DocumentUUIDTestCase(BaseTestCase):

    def test_get_task_by_valid_uuid(self):
        filename = os.path.join(self.inputs, "test8.docx")
        response = self.convert_file(filename, {
            "formats": ["txt"]
        })
        json = ujson.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.get("id"))
        self.assertEqual(json.get("status"), "queued")
        response = self.client.get("/api/document/{0}".format(json.get("id")))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ujson.loads(response.data), {
            "id": json.get("id"),
            "status": "queued"
        })

    def test_get_task_by_invalid_uuid(self):
        response = self.client.get("/api/document/uuid-with-ponies")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(ujson.loads(response.data), {
            "message": "Unknown task_id. You have requested this URI [/api/document/uuid-with-ponies] but did you mean /api/document/upload or /api/document/convert or /api/document/download/<task_id> ?"
        })

# Group of tests that test if file it's available to uploading
class DocumentUploadAvailableTestCase(BaseTestCase):
    def test_upload_without_need_convert(self):
        filename = os.path.join(self.inputs, "test6.odt")
        
        response = self.upload_file(filename)
        json = ujson.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.get("id"))
        self.assertEqual(json.get("status"), "queued")

    def test_upload_need_convert(self):
        filename = os.path.join(self.inputs, "test8.docx")
        
        response = self.upload_file(filename)
        json = ujson.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json, {
            "message": "File cannot be uploaded needs to be converted"
        })
        
# Group of tests that test detection of type file and check if it's possible to convert
class DocumentDetectionAndConvertTestCase(BaseTestCase):

    def test_convert_without_file(self):
        response = self.client.post("/api/document/convert", data={
            "options": ujson.dumps(["pdf"])
        })
        json = ujson.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json, {
            "message": "file field is required"
        })

    def test_convert_invalid_mimetype(self):
        response = self.convert_file("/bin/sh", {
            "formats": ["pdf"],
        })
        json = ujson.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json, {
            "message": "Not supported mimetype: 'application/x-sharedlib'"
        })

    def test_convert_empty_formats(self):
        filename = os.path.join(self.inputs, "test8.docx")
        response = self.convert_file(filename, {
            "formats": []
        })
        json = ujson.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json, {
            "message": "Invalid 'formats' value"
        })

    def test_convert_invalid_formats(self):
        filename = os.path.join(self.inputs, "test8.docx")
        response = self.convert_file(filename, {
            "formats": ["csv"]
        })
        json = ujson.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json, {
            "message": "'application/vnd.openxmlformats-offi"
                       "cedocument.wordprocessingml.document'"
                       " mimetype can't be converted to 'csv'"
        })

    def test_detection_convert_not_required(self):
        arrFilenames = [
            #.ODT
            "test6.odt*application/vnd.oasis.opendocument.text",
            #.ODP
            "test4.odp*application/vnd.oasis.opendocument.presentation",
            #.ODG
            "test18.odg*application/vnd.oasis.opendocument.graphics",
            #.ODF
            "test19.odf*application/vnd.oasis.opendocument.formula",
            #.ODS
            "test20.ods*application/vnd.oasis.opendocument.spreadsheet",
            #.PNG
            "test9.png*image/png", 
            #.PDF
            "test7.pdf*application/pdf",
            #.TXT
            "test11.txt*text/plain",
            #.CSV
            "test12.csv*text/plain",
            #.EPUB
            "test14.epub*application/epub+zip",
            #.MP4
            "test15.mp4*video/mp4",
            #.JPG
            "test17.jpg*image/jpeg"
            ]
        for file in arrFilenames:
            splitValue = file.split("*")
            filename = os.path.join(self.inputs, splitValue[0])
            
            # Detection file type
            response_detection = self.detection_file(filename)
            json = ujson.loads(response_detection.data)
            self.assertEqual(response_detection.status_code, 200)
            self.assertEqual(json, {
                "mimetype": splitValue[1]
            })
            time.sleep(5)

            # Convert file 
            response = self.convert_file(filename, {"formats": ["pdf"]})
            json = ujson.loads(response.data)
            self.assertEqual(json, {
                'message': 'File does not need to be converted.'
            })
    
    def test_detection_convert_required(self):
        arrFilenames = [
        #.XLSX
        "test1.xlsx*application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        #.DOC
        "test5.doc*application/msword",
        #.DOCX
        "test8.docx*application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        #.PPTX
        "test10.pptx*application/vnd.openxmlformats-officedocument.presentationml.presentation", 
        #.RTF
        "test13.rtf*text/rtf",
        #.PPT
        "test2.ppt*application/vnd.ms-powerpoint",
        #.XLS
        "test22.xls*application/vnd.ms-office",
		#.STW
        "test21.stw*application/octet-stream"
        ]
        for file in arrFilenames:
            splitValue = file.split("*")
            filename = os.path.join(self.inputs, splitValue[0])
            
            # Detection file type
            response_detection = self.detection_file(filename)
            json = ujson.loads(response_detection.data)
            self.assertEqual(response_detection.status_code, 200)
            self.assertEqual(json, {
                "mimetype": splitValue[1]
            })
            time.sleep(5)

            # Convert file 
            response = self.convert_file(filename, {"formats": ["pdf"]})
            json = ujson.loads(response.data)
            self.assertTrue(json.get("id"))
            self.assertEqual(json.get("status"), "queued")


# Group of tests that test all process: detection, convert and retrieve file for a specific folder
class DocumentDetectionConvertAndRetrieveTestCase(BaseTestCase):

    def test_detection_convert_and_retrieving_valid_formats(self):
        filename = os.path.join(self.inputs, "test5.doc")

        # Detection file type
        response_detection = self.detection_file(filename)
        json = ujson.loads(response_detection.data)
        self.assertEqual(response_detection.status_code, 200)
        self.assertEqual(json, {
            "mimetype": 'application/msword'
        })

        # Check if need to be converted
        response_checkConverter = self.upload_file(filename)
        json = ujson.loads(response_checkConverter.data)
        self.assertEqual(response_checkConverter.status_code, 200)
        self.assertEqual(json, {
            "message": "File cannot be uploaded needs to be converted"
        })
        
        # Convert file 
        response = self.convert_file(filename, {"formats": ["pdf"]})
        json = ujson.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.get("id"))
        self.assertEqual(json.get("status"), "queued")
        time.sleep(10)
        response = self.client.get("/api/document/{0}".format(json.get("id")))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ujson.loads(response.data), {
            "id": json.get("id"),
            "status": "finished"
        })
        time.sleep(10)
        base_dir = os.path.abspath(os.path.dirname(__file__)+'/outputs')
        file_dir = os.path.join(base_dir, json.get("id")+".pdf")
        response = self.client.get("/api/document/download/"+json.get("id"))
        self.assertEqual(response.status_code, 200)
        with open(file_dir, "wb") as file:
            file.write(response.data)
        existFile = os.path.exists(file_dir)
        self.assertEqual(existFile, True)
        self.assertIn(os.path.split(file_dir)[1], os.listdir(base_dir))
