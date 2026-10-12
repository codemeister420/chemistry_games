from flask import Blueprint, render_template

ph_dodger_bp = Blueprint(
    "ph_dodger",
    __name__,
    template_folder="templates",
    static_folder="static",
)

@ph_dodger_bp.route("/")
def start():
    return render_template("ph_dodger/game.html")
