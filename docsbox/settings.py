import os

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
RQ_REDIS_URL = REDIS_URL

BASE_DIR = os.path.abspath(os.path.dirname(__file__)) 
MEDIA_PATH = os.path.join(BASE_DIR, "media/")
MEDIA_URL = "/media/"

SUPPORTED_FORMATS = { "pdf", "txt", "csv", "jpeg", "png" }

GENERATE_THUMBNAILS = False # If True enables the option of thumbnails generation

DOCUMENT_EXPORT_FORMATS = ["pdf", "txt"]
SPREADSHEET_EXPORT_FORMATS = ["pdf", "csv"]
PRESENTATION_EXPORT_FORMATS = ["pdf"]
IMAGE_EXPORT_FORMATS = ["jpeg", "png"]
PDF_EXPORT_FORMATS = ["pdf"]

ACCEPTED_MIMETYPES = {
    # LibreOffice Writer
    "application/vnd.oasis.opendocument.text": {
        "format": "odt",
    },

    # LibreOffice Calc
    "application/vnd.oasis.opendocument.spreadsheet": {
        "format": "ods",
    },

    # LibreOffice Impress
    "application/vnd.oasis.opendocument.presentation": {
        "format": "odp",
    },

    # LibreOffice Draw
    "application/vnd.oasis.opendocument.graphics": {
        "format": "odg",
    },

    # LibreOffice Math
    "application/vnd.oasis.opendocument.formula": {
        "format": "odf",
    },

    # Comma Seperated Values
    "text/plain": {
        "format": "txt",
    },

    # Comma Seperated Values
    "text/scv": {
        "format": "csv",
    },

    # Portable Document Format
    "application/pdf": {
        "format": "pdf",
    },

    # EPUB
    "application/epub+zip": {
        "format": "epub",
    },

    # Free Lossless Audio Codec
    "audio/flac": {
        "format": "flac"
    },

    # Advanced Video Coding
    "video/mp4": {
        "format": "mp4"
    },

    # Joint Photographic Group
    "image/jpeg": {
        "format": "jpeg"
    },

    # Portable Network Graphics
    "image/png": {
        "format": "png"
    },
}

CONVERTABLE_MIMETYPES = {
    # Microsoft Word 2003
    "application/msword": {
        "formats": DOCUMENT_EXPORT_FORMATS,
    },
    
    # Microsoft Word 2007
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
        "formats": DOCUMENT_EXPORT_FORMATS,
    },

    # Microsoft Excel 2003
    "application/vnd.ms-excel": {
        "formats": SPREADSHEET_EXPORT_FORMATS,
    },

    # Microsoft Excel 2007
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
        "formats": SPREADSHEET_EXPORT_FORMATS,
    },

    # Microsoft Powerpoint 2003
    "application/vnd.ms-powerpoint": {
        "formats": PRESENTATION_EXPORT_FORMATS,
    },

    # Microsoft Powerpoint 2007
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": {
        "formats": PRESENTATION_EXPORT_FORMATS,
    },

    # Rich Text Format
    "text/rtf": {
        "formats": DOCUMENT_EXPORT_FORMATS,
    },

    #XML OpenOffice
    # sxw
    "application/vnd.sun.xml.writer": {
        "formats": DOCUMENT_EXPORT_FORMATS,
    },

    # sxc
    "application/vnd.sun.xml.calc": {
        "formats": SPREADSHEET_EXPORT_FORMATS,
    },

    # sxd
    "application/vnd.sun.xml.draw": {
        "formats": PRESENTATION_EXPORT_FORMATS,
    },

    # sxi
    "application/vnd.sun.xml.impress": {
        "formats": PRESENTATION_EXPORT_FORMATS,
    },

    # sxm
    "application/vnd.sun.xml.math": {
        "formats": SPREADSHEET_EXPORT_FORMATS,
    },

    # sxg
    "application/vnd.sun.xml.writer.global": {
        "formats": DOCUMENT_EXPORT_FORMATS,
    },

    #Apple Keynote
    "application/vnd.apple.keynote":{
        "formats": PRESENTATION_EXPORT_FORMATS,
    },

    #Apple Numbers
    "application/vnd.apple.numbers":{
        "formats": SPREADSHEET_EXPORT_FORMATS,
    },

    #Apple Pages
    "application/vnd.apple.pages":{
        "formats": DOCUMENT_EXPORT_FORMATS,
    },
}

DEFAULT_OPTIONS = {
    "formats": ["pdf"]
}
