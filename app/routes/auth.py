# -----------------------------------------------------------------
#  app/routes/auth.py
#  Veltrix - Authentication Blueprint (DEMO MODE)
# -----------------------------------------------------------------

from datetime import datetime, timezone

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)

from app.models.user import User

# -----------------------------------------------------------------
# Blueprint
# -----------------------------------------------------------------

auth_bp = Blueprint("auth", __name__)


# -----------------------------------------------------------------
# Register (Disabled)
# -----------------------------------------------------------------

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Demo mode.
    Registration is disabled.
    """

    flash(
        "Mode demo aktif. Gunakan akun demo untuk login.",
        "info"
    )

    return redirect(url_for("auth.login"))


# -----------------------------------------------------------------
# Login
# -----------------------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # =========================================================
        # DEMO ACCOUNT
        # =========================================================

        if (
            email == "admin@vertix.com"
            and password == "admin123"
        ):

            user = User()

            user.id = 1
            user.username = "Administrator"
            user.email = "admin@vertix.com"
            user.password = ""
            user.created_at = datetime.now(timezone.utc)

            login_user(user)

            flash(
                "Welcome Administrator!",
                "success"
            )

            return redirect(url_for("main.dashboard"))

        flash(
            "Email atau password salah.",
            "danger"
        )

    return render_template("login.html")


# -----------------------------------------------------------------
# Logout
# -----------------------------------------------------------------

@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "Logout berhasil.",
        "success"
    )

    return redirect(url_for("main.landing"))