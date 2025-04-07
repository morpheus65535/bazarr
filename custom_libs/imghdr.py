import filetype

_IMG_MIME = {
    'image/jpeg': 'jpeg',
    'image/png': 'png',
    'image/gif': 'gif'
}

def what(_, img):
    img_type = filetype.guess(img)
    return _IMG_MIME.get(img_type.mime) if img_type else None
