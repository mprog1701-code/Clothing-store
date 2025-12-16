import os
from storages.backends.s3boto3 import S3Boto3Storage


class R2MediaStorage(S3Boto3Storage):
    location = 'media'
    default_acl = 'public-read'
    file_overwrite = False

    def __init__(self, *args, **kwargs):
        custom = os.environ.get('R2_PUBLIC_DOMAIN') or os.environ.get('R2_PUBLIC_BASE_URL')
        if custom:
            kwargs['custom_domain'] = custom
        super().__init__(*args, **kwargs)

