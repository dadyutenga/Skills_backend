from rest_framework.decorators import api_view
from django.shortcuts import redirect
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.urls import reverse
from authlib.integrations.django_client import OAuth
from urllib.parse import quote_plus, urlencode
import logging
from .models import User

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
        userinfo = token['userinfo']
        
        # Create or update user in database
        user, created = User.objects.update_or_create(
            auth0_id=userinfo['sub'],
            defaults={
                'name': userinfo['name'],
                'email': userinfo['email'],
                'picture': userinfo['picture']
            }
        )
        
        # Store user info in session
        request.session['user'] = {
            'id': str(user.id),
            'auth0_id': user.auth0_id,
            'name': user.name,
            'email': user.email,
            'picture': user.picture,
            'bio': user.bio,
            'phone': user.phone,
            'location': user.location
        }
        
        # Redirect to React frontend dashboard
        frontend_url = 'http://localhost:3000/dashboard'
        return redirect(frontend_url)
        
    except Exception as e:
        logger.error(f"Callback error: {str(e)}")
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
        session_user = request.session.get('user')
        if not session_user:
            return Response(
                {"error": "Not authenticated"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            user = User.objects.get(id=session_user['id'])
            profile_data = {
                'id': str(user.id),
                'name': user.name,
                'email': user.email,
                'picture': user.picture,
                'bio': user.bio,
                'phone': user.phone,
                'location': user.location,
                'age': user.age,
                'specialization': user.specialization
            }
            return Response(profile_data)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return Response(
            {"error": "Failed to retrieve profile"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PUT'])
def update_profile(request):
    try:
        session_user = request.session.get('user')
        if not session_user:
            return Response(
                {"error": "Not authenticated"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        try:
            user = User.objects.get(id=session_user['id'])
            
            # Update user data in database
            user.name = request.data.get('name', user.name)
            user.email = request.data.get('email', user.email)
            user.picture = request.data.get('picture', user.picture)
            user.bio = request.data.get('bio', user.bio)
            user.phone = request.data.get('phone', user.phone)
            user.location = request.data.get('location', user.location)
            user.age = request.data.get('age', user.age)
            user.specialization = request.data.get('specialization', user.specialization)
            user.save()
            
            # Update session data
            request.session['user'] = {
                'id': str(user.id),
                'auth0_id': user.auth0_id,
                'name': user.name,
                'email': user.email,
                'picture': user.picture,
                'bio': user.bio,
                'phone': user.phone,
                'location': user.location,
                'age': user.age,
                'specialization': user.specialization
            }
            
            return Response({
                "message": "Profile updated successfully",
                "user": request.session['user']
            })
            
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        return Response(
            {"error": "Failed to update profile"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
