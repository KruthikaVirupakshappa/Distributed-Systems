from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND

router=APIRouter()

templates = Jinja2Templates(directory="templates")

VALID_USERNAME = "admin"
VALID_PASSWORD = "password"

@router.get("/")
def home(request:Request):
    user = request.session.get("user")
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user":user
        }
    )

@router.get("/login")
def login_page(request: Request):
    user = request.session.get("user")

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "user": user
        }
    )

@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """
    Handles login form submission.

    - Reads username and password from the form
    - Validates credentials
    - Stores user info in session if valid
    - Displays Bootstrap alert if invalid
    """
    if username == VALID_USERNAME and password == VALID_PASSWORD:
        # Store logged-in user in session
        request.session["user"] = username

        # Redirect user to dashboard
        return RedirectResponse(
            url="/dashboard",
            status_code=HTTP_302_FOUND
        )
        # If credentials are invalid:
    # Re-render login page with error message
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "user": None,
            "error": "Invalid username or password"
        }
    )


@router.get("/dashboard")
def dashboard(request: Request):
    """
    Protected route.

    - Only accessible if user is logged in
    - Redirects to login page if session is missing
    """
    user = request.session.get("user")

    # If user is not logged in, block access
    if not user:
        return RedirectResponse(
            url="/login",
            status_code=HTTP_302_FOUND
        )

    # If user is logged in, render dashboard
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user
        }
    )


@router.get("/logout")
def logout(request: Request):
    """
    Logs the user out.

    - Clears all session data
    - Redirects back to home page
    """
    request.session.clear()

    return RedirectResponse(
        url="/",
        status_code=HTTP_302_FOUND
    )