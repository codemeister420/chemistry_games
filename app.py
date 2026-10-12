from flask import Flask, render_template

def create_app():
    app = Flask(__name__)
    app.secret_key = "dev-secret-change-later"

    # import blueprints
    from games.functional_group.routes import functional_group_bp
    from games.isomer.routes import isomer_bp
    from games.carb_snake.routes import carb_snake_bp
    from games.ph_dodger.routes import ph_dodger_bp
    from games.reaction_lab.routes import reaction_lab_bp   
    from games.cell_simulator.routes import cell_simulator_bp

    # register blueprints
    app.register_blueprint(functional_group_bp, url_prefix="/functional-group")
    app.register_blueprint(isomer_bp, url_prefix="/isomer")
    app.register_blueprint(carb_snake_bp, url_prefix="/carb-snake")
    app.register_blueprint(ph_dodger_bp, url_prefix="/ph-dodger")
    app.register_blueprint(reaction_lab_bp, url_prefix="/reaction-lab")
    app.register_blueprint(cell_simulator_bp, url_prefix="/cell-simulator")


    # main site route
    @app.route("/")
    def home():
        return render_template("index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
