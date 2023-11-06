from flask import Flask, render_template, request
from datetime import datetime
import pytz

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
    response = (requests.get
                (f"https://api.github.com/users/{input_username}/repos"))

    if response.status_code == 200:
        repos = response.json()
        for repo in repos:
            repo_commit_details = requests.get(
                f'https://api.github.com/repos/{repo["full_name"]}/commits'
            )

            if repo_commit_details.status_code == 200:
                commits = repo_commit_details.json()
                if commits:
                    # Get the first commit's data
                    commit_data = commits[0]["commit"]
                    author_data = commit_data["author"]

                    # Format the date string to a more readable format
                    date_str = author_data["date"]
                    date_obj = (datetime.strptime
                                (date_str, "%Y-%m-%dT%H:%M:%SZ"))
                    date_obj = date_obj.replace(
                        tzinfo=pytz.utc
                    )  # Attach UTC timezone information

                    # Here you can adjust the
                    # date format as per your requirement
                    formatted_date = (
                        date_obj.strftime("%B %d, %Y %H:%M:%S UTC"))

                    # Add the cleaned up data to the repo dictionary
                    repo["special_sha"] = commits[0]["sha"]
                    repo["author_name"] = author_data["name"]
                    repo["author_email"] = author_data["email"]
                    repo["commit_date"] = formatted_date
                else:
                    repo["special_sha"] = "No commits available"
                    repo["author_name"] = ""
                    repo["author_email"] = ""
                    repo["commit_date"] = ""
            else:
                repo["special_sha"] = "Error fetching commits"
                repo["author_name"] = ""
                repo["author_email"] = ""
                repo["commit_date"] = ""
        return render_template(
            "github_form_post.html",
            github_username=input_username,
            github_repos=repos
        )
    else:
        repos = None
        error_message = ("Failed to fetch repositories. "
                         "Please check the GitHub username and try again.")
        return render_template(
            "github_form_post.html",
            github_username=input_username,
            github_repos=repos,
            error_message=error_message,
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
