from rest_framework.decorators import api_view
from django.shortcuts import redirect
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
        
        # Store user info in session
        request.session['user'] = {
            'name': token['userinfo']['name'],
            'email': token['userinfo']['email'],
            'picture': token['userinfo']['picture'],
            'sub': token['userinfo']['sub']
        }
        
        # Redirect to React frontend dashboard
        frontend_url = 'http://localhost:3000/dashboard'
        return redirect(frontend_url)
        
    except Exception as e:
        logger.error(f"Callback error: {str(e)}")
        # Redirect to frontend login page on error
        return redirect('http://localhost:3000/login?error=auth_failed')

@api_view(['GET', 'OPTIONS'])
def get_auth_status(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    return Response({
        "isAuthenticated": bool(request.session.get("user")),
        "user": request.session.get("user")
    })

@api_view(['POST'])
def logout(request):
    try:
        # Clear the Django session
        request.session.flush()
        
        # Construct the Auth0 logout URL
        return_to = 'http://localhost:3000/login'
        logout_url = (
            f'https://{settings.AUTH0_DOMAIN}/v2/logout?'
            f'client_id={settings.AUTH0_CLIENT_ID}&'
            f'returnTo={return_to}'
        )
        
        return Response({
            "logoutUrl": logout_url
        })
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response(
            {"error": "Logout failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_profile(request):
    try:
        user = request.session.get('user')
        if not user:
            return Response(
                {"error": "Not authenticated"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        profile_data = {
            'name': user.get('name', ''),
            'email': user.get('email', ''),
            'picture': user.get('picture', ''),
            'bio': user.get('bio', ''),
            'phone': user.get('phone', ''),
            'location': user.get('location', '')
        }
        
        return Response(profile_data)
        
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return Response(
            {"error": "Failed to retrieve profile"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PUT'])
def update_profile(request):
    try:
        user = request.session.get('user')
        if not user:
            return Response(
                {"error": "Not authenticated"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        # Update user data in session
        user.update({
            'name': request.data.get('name', user.get('name')),
            'email': request.data.get('email', user.get('email')),
            'picture': request.data.get('picture', user.get('picture')),
            'bio': request.data.get('bio', user.get('bio')),
            'phone': request.data.get('phone', user.get('phone')),
            'location': request.data.get('location', user.get('location'))
        })
        
        request.session['user'] = user
        request.session.modified = True
        
        return Response(user)
        
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        return Response(
            {"error": "Failed to update profile"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
