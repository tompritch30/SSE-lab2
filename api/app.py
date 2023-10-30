from flask import Flask, render_template, request


app = Flask(__name__)


@app.route("/")
def hello_world():
    return render_template("index.html")


# @app.route("/query?q=dinosaurs", methods=["GET"])
@app.route("/query", methods=["GET"])
def dinosaurs():
    q = request.args.get("q")
    process_query(q)


@app.route("/submit", methods=["POST"])
def submit():
    input_name = request.form.get("name")
    input_age = request.form.get("age")
    input_sort = request.form.get("sortcode")
    input_account = request.form.get("accountnumber")
    input_pg = request.form.get("pgnum")
    return render_template(
        "hello.html",
        name=input_name,
        age=input_age,
        sort=input_sort,
        acc=input_account,
        pg=input_pg,
    )


def process_query(word):
    if "dinosaurs" in word:
        return "Dinosaurs ruled the Earth 200 million years ago"
    elif "name" in word:
        return "agiledevs1"
    if "What is 84 plus 32?" in word:
        return 84 + 32
    if "Which of the following numbers is the largest: 37, 65, 21?" in word:
        return 65
    if "What is 43 plus 73?" in word:
        return 42 + 73
    else:
        return "Unknown"
