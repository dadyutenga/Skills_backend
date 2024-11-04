from rest_framework.decorators import api_view
from rest_framework.response import Response
from authlib.integrations.django_client import OAuth
from django.conf import settings
from django.urls import reverse
from urllib.parse import quote_plus, urlencode

oauth = OAuth()

oauth.register(
    "auth0",
    client_id=settings.AUTH0_CLIENT_ID,
    client_secret=settings.AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration",
)

@api_view(['GET'])
def get_auth_status(request):
    return Response({
        "isAuthenticated": bool(request.session.get("user")),
        "user": request.session.get("user")
    })

@api_view(['GET'])
def callback(request):
    token = oauth.auth0.authorize_access_token(request)
    request.session["user"] = token
    return Response({
        "success": True,
        "user": token
    })

@api_view(['GET'])
def login(request):
    redirect_uri = request.build_absolute_uri(reverse("callback"))
    return Response({
        "authUrl": oauth.auth0.authorize_redirect(request, redirect_uri).url
    })

@api_view(['POST'])
def logout(request):
    request.session.clear()
    return Response({
        "logoutUrl": f"https://{settings.AUTH0_DOMAIN}/v2/logout?"
        + urlencode(
            {
                "returnTo": settings.FRONTEND_URL,
                "client_id": settings.AUTH0_CLIENT_ID,
            },
            quote_via=quote_plus,
        )
    })
