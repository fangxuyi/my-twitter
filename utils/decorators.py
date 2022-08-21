from rest_framework.response import Response
from rest_framework import status
from functools import wraps


def required_params(method='get', params=None):

    if params is None:
        params = []

    # with required_params as a decorator
    # function def decorator is called and return with the new function as an argument
    def decorator(view_func):

        # wraps is another decorator
        # that passes in the view_func, *args, **kwargs
        @wraps(view_func)
        def _wrapped_view(instance, request, *args, **kwargs):
            if method.lower() == 'get':
                data = request.query_params
            else:
                data = request.data
            missing_params = [
                param
                for param in params
                if param not in data
            ]

            if missing_params:
                params_str = ".".join(missing_params)
                return Response({
                    'message': 'missing {} in request'.format(params_str),
                    'success': False,
                }, status=status.HTTP_400_BAD_REQUEST)

            return view_func(instance, request, *args, **kwargs)
        return _wrapped_view
    return decorator