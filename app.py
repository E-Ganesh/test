"""
Single-file Django + Swagger 2 — No Database
============================================
1. pip install django djangorestframework drf-yasg
2. py app.py
3. Open http://127.0.0.1:8000/swagger/
"""

import os
import sys
import django
from django.conf import settings

# ── Configuration ────────────────────────────────────────────────────────────
settings.configure(
    DEBUG=True,
    SECRET_KEY='single-file-swagger-demo-key',
    ALLOWED_HOSTS=['*'],
    ROOT_URLCONF=__name__,
    INSTALLED_APPS=[
        'django.contrib.contenttypes',  # required by drf_yasg
        'django.contrib.auth',          # required by contenttypes
        'django.contrib.staticfiles',
        'rest_framework',
        'drf_yasg',
    ],
    MIDDLEWARE=[
        'django.middleware.common.CommonMiddleware',
    ],
    # In-memory SQLite — no file created, just satisfies Django internals
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {'context_processors': ['django.template.context_processors.request']},
    }],
    STATIC_URL='/static/',
)

django.setup()

# ── Views ────────────────────────────────────────────────────────────────────
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class HelloWorldView(APIView):
    """Simple Hello World API — no database needed."""

    @swagger_auto_schema(
        operation_summary="Say Hello",
        operation_description="Returns a hello message. No DB required.",
        responses={200: openapi.Response(
            description="Success",
            examples={"application/json": {"message": "Hello, World!", "status": "ok"}}
        )}
    )
    def get(self, request):
        return Response({"message": "Hello, World!", "status": "ok"})

    @swagger_auto_schema(
        operation_summary="Greet by name",
        operation_description='Send `{"name": "Alice"}` and get a personalized greeting.',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Your name'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Personalized greeting",
                examples={"application/json": {"message": "Hello, Alice!", "status": "ok"}}
            ),
            400: "Missing 'name' field",
        }
    )
    def post(self, request):
        name = request.data.get('name')
        if not name:
            return Response({"error": "'name' is required"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": f"Hello, {name}!", "status": "ok"})


class CalculatorView(APIView):
    """In-memory calculator — add, subtract, multiply, divide."""

    @swagger_auto_schema(
        operation_summary="Calculate",
        operation_description='Send `{"a": 10, "b": 5, "operation": "add"}`. Operations: `add` `subtract` `multiply` `divide`',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['a', 'b', 'operation'],
            properties={
                'a':         openapi.Schema(type=openapi.TYPE_NUMBER, description='First number'),
                'b':         openapi.Schema(type=openapi.TYPE_NUMBER, description='Second number'),
                'operation': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['add', 'subtract', 'multiply', 'divide'],
                    description='Operation'
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Result",
                examples={"application/json": {"a": 10, "b": 5, "operation": "add", "result": 15}}
            ),
            400: "Bad input or division by zero",
        }
    )
    def post(self, request):
        a         = request.data.get('a')
        b         = request.data.get('b')
        operation = request.data.get('operation')

        if a is None or b is None or not operation:
            return Response({"error": "Fields 'a', 'b', and 'operation' are required."}, status=400)

        try:
            a, b = float(a), float(b)
        except (ValueError, TypeError):
            return Response({"error": "'a' and 'b' must be numbers."}, status=400)

        ops = {
            'add':      a + b,
            'subtract': a - b,
            'multiply': a * b,
            'divide':   a / b if b != 0 else None,
        }

        if operation not in ops:
            return Response({"error": f"Unknown operation '{operation}'."}, status=400)

        result = ops[operation]
        if result is None:
            return Response({"error": "Division by zero."}, status=400)

        return Response({"a": a, "b": b, "operation": operation, "result": result})


# ── URLs ─────────────────────────────────────────────────────────────────────
from django.urls import path, re_path
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view

schema_view = get_schema_view(
    openapi.Info(
        title="My API",
        default_version='v2',
        description="Basic Django REST API with Swagger 2 — no database",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[AllowAny],
)

urlpatterns = [
    # Swagger 2 UI  →  http://127.0.0.1:8000/swagger/
    re_path(r'^swagger/$',                        schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
    # ReDoc UI      →  http://127.0.0.1:8000/redoc/
    re_path(r'^redoc/$',                          schema_view.with_ui('redoc',   cache_timeout=0), name='redoc-ui'),
    # Raw schema    →  http://127.0.0.1:8000/swagger.json
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0),        name='schema-json'),

    path('api/hello/',      HelloWorldView.as_view(),  name='hello'),
    path('api/calculator/', CalculatorView.as_view(),  name='calculator'),
]

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    from django.core.management import call_command
    print("\n✅  Server starting...")
    print("📄  Swagger UI  →  http://127.0.0.1:8000/swagger/")
    print("📄  ReDoc UI    →  http://127.0.0.1:8000/redoc/")
    print("🔗  Hello API   →  http://127.0.0.1:8000/api/hello/")
    print("🔗  Calculator  →  http://127.0.0.1:8000/api/calculator/\n")
    call_command('runserver', '0.0.0.0:8000')
