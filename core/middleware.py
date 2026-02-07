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

