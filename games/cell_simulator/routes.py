from flask import Blueprint, render_template

from .logic import build_exploration_data, molecule_gallery


cell_simulator_bp = Blueprint(
    "cell_simulator",
    __name__,
    template_folder="templates",
    static_folder="static",
)


@cell_simulator_bp.route("/")
def explore():
    return render_template(
        "cell_simulator/explorer.html",
        exploration_data=build_exploration_data(),
        molecules=molecule_gallery(),
    )