from flask import Blueprint, render_template, request, session
from .logic import generate_quiz_round, cleanup_generated_images

functional_group_bp = Blueprint(
    "functional_group",
    __name__,
    template_folder="templates",
    static_folder="static",
)

@functional_group_bp.route("/", methods=["GET", "POST"])
def start():
    # init game state
    if "fg_round" not in session:
        session["fg_round"] = 0
        session["fg_score"] = 0
        session["fg_seen"] = []
        session["fg_current"] = None

    feedback = None

    # Handle answer submission
    if request.method == "POST":
        user_answer = request.form.get("answer", "")
        correct_answer = session.get("fg_current")

        if correct_answer:
            if user_answer == correct_answer:
                session["fg_score"] += 1
                feedback = "✅ Correct!"
            else:
                feedback = f"❌ Wrong! Correct answer: {correct_answer}"

        session["fg_round"] += 1

    # End condition (10 rounds)
    if session["fg_round"] >= 10:
        final_score = session["fg_score"]

        cleanup_generated_images()

        # clear just this game's session keys
        session.pop("fg_round", None)
        session.pop("fg_score", None)
        session.pop("fg_seen", None)
        session.pop("fg_current", None)

        return render_template("functional_group/quiz_end.html", score=final_score)

    # Generate a new question, trying to avoid repeats (best-effort)
    max_attempts = 25
    img_relpath = None
    fg_name = None
    options = None

    seen = set(session.get("fg_seen", []))

    for _ in range(max_attempts):
        img_relpath, fg_name, options = generate_quiz_round()
        if fg_name not in seen:
            break

    # If repeats happen anyway (small pool / random chance), still proceed
    session["fg_current"] = fg_name
    session["fg_seen"] = session.get("fg_seen", []) + [fg_name]

    return render_template(
        "functional_group/functional_group.html",
        molecule_img=img_relpath,          # e.g. "generated/quiz_xxx.png"
        score=session["fg_score"],
        round=session["fg_round"] + 1,     # display 1..10
        feedback=feedback,
        options=options,
    )
