import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from flask import Flask, flash, redirect, render_template, request, send_from_directory, url_for

from database.database import get_cases, init_db, save_case
from modules.evidence_analyzer import analyze_evidence
from modules.fingerprint_matcher import compare_fingerprints
from modules.reporter import generate_pdf
from modules.sketch_generator import generate_sketch

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
REPORTS_FOLDER = BASE_DIR / "reports"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp"}

app = Flask(__name__)
app.config["SECRET_KEY"] = "forenvision-ai-secret"
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

UPLOAD_FOLDER.mkdir(exist_ok=True)
REPORTS_FOLDER.mkdir(exist_ok=True)
init_db()


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file_storage) -> Optional[str]:
    if file_storage is None or file_storage.filename == "":
        return None
    if not allowed_file(file_storage.filename):
        raise ValueError("Unsupported file type")
    filename = f"{uuid.uuid4().hex}_{file_storage.filename}"
    destination = Path(app.config["UPLOAD_FOLDER"]) / filename
    file_storage.save(destination)
    return str(destination)


@app.route("/")
def index():
    cases = get_cases(limit=5)
    return render_template("index.html", cases=cases)


@app.route("/evidence", methods=["GET", "POST"])
def evidence():
    if request.method == "POST":
        title = request.form.get("title", "Evidence Review")
        category = request.form.get("category", "Scene")
        summary = request.form.get("summary", "")
        image_file = request.files.get("image")
        try:
            image_path = save_upload(image_file)
            if not image_path:
                flash("Please upload an image.", "warning")
                return redirect(url_for("evidence"))
            analysis = analyze_evidence(image_path)
            case_data = {
                "case_number": f"FV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "title": title,
                "category": category,
                "status": "Active",
                "summary": f"{summary}\n\nEvidence analysis: {analysis['summary']}",
                "evidence_path": image_path,
                "created_at": datetime.utcnow().isoformat(),
            }
            save_case(case_data)
            flash("Evidence analysis case created successfully.", "success")
            return redirect(url_for("cases"))
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("evidence"))
    return render_template("evidence.html")


@app.route("/fingerprint", methods=["GET", "POST"])
def fingerprint():
    if request.method == "POST":
        title = request.form.get("title", "Fingerprint Verification")
        category = request.form.get("category", "Fingerprint")
        summary = request.form.get("summary", "")
        image_a = request.files.get("fingerprint_a")
        image_b = request.files.get("fingerprint_b")
        try:
            path_a = save_upload(image_a)
            path_b = save_upload(image_b)
            if not path_a or not path_b:
                flash("Please upload both fingerprint images.", "warning")
                return redirect(url_for("fingerprint"))
            comparison = compare_fingerprints(path_a, path_b)
            case_data = {
                "case_number": f"FV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "title": title,
                "category": category,
                "status": "Active",
                "summary": f"{summary}\n\nFingerprint comparison: {comparison['summary']}",
                "evidence_path": path_a,
                "fingerprint_score": comparison["similarity"],
                "created_at": datetime.utcnow().isoformat(),
            }
            save_case(case_data)
            flash("Fingerprint comparison case created successfully.", "success")
            return redirect(url_for("cases"))
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("fingerprint"))
    return render_template("fingerprint.html")


@app.route("/sketch", methods=["GET", "POST"])
def sketch():
    if request.method == "POST":
        title = request.form.get("title", "Sketch Synthesis")
        category = request.form.get("category", "Sketch")
        summary = request.form.get("summary", "")
        profile = {
            "hair": request.form.get("hair", "unknown"),
            "eyes": request.form.get("eyes", "unknown"),
            "build": request.form.get("build", "unknown"),
            "clothing": request.form.get("clothing", "unknown"),
            "features": request.form.get("features", "unknown"),
        }
        synthesis = generate_sketch(profile)
        case_data = {
            "case_number": f"FV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "title": title,
            "category": category,
            "status": "Active",
            "summary": f"{summary}\n\nSketch profile: {synthesis['summary']}",
            "sketch_profile": synthesis["composite_profile"],
            "created_at": datetime.utcnow().isoformat(),
        }
        save_case(case_data)
        flash("Sketch synthesis case created successfully.", "success")
        return redirect(url_for("cases"))
    return render_template("sketch.html")


@app.route("/cases")
def cases():
    case_list = get_cases()
    return render_template("cases.html", cases=case_list)


@app.route("/cases/<int:case_id>/pdf")
def download_pdf(case_id: int):
    case = None
    for item in get_cases():
        if item["id"] == case_id:
            case = item
            break
    if not case:
        flash("Case not found.", "warning")
        return redirect(url_for("cases"))

    report_path = REPORTS_FOLDER / f"case_{case_id}.pdf"
    generate_pdf(case, str(report_path))
    return send_from_directory(str(REPORTS_FOLDER), f"case_{case_id}.pdf", as_attachment=True)


@app.route("/static/<path:filename>")
def static_files(filename: str):
    return send_from_directory(str(BASE_DIR / "static"), filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
