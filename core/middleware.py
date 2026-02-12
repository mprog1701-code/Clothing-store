import logging
import uuid


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        rid = str(uuid.uuid4())
        setattr(request, 'request_id', rid)
        try:
            return self.get_response(request)
        except Exception as e:
            try:
                user_id = getattr(getattr(request, 'user', None), 'id', None)
                store_id = request.GET.get('store_id') or request.POST.get('store_id') or None
                logging.exception(
                    'unhandled_exception',
                    extra={'request_id': rid, 'path': request.path, 'user_id': user_id, 'store_id': store_id},
                )
            except Exception:
                pass
            raise

    def process_exception(self, request, exception):
        try:
            rid = getattr(request, 'request_id', None) or str(uuid.uuid4())
            user_id = getattr(getattr(request, 'user', None), 'id', None)
            store_id = request.GET.get('store_id') or request.POST.get('store_id') or None
            logging.exception(
                'process_exception',
                extra={'request_id': rid, 'path': request.path, 'user_id': user_id, 'store_id': store_id},
            )
        except Exception:
            pass
        return None


class ErrorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as e:
            try:
                from django.utils import timezone
                from .models import ErrorLog
                import traceback, hashlib
                tb = getattr(e, '__traceback__', None)
                file_path = ''
                line_number = 0
                if tb:
                    try:
                        last = traceback.extract_tb(tb)[-1]
                        file_path = str(last.filename or '')
                        line_number = int(last.lineno or 0)
                    except Exception:
                        file_path = ''
                        line_number = 0
                error_type = e.__class__.__name__
                message = str(e)
                url = ''
                try:
                    url = request.build_absolute_uri()
                except Exception:
                    url = getattr(request, 'path', '')
                user_obj = getattr(request, 'user', None)
                if not getattr(user_obj, 'is_authenticated', False):
                    user_obj = None
                base = 'backend|' + error_type + '|' + file_path + '|' + str(line_number) + '|' + (message[:120] or '')
                fp = hashlib.sha256(base.encode('utf-8', errors='ignore')).hexdigest()
                obj = ErrorLog.objects.filter(fingerprint=fp).first()
                if obj:
                    obj.occurrences = (obj.occurrences or 0) + 1
                    obj.last_seen = timezone.now()
                    obj.save(update_fields=['occurrences', 'last_seen'])
                else:
                    ErrorLog.objects.create(
                        source='backend',
                        error_type=error_type,
                        message=message,
                        file_path=file_path,
                        line_number=line_number,
                        url=url,
                        user=user_obj,
                        fingerprint=fp,
                        occurrences=1,
                    )
            except Exception:
                pass
            raise
