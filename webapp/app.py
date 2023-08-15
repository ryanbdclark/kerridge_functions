import json
import os

import psycopg2
import psycopg2.extras
from flask import Flask, redirect, render_template, request, url_for
from flask_tinymce import TinyMCE
from flask_wtf import CSRFProtect
from waitress import serve

tinymce = TinyMCE()
crsf = CSRFProtect()


def config(filename="/workspaces/kerridge_functions/config.json"):
    db = {}

    if os.path.isfile(filename):
        with open(filename, "r") as config_file:
            config = json.load(config_file)

            if "database" not in config.keys():
                raise Exception("Database section not found in the config file")

            db = config["database"]

    else:
        print("config file not found")

    return db


def get_db_connection():
    """Connect to the PostgreSQL database server"""
    conn = None
    # read connection parameters
    params = config()
    conn = psycopg2.connect(**params)
    return conn


def get_modules():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""SELECT * FROM modules""")
    modules = cur.fetchall()
    cur.close()
    return modules


def format_functions(functions):
    return {
        function["name"]: {
            "description": function["description"],
            "detailed_description": function["detailed_description"],
            "module": function["module"],
            "definition": function["definition"],
            "examples": {},
            "params_in": {},
            "params_out": {},
        }
        for function in functions
    }


def execute_search(search_term):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    response = request.form.to_dict()
    formatted_functions = {}
    functions = []

    if "search-name" in response.keys():
        cur.execute(
            """SELECT * FROM functions WHERE name ILIKE %s""",
            [
                "%" + search_term + "%",
            ],
        )

        functions.append(cur.fetchall())

    if "search-description" in response.keys():
        cur.execute(
            """SELECT * FROM functions WHERE description ILIKE %s OR detailed_description ILIKE %s""",
            [
                "%" + search_term + "%",
                "%" + search_term + "%",
            ],
        )

        functions.append(cur.fetchall())

    if "search-definition" in response.keys():
        cur.execute(
            """SELECT * FROM functions WHERE definition ILIKE %s""",
            [
                "%" + search_term + "%",
            ],
        )

        functions.append(cur.fetchall())

    if "search-examples" in response.keys():
        cur.execute(
            """SELECT * FROM functions LEFT JOIN examples ON functions.module = examples.module AND functions.name = examples.function WHERE example ILIKE %s""",
            [
                "%" + search_term + "%",
            ],
        )

        functions.append(cur.fetchall())

    for function_list in functions:
        formatted_functions = formatted_functions | format_functions(function_list)

    return formatted_functions


def get_functions(module):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    formatted_functions = {}
    cur.execute("""SELECT * FROM functions WHERE module = %s""", [module])

    formatted_functions = format_functions(cur.fetchall())

    cur.close()
    return formatted_functions


def get_function(module, function):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute(
        """SELECT * FROM functions WHERE module = %s AND name = %s""",
        [module, function],
    )
    function_dict = cur.fetchone()

    formatted_function = format_functions([function_dict])[function]
    formatted_function["name"] = function
    formatted_function["files"] = []

    cur.execute(
        """SELECT * FROM parameters WHERE module = %s AND function = %s""",
        [formatted_function["module"], formatted_function["name"]],
    )

    params = cur.fetchall()
    for param in params:
        if param["type"] == "in":
            formatted_function["params_in"][param["name"]] = param["description"]
        else:
            formatted_function["params_out"][param["name"]] = param["description"]

    cur.execute(
        """SELECT sequence, example FROM examples WHERE module=%s AND function=%s ORDER BY sequence ASC""",
        [formatted_function["module"], formatted_function["name"]],
    )

    examples = cur.fetchall()

    for example in examples:
        formatted_function["examples"][example["sequence"]] = example["example"]

    cur.close()

    cur = conn.cursor()
    cur.execute(
        """SELECT file FROM files WHERE module = %s AND function = %s""",
        [formatted_function["module"], formatted_function["name"]],
    )

    formatted_function["files"] = cur.fetchall()

    cur.close()
    return formatted_function


def get_module_description(module):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """SELECT description FROM modules WHERE code = %s""",
        [module],
    )
    module = cur.fetchone()
    cur.close()
    return module[0]


if os.path.isfile("config.json"):
    with open("config.json", "r") as config_file:
        config_file = json.load(config_file)

        if "secret_key" not in config_file.keys():
            raise Exception("secret key not found in the config file")

    secret_key = config_file["secret_key"]

app = Flask(__name__)
app.config["SECRET_KEY"] = secret_key
app.config["DEBUG"] = True

crsf.init_app(app)
tinymce.init_app(app)


@app.route("/")
def index():
    return render_template("index.html", modules=get_modules())


@app.route("/module/<module>")
def module_page(module):
    return render_template(
        "module.html",
        module=module,
        description=get_module_description(module),
        functions=get_functions(module),
    )


@app.route("/module/<module>/function/<function>")
def view_function(module, function):
    return render_template(
        "function.html", name=function, function=get_function(module, function)
    )


@app.route("/search", methods=["POST"])
def search():
    search_term = request.form.to_dict()["search"]
    return render_template(
        "module.html",
        module=search_term,
        description="",
        functions=execute_search(search_term),
    )


@app.route("/module/<module>/function/<function>/add_example", methods=["POST"])
def add_example(module, function):
    response = request.form.to_dict()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO examples (module, function, example) VALUES (%s,%s,%s)",
        [module, function, response["example_text_create"]],
    )

    cur.close()
    conn.commit()

    return redirect(url_for("view_function", module=module, function=function))


@app.route(
    "/module/<module>/function/<function>/example/<example_sequence>/delete",
    methods=["POST"],
)
def delete_example(module, function, example_sequence):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM examples WHERE sequence = %s", [example_sequence])
    cur.close()
    conn.commit()
    return redirect(url_for("view_function", module=module, function=function))


@app.route(
    "/module/<module>/function/<function>/example/<example_sequence>/edit",
    methods=["POST"],
)
def edit_example(module, function, example_sequence):
    response = request.form.to_dict()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE examples SET example=%s WHERE sequence = %s",
        [response["example_text_edit_" + example_sequence], example_sequence],
    )
    cur.close()
    conn.commit()
    return redirect(url_for("view_function", module=module, function=function))


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5002)
