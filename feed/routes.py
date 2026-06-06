from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from feed.models import Produits



produits_bp = Blueprint('produits', __name__)


@produits_bp.route('/')