
from django.middleware.common import CommonMiddleware

class CustomCorsMiddleware(CommonMiddleware):
    def process_response(self, request, response):
        response["Access-Control-Allow-Origin"] = "*"  # Barcha domenlarga ruxsat
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response