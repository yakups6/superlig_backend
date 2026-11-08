from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class FlexibleJWTAuthentication(JWTAuthentication):
    """
    Özel JWT Kimlik Doğrulayıcı:
    GET, HEAD, OPTIONS gibi salt okunur (güvenli) isteklerde,
    Swagger'da yanlışlıkla hatalı/süresi geçmiş bir token girilmiş olsa bile
    401 hatası vermek yerine isteği anonim kullanıcı olarak kabul eder ve 200 OK ile veriyi döner.
    POST, PUT, PATCH, DELETE gibi yetki gerektiren veri yazma işlemlerinde ise katı kimlik doğrulamayı uygular.
    """
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except exceptions.AuthenticationFailed:
            # Okuma işlemlerinde Swagger oturum hatalarının kullanıcıyı engellemesini önle
            if request.method in ('GET', 'HEAD', 'OPTIONS'):
                return None
            raise


class FlexibleJWTScheme(OpenApiAuthenticationExtension):
    """
    Swagger / OpenAPI arayüzünde yeşil 'Authorize' butonunun
    doğrudan JWT Bearer Token ile görünmesini sağlar.
    """
    target_class = 'api.authentication.FlexibleJWTAuthentication'
    name = 'jwtAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'Giriş (Login) yaptıktan sonra aldığınız "access" token\'ı buraya yapıştırıp Authorize butonuna tıklayın.',
        }
