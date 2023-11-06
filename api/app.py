from flask import Flask, render_template, request

import requests

app = Flask(__name__)


@app.route("/")
def hello_world():
    return render_template("index.html")


@app.route("/github_form")
def github_username_form():
    return render_template("github_form.html")


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


@app.route("/github_form/submit", methods=["POST"])
def submit_github():
    input_username = request.form.get("github_username")
    response = requests.get(f'https://api.github.com/users/'
                            f'{input_username}/repos')
    if response.status_code == 200:
        repos = response.json()
        latest_comments = []

        for repo in repos:
            repo_commit_details = (
                requests.get(f'https://api.github.com/repos/'
                             f'{input_username}/{repo["full_name"]}'
                             f'/commits'))
            if repo_commit_details.status_code == 200:
                commit = repo_commit_details.json()
                latest_comments.append(commit[0]["sha"])

        repos["special_sha"] = latest_comments

    return render_template(
        "github_form_post.html",
        github_username=input_username,
        github_repos=repos
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
