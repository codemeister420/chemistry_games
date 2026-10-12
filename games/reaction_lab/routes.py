import os
from flask import Blueprint, render_template, request, session, url_for, redirect
from .logic import make_round, render_product, MODS, cleanup_old_images

reaction_lab_bp = Blueprint(
    "reaction_lab",
    __name__,
    template_folder="templates",
    static_folder="static",
)

def _gen_dir():
    base = os.path.join(os.path.dirname(__file__), "static", "reaction_lab", "gen")
    os.makedirs(base, exist_ok=True)
    return base

def _label_for(mod_key):
    for k, label in MODS:
        if k == mod_key:
            return label
    return mod_key

@reaction_lab_bp.route("/")
def start():
    # reset any old game
    cleanup_old_images(_gen_dir(), keep=0)
    session.pop("rxn_round", None)
    session.pop("rxn_score", None)
    session.pop("rxn_state", None)
    session.pop("rxn_feedback", None)
    session.pop("rxn_product_img", None)
    session.pop("rxn_product_formula", None)
    session.pop("rxn_show_result", None)
    return render_template("reaction_lab/start.html")

@reaction_lab_bp.route("/play", methods=["GET", "POST"])
def play():
    # init session
    if "rxn_round" not in session:
        session["rxn_round"] = 0
        session["rxn_score"] = 0
        session["rxn_state"] = make_round(_gen_dir())
        session["rxn_feedback"] = None
        session["rxn_product_img"] = None
        session["rxn_product_formula"] = None
        session["rxn_show_result"] = False

    # NEXT button pressed -> advance round
    if request.method == "POST" and request.form.get("action") == "next":
        # clear result UI
        session["rxn_feedback"] = None
        session["rxn_product_img"] = None
        session["rxn_product_formula"] = None
        session["rxn_show_result"] = False

        # end after 10 answered rounds
        if session["rxn_round"] >= 10:
            return redirect(url_for("reaction_lab.end"))

        # new round
        session["rxn_state"] = make_round(_gen_dir())
        return redirect(url_for("reaction_lab.play"))

    # Answer submitted -> render product + show result, DO NOT advance to next starter yet
    if request.method == "POST" and request.form.get("action") == "answer":
        chosen = request.form.get("choice")
        state = session.get("rxn_state", {})
        correct = state.get("correct_mod")

        prod_img, formula, err = render_product(_gen_dir(), state.get("starter_id"), chosen)

        if err:
            session["rxn_feedback"] = f"⚠️ {err}"
            session["rxn_product_img"] = None
            session["rxn_product_formula"] = None
            session["rxn_show_result"] = True
        else:
            session["rxn_product_img"] = prod_img
            session["rxn_product_formula"] = formula

            if chosen == correct:
                session["rxn_score"] += 1
                session["rxn_feedback"] = f"✅ Correct: {_label_for(chosen)}"
            else:
                session["rxn_feedback"] = (
                    f"❌ Wrong: you chose {_label_for(chosen)}. "
                    f"Correct was {_label_for(correct)}."
                )

            # count this as an answered round
            session["rxn_round"] += 1
            session["rxn_show_result"] = True

        return redirect(url_for("reaction_lab.play"))

    # Render UI
    state = session.get("rxn_state", {})
    starter_img = state.get("starter_img")
    starter_url = (
        url_for("reaction_lab.static", filename=f"reaction_lab/gen/{starter_img}")
        if starter_img else None
    )

    product_img = session.get("rxn_product_img")
    product_url = (
        url_for("reaction_lab.static", filename=f"reaction_lab/gen/{product_img}")
        if product_img else None
    )

    return render_template(
        "reaction_lab/play.html",
        round_no=min(session.get("rxn_round", 0) + 1, 10),
        answered=session.get("rxn_round", 0),
        score=session.get("rxn_score", 0),
        goal_text=state.get("goal_text", ""),
        starter_url=starter_url,
        options=state.get("options", []),
        option_labels={k: v for k, v in MODS},
        feedback=session.get("rxn_feedback"),
        product_url=product_url,
        product_formula=session.get("rxn_product_formula"),
        show_result=bool(session.get("rxn_show_result")),
    )

@reaction_lab_bp.route("/end")
def end():
    final_score = session.get("rxn_score", 0)

    cleanup_old_images(_gen_dir(), keep=0)

    # clear game
    session.pop("rxn_round", None)
    session.pop("rxn_score", None)
    session.pop("rxn_state", None)
    session.pop("rxn_feedback", None)
    session.pop("rxn_product_img", None)
    session.pop("rxn_product_formula", None)
    session.pop("rxn_show_result", None)

    return render_template("reaction_lab/end.html", score=final_score)
