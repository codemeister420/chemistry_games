from flask import Blueprint, render_template, request, session, redirect, url_for
from .logic import generate_isomer_round, ANSWER_OPTIONS, cleanup_generated_images

isomer_bp = Blueprint(
    "isomer",
    __name__,
    template_folder="templates",
    static_folder="static",
)

@isomer_bp.route("/", methods=["GET", "POST"])
def start():
    if "iso_round" not in session:
        session["iso_round"] = 0
        session["iso_score"] = 0
        session["iso_current_round"] = generate_isomer_round([])
        session["iso_seen"] = []
        session["iso_show_result"] = False
        session["iso_feedback"] = None
        session["iso_user_answer"] = None

    # Answer submitted
    if request.method == "POST" and request.form.get("action") == "answer":
        user_answer = request.form.get("answer")
        round_data = session.get("iso_current_round", {})
        correct_answer = round_data.get("correct_answer")

        session["iso_user_answer"] = user_answer

        if user_answer == correct_answer:
            session["iso_score"] += 1
            session["iso_feedback"] = "✅ Correct!"
        else:
            session["iso_feedback"] = f"❌ Wrong. Correct answer: {correct_answer}"

        session["iso_round"] += 1
        session["iso_show_result"] = True

        return redirect(url_for("isomer.start"))

    # Next button
    if request.method == "POST" and request.form.get("action") == "next":
        if session.get("iso_round", 0) >= 10:
            final_score = session.get("iso_score", 0)

            cleanup_generated_images()

            session.pop("iso_round", None)
            session.pop("iso_score", None)
            session.pop("iso_current_round", None)
            session.pop("iso_seen", None)
            session.pop("iso_show_result", None)
            session.pop("iso_feedback", None)
            session.pop("iso_user_answer", None)

            return render_template("isomer/isomer_quiz_end.html", score=final_score)

        seen = session.get("iso_seen", [])
        old_round = session.get("iso_current_round", {})
        if old_round.get("pair_id"):
            seen.append(old_round["pair_id"])

        session["iso_seen"] = seen
        session["iso_current_round"] = generate_isomer_round(seen)
        session["iso_show_result"] = False
        session["iso_feedback"] = None
        session["iso_user_answer"] = None

        return redirect(url_for("isomer.start"))

    round_data = session.get("iso_current_round", {})

    return render_template(
        "isomer/isomer_quiz.html",
        round=session.get("iso_round", 0) + 1,
        answered=session.get("iso_round", 0),
        score=session.get("iso_score", 0),
        options=ANSWER_OPTIONS,
        feedback=session.get("iso_feedback"),
        user_answer=session.get("iso_user_answer"),
        show_result=session.get("iso_show_result", False),

        mol1_img=round_data.get("mol1_img"),
        mol2_img=round_data.get("mol2_img"),
        mol1_numbered_img=round_data.get("mol1_numbered_img"),
        mol2_numbered_img=round_data.get("mol2_numbered_img"),

        name1=round_data.get("name1"),
        name2=round_data.get("name2"),
        formula1=round_data.get("formula1"),
        formula2=round_data.get("formula2"),
        correct_answer=round_data.get("correct_answer"),
        explanation=round_data.get("explanation"),
        total_pairs=round_data.get("total_pairs"),
    )