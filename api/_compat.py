from functools import wraps

try:
    from flask_jwt_extended import get_jwt_identity, jwt_required
except ImportError:  # pragma: no cover - fallback for local/demo use
    def jwt_required(*args, **kwargs):
        def decorator(fn):
            @wraps(fn)
            def wrapper(*f_args, **f_kwargs):
                return fn(*f_args, **f_kwargs)

            return wrapper

        return decorator

    def get_jwt_identity():
        return "demo-user"
