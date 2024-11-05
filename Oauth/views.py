from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.urls import reverse
from authlib.integrations.django_client import OAuth
from urllib.parse import quote_plus, urlencode
import logging

logger = logging.getLogger(__name__)

oauth = OAuth()

oauth.register(
    "auth0",
    client_id=settings.AUTH0_CLIENT_ID,
    client_secret=settings.AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration",
    authorize_url=f"https://{settings.AUTH0_DOMAIN}/authorize",
    token_url=f"https://{settings.AUTH0_DOMAIN}/oauth/token",
    userinfo_url=f"https://{settings.AUTH0_DOMAIN}/userinfo",
)

@api_view(['GET', 'OPTIONS'])
def login(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        redirect_uri = settings.AUTH0_CALLBACK_URL
        return Response({
            "authUrl": oauth.auth0.authorize_redirect(request, redirect_uri).url
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET', 'OPTIONS'])
def callback(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        token = oauth.auth0.authorize_access_token(request)
        request.session["user"] = token
        return Response({
            "success": True,
            "user": token
        })
    except Exception as e:
        logger.error(f"Callback error: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET', 'OPTIONS'])
def get_auth_status(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    return Response({
        "isAuthenticated": bool(request.session.get("user")),
        "user": request.session.get("user")
    })

@api_view(['POST', 'OPTIONS'])
def logout(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
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
