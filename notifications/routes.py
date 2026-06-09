from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from ext import bcrypt, mail, get_db_connection
from notifications.models import Notification

notifications_bp = Blueprint('notification', __name__)

@notifications_bp.route("/notifications")
@login_required
def notifications():
    user_id = current_user.id
    notifications = Notification.get_notifications(user_id)
    return render_template("notifications.html", notifications=notifications)