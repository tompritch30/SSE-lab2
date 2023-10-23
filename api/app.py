from flask import Flask, render_template, request


app = Flask(__name__)


@app.route("/")
def hello_world():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    input_name = request.form.get("name")
    input_age = request.form.get("age")
    input_sort = request.form.get("sortcode")
    input_account = request.form.get("accountnumber")
    input_pg = request.form.get("pgnum")
    return render_template("hello.html",
                           name=input_name,
                           age=input_age,
                           sort=input_sort,
                           acc=input_account,
                           pg=input_pg)
