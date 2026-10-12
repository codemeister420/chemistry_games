from flask import Blueprint, render_template

carb_snake_bp = Blueprint(
    "carb_snake",
    __name__,
    template_folder="templates",
    static_folder="static",
)

@carb_snake_bp.route("/")
def start():
    return render_template("carb_snake/game.html")
