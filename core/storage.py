import os
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class R2MediaStorage(S3Boto3Storage):
    location = 'media'
    default_acl = 'public-read'
    file_overwrite = False

    def __init__(self, *args, **kwargs):
        custom = (
            getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', '')
            or os.environ.get('R2_PUBLIC_DOMAIN')
            or os.environ.get('R2_PUBLIC_BASE_URL')
        )
        if custom:
            cd = str(custom).strip()
            if cd.startswith('http://') or cd.startswith('https://'):
                try:
                    from urllib.parse import urlparse
                    p = urlparse(cd)
                    cd = p.netloc
                except Exception:
                    pass
            kwargs['custom_domain'] = cd

        self.bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
        self.endpoint_url = getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
        self.region_name = getattr(settings, 'AWS_S3_REGION_NAME', 'auto')
        self.signature_version = getattr(settings, 'AWS_S3_SIGNATURE_VERSION', 's3v4')
        self.addressing_style = getattr(settings, 'AWS_S3_ADDRESSING_STYLE', 'path')
        self.querystring_auth = getattr(settings, 'AWS_QUERYSTRING_AUTH', False)

        super().__init__(*args, **kwargs)

    def url(self, name, parameters=None, expire=None):
        cd = (
            getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', '')
            or os.environ.get('R2_PUBLIC_DOMAIN', '')
        )
        base = (
            getattr(settings, 'R2_PUBLIC_BASE_URL', '')
            or os.environ.get('R2_PUBLIC_BASE_URL', '')
        )
        key = str(name).lstrip('/')
        prefix = str(getattr(self, 'location', '') or '').strip('/')
        if prefix and not key.startswith(prefix + '/'):
            key = f"{prefix}/{key}"
        if cd:
            return f"https://{str(cd).strip('/').strip()}/{key}"
        if base and (base.startswith('http://') or base.startswith('https://')):
            return f"{base.rstrip('/')}/{key}"
        return super().url(name, parameters=parameters, expire=expire)
