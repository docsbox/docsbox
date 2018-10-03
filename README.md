# docsbox [![Build Status](https://travis-ci.org/dveselov/docsbox.svg?branch=master)](https://travis-ci.org/dveselov/docsbox)

`docsbox` is a standalone service that allows you convert office documents, like .docx and .pptx, into more useful filetypes like PDF, for viewing it in browser with PDF.js, or HTML for organizing full-text search of document content.  
`docsbox` uses **LibreOffice** (via **LibreOfficeKit**) for document converting.

# Install

Currently, installing powered by docker-compose:

```bash
$ git clone https://github.com/oikeusministerio/docsbox.git && cd docsbox
$ docker-compose build
$ docker-compose up
```


It'll start this services:

```bash
CONTAINER ID        IMAGE                 COMMAND                  CREATED             STATUS              PORTS                    NAMES
7ce674173732        docsbox_nginx         "/usr/sbin/nginx"        8 minutes ago       Up 8 minutes        0.0.0.0:80->80/tcp       docsbox_nginx_1
f6b55773c71d        docsbox_rqworker      "rq worker -c docsbox"   15 minutes ago      Up 8 minutes                                 docsbox_rqworker_1
662b08daefea        docsbox_rqscheduler   "rqscheduler -H redis"   15 minutes ago      Up 8 minutes                                 docsbox_rqscheduler_1
0364df126b36        docsbox_web           "gunicorn -b :8000 do"   15 minutes ago      Up 8 minutes        8000/tcp                 docsbox_web_1
5e8c8481e288        redis:latest          "docker-entrypoint.sh"   9 hours ago         Up 8 minutes        0.0.0.0:6379->6379/tcp   docsbox_redis_1
```

# Settings (env)

```
REDIS_URL - redis-server url (default: redis://redis:6379/0)
REDIS_JOB_TIMEOUT - job timeout (default: 10 minutes)
ORIGINAL_FILE_TTL - TTL for uploaded file in seconds (default: 10 minutes)
RESULT_FILE_TTL - TTL for result file in seconds (default: 24 hours)
THUMBNAILS_DPI - thumbnails dpi, for bigger thumbnails choice bigger values (default: 90)
LIBREOFFICE_PATH - path to libreoffice (default: /usr/lib/libreoffice/program/)
```

# Test

Uploading File:

```bash
$ curl -X POST -F "file=@test.odt" http://localhost/api/document/upload
{"status": "queued", "id": "32982f1d-6b23-4360-b1aa-c324b538ac4c"}

$ curl -X POST -F "file=@test.docx" http://localhost/api/document/upload
{"message": "File cannot be uploaded needs to be converted"}
```

Checking File Type:

```bash
$ curl -X GET -F "file=@test.odt" http://localhost/api/document
{"mimetype": "application/vnd.oasis.opendocument.text"}
```

Converting and Retrieving a File:

```bash
$ curl -X POST -F "file=@test.docx" http://localhost/api/document/convert
{"status": "queued", "id": "146faa45-893b-4e3f-9251-d5f6dbeb5934"}

$ curl -X GET http://localhost/api/document/146faa45-893b-4e3f-9251-d5f6dbeb5934
{"status": "finished", "id": "146faa45-893b-4e3f-9251-d5f6dbeb5934"}

$ curl -X GET -O http://localhost/api/document/download/146faa45-893b-4e3f-9251-d5f6dbeb5934
```
Download returns converted file (default to pdf)


# API

```
POST (multipart/form-data) /api/document/convert
file=@test.docx
options={ # json, optional
    "formats": ["pdf"] # desired formats to be converted in, optional
    "thumbnails": { # optional
        "size": "320x240",
    } 
}

GET /api/document/{task_id}
```

# Scaling
Within a single physical server, docsbox can be scaled by docker-compose:
```bash
$ docker-compose scale web=4 rqworker=8
```
For multi-host deployment you'll need to create global syncronized volume (e.g. with flocker), global redis-server and mount it at `docker-compose.yml` file.


# Run tests (Ubuntu)
```
1 - cd docsbox/docsbox/docs/tests
2 - docker-compose build
3 - docker-compose up
4 - The tests are run on the docker container and the run result is returned on the console
5 - Folder Inputs to input files for conversion
6 - Folder Outputs to output of converted files
```

# Supported filetypes


| Input                              | Output              | Thumbnails |
| ---------------------------------- | ------------------- | ---------- |
| Document `doc` `docx` `odt` `rtf`  | `pdf` `txt` `html`  | `yes`      |
| Presentation `ppt` `pptx` `odp`    | `pdf` `html`        | `yes`      |
| Spreadsheet `xls` `xlsx` `ods`     | `pdf` `csv` `html`  | `yes`      |
