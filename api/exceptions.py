from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    # DRF varsayılan exception handler'ını çağır
    response = exception_handler(exc, context)

    if response is not None:
        # Hata mesajlarını kullanıcı dostu standart bir formata dönüştür
        error_detail = response.data
        message = "İşlem sırasında bir hata oluştu."

        if isinstance(error_detail, dict):
            if 'detail' in error_detail:
                message = str(error_detail['detail'])
            else:
                # İlk hata alanını başlık olarak al
                first_key = next(iter(error_detail))
                first_val = error_detail[first_key]
                if isinstance(first_val, list):
                    first_val = first_val[0]
                message = f"{first_key}: {first_val}"
        elif isinstance(error_detail, list):
            message = str(error_detail[0])

        response.data = {
            "success": False,
            "status_code": response.status_code,
            "error": message,
            "details": error_detail
        }
    else:
        # 500 gibi beklenmeyen hatalar için
        response = Response({
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "error": "Sunucu tarafında beklenmeyen bir hata meydana geldi.",
            "details": str(exc)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
