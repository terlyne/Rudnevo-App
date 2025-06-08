from flask import Blueprint, request, render_template


panel = Blueprint("panel", __name__, template_folder="templates")


@panel.route("/", methods=["GET", "POST"])
def home():
    return render_template("panel/home.html")
    
    ...