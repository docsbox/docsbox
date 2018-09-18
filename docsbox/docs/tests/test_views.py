import os
import ujson
import unittest
import docsbox
import time
import test_dependencies as dep

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

    # Checking File Type
    def detection_file(self, filename):
        with open(filename, "rb") as source:
            response = self.client.get("/api/document", data={
                "file": source,
            })
        return response

    # Converting and Retrieving a File
    def convert_file_status_queued(self, filename, options):
        with open(filename, "rb") as source:
            response = self.client.post("/api/document/convert", data={
                "file": source,
                "options": ujson.dumps(options),
            })
        return response

    def convert_file_status_finished(self, fileId):
        return self.client.get("/api/document/{0}".format(fileId))

    def retrieve_file_pdf(self, fileId):
        return self.client.get("/api/document/download/"+fileId)

# Group of tests that test valid or invalid UUID
class DocumentUUIDTestCase(BaseTestCase):
    def test_get_task_by_valid_uuid(self):
        filename = os.path.join(self.inputs, "test8.docx")
        response = self.convert_file_status_queued(filename, {
            "formats": ["pdf"]
        })
        json = ujson.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.get("id"))
        self.assertEqual(json.get("status"), "queued")
        
        time.sleep(3)
        
        response = self.convert_file_status_finished(json.get("id"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ujson.loads(response.data), {
            "id": json.get("id"),
            "status": "finished"
        })
        
    def test_get_task_by_invalid_uuid(self):
        response = self.client.get("/api/document/uuid-with-ponies")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(ujson.loads(response.data), {
            "message": "Unknown task_id. You have requested this URI [/api/document/uuid-with-ponies] but did you mean /api/document/upload or /api/document/convert or /api/document/download/<task_id> ?"
        })

 
# Group of tests that test detection of type file and check if it's possible to convert
class DocumentDetectAndConvertTestCase(BaseTestCase):
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
        filename = os.path.join(self.inputs, "test35.sh")
        response = self.convert_file_status_queued(filename, {
            "formats": ["pdf"],
        })
        json = ujson.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json, {
            "message": "Not supported mimetype: 'text/x-shellscript'"
        })

    def test_convert_empty_formats(self):
        filename = os.path.join(self.inputs, "test8.docx")
        response = self.convert_file_status_queued(filename, {
            "formats": []
        })
        json = ujson.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json, {
            "message": "Invalid 'formats' value"
        })

    def test_convert_invalid_formats(self):
        filename = os.path.join(self.inputs, "test8.docx")
        response = self.convert_file_status_queued(filename, {
            "formats": ["csv"]
        })
        json = ujson.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json, {
            "message": "'application/vnd.openxmlformats-offi"
                       "cedocument.wordprocessingml.document'"
                       " mimetype can't be converted to 'csv'"
        })
  
    def test_detect_convert_file_not_required(self):
        for file in dep.listFilesConvertNotRequired:
            filename = os.path.join(self.inputs, file)
            
            # Detect file type   
            response = self.detection_file(filename)
            json = ujson.loads(response.data)    
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json, {
                "mimetype": json.get("mimetype")
            }) 

            # Convert file 
            response = self.convert_file_status_queued(filename, {"formats": ["pdf"]})
            json = ujson.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json, {
                'message': 'File does not need to be converted.'
            })

    def test_detect_convert_file_required(self):
         for file in dep.listFilesConvertRequired:
            filename = os.path.join(self.inputs, file)
            
            # Detect file type   
            response = self.detection_file(filename)
            json = ujson.loads(response.data)    
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json, {
                "mimetype": json.get("mimetype")
            })

            # Convert file 
            response = self.convert_file_status_queued(filename, {"formats": ["pdf"]})
            json = ujson.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(json.get("id"))
            self.assertEqual(json.get("status"), "queued")
            
            time.sleep(3)
            
            response = self.convert_file_status_finished(json.get("id"))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(ujson.loads(response.data), {
                "id": json.get("id"),
                "status": "finished"
            })


# Test that tests all process, detect, convert and retrieve file for output folder
class DocumentDetectConvertAndRetrieveTestCase(BaseTestCase):
    def test_detect_convert_retrieve_file(self):
        mergeLists = dep.listFilesConvertRequired + dep.listFilesUnknown + dep.listFilesConvertNotRequired
        for file in mergeLists:
            filename = os.path.join(self.inputs, file)
            
            # Detect file type   
            response = self.detection_file(filename)
            json = ujson.loads(response.data)    
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json, {
                "mimetype": json.get("mimetype")
            }) 

            # Convert file 
            response = self.convert_file_status_queued(filename, {"formats": ["pdf"]})
            json = ujson.loads(response.data)
            
            if response.status_code == 200:
                if json.get("id") == None:
                    self.assertEqual(json, {
                        'message': 'File does not need to be converted.'
                    })
                else:
                    self.assertTrue(json.get("id"))
                    self.assertEqual(json.get("status"), "queued")
                    
                    time.sleep(3)
                    
                    response = self.convert_file_status_finished(json.get("id"))
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(ujson.loads(response.data), {
                        "id": json.get("id"),
                        "status": "finished"
                    })

                    base_dir = os.path.abspath(os.path.dirname(__file__)+'/outputs')
                    file_dir = os.path.join(base_dir, json.get("id")+".pdf")
                    response = self.retrieve_file_pdf(json.get("id"))      
                    self.assertEqual(response.status_code, 200)
                    with open(file_dir, "wb") as file:
                        file.write(response.data)
                    existFile = os.path.exists(file_dir)
                    self.assertEqual(existFile, True)
                    self.assertIn(os.path.split(file_dir)[1], os.listdir(base_dir))
            else:
                self.assertEqual(response.status_code, 400)
                split_mimetype = json.get("message").split(":")
                self.assertEqual(json, {
                    "message": "Not supported mimetype:"+split_mimetype[1]
                })
