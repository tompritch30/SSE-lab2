from app import process_query


def test_knows_about_dinosaurs():
    assert (
        process_query("dinosaurs") ==
        "Dinosaurs ruled the Earth 200 million years ago"
    )


def test_does_not_know_about_asteroids():
    assert process_query("asteroids") == "Unknown"


def test_does_name():
    assert process_query("What is your name?") == "agiledevs"


def test_does_plus():
    assert process_query("What is 52 plus 56?") == "108"


def test_does_multiplied():
    assert process_query("What is 20 multiplied by 95?") == "1900"
