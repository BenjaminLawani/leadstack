from uuid import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Request,
    Path,
    Query,
)
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_sso.sso.google import GoogleSSO


from .models import User
from .schemas import (
    UserCreate,
    UserResponse,
    Token
)

from src.core.config import settings, templates
from src.core.enums import LoginMethod
from src.core.db import get_db
from src.core.security import (
    create_access_token,
    create_refresh_token,
    generate_otp_code,
    get_current_user,
    verify_password,
    hash_password
)

from src.core.utils import fm

google_sso = GoogleSSO(
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    redirect_uri=settings.GOOGLE_REDIRECT_URI,
    allow_insecure_http=True,
)

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@auth_router.post(
    "/get-started", 
    response_model=UserResponse)

def create_email_user(
    request: Request,
    user: UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(User.email == user.email).one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists"
        )
    try:
        new_user = User(**user.model_dump(exclude={"first_name", "last_name"}))
        new_user.email = user.email.lower().strip()
        new_user.name = f"{user.first_name} {user.last_name}"
        new_user.password = hash_password(user.password)
        new_user.login_method = LoginMethod.LOCAL

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return UserResponse.model_validate(new_user)


    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{e.orig}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f"An error occurred while trying to create an account for {user.email}"
        )

@auth_router.post("/login")
def login_email_user(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.email == form_data.username.lower().strip()).one_or_none()
    if not db_user or not verify_password(form_data.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(
        {
            "sub": str(db_user.id),
            "email":db_user.email
        }
    )
    return Token(
        access_token=access_token,
        token_type="bearer"
    )

@auth_router.get("/google-login")
async def google_auth_route():
    async with google_sso:
        return await google_sso.get_login_redirect(params={"prompt": "consent",
                                                        "access_type": "offline"})



@auth_router.get("/google-callback")
async def login_google_user(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        async with google_sso:
            google_user = await google_sso.verify_and_process(request)

            user_email = google_user.email.lower().strip()
            name = google_user.display_name

            if user_email is None:
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Google SSO did not return an email address."
                )

            db_user = db.query(User).filter(User.email == user_email).first()
            if not db_user:
                db_user = User(
                    name = name,
                    email=user_email,
                    login_method = LoginMethod.GOOGLE
                )

                db.add(db_user)
                db.commit()
                db.refresh(db_user)

            # Issue JWT token
            access_token = create_access_token(
                {
                    "sub": str(db_user.id),
                    "email": db_user.email,
                }
            )
            
            # Return HTML page that stores token and redirects
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Redirecting...</title>
            </head>
            <body>
                <script>
                    localStorage.setItem('access_token', '{access_token}');
                    localStorage.setItem('token_type', 'bearer');
                    window.location.href = '/dashboard.html';
                </script>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred: {e}"
        )

@auth_router.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@auth_router.get("/get-started")
async def get_started(request: Request):
    return templates.TemplateResponse("get-started.html", {"request": request})

@auth_router.get("/me", response_model=UserResponse)
def me(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return UserResponse.model_validate(current_user)