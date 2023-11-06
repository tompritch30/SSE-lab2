from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def hello_world():
    q = request.args.get("q")
    return process_query(q)


# @app.route("/query?q=dinosaurs", methods=["GET"])
@app.route("/query", methods=["GET"])
def dinosaurs():
    q = request.args.get("q")
    return process_query(q)


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

@app.route("/submit_github", methods=["POST"])
def submit_github():
    input_username = request.form.get("github_username")
    return render_template(
        "github_form_post.html",
        github_username=input_username,
    )


def process_query(word):
    if "dinosaurs" in word:
        return "Dinosaurs ruled the Earth 200 million years ago"
    elif "name" in word:
        return "agiledevs"
    if "largest" in word:
        numbers = word.split(": ")[1]
        numbers = numbers.replace("?", "")
        numbers = numbers.replace(" ", "")
        numbers = numbers.split(",")
        return str(max([int(i) for i in numbers]))

    if "plus" in word:
        numbers = word[:-1].split()
        return str(int(numbers[2]) + int(numbers[4]))
    if "multiplied" in word:
        numbers = word[:-1].split()
        return str(int(numbers[2]) * int(numbers[5]))
    else:
        return "Unknown"
