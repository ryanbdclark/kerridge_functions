import psycopg2
import json
import os


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


def connect():
    """Connect to the PostgreSQL database server"""
    conn = None
    try:
        # read connection parameters
        params = config()

        conn = psycopg2.connect(**params)

        # create a cursor
        cur = conn.cursor()

        cur.execute(
            """SELECT table_schema, table_name from information_schema.tables WHERE table_name like 'modules'"""
        )
        if len(cur.fetchall()):
            cur.execute(
                """
            DROP TABLE modules
            """
            )

        cur.execute(
            """SELECT table_schema, table_name from information_schema.tables WHERE table_name like 'functions'"""
        )
        if len(cur.fetchall()):
            cur.execute(
                """
            DROP TABLE functions
            """
            )


        cur.execute(
            """SELECT table_schema, table_name from information_schema.tables WHERE table_name like 'parameters'"""
        )
        if len(cur.fetchall()):
            cur.execute(
                """
            DROP TABLE parameters
            """
            )

        cur.execute(
            """SELECT table_schema, table_name from information_schema.tables WHERE table_name like 'files'"""
        )
        if len(cur.fetchall()):
            cur.execute(
                """
            DROP TABLE files
            """
            )

        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS modules (
            code varchar(30) NOT NULL,
            description varchar(255) NOT NULL,
            PRIMARY KEY(code)
        )
        """
        )

        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS functions (
            name varchar(255) NOT NULL,
            description varchar(2000),
            detailed_description varchar(2500),
            module varchar(30) NOT NULL,
            definition varchar(140000) NOT NULL,
            PRIMARY KEY(name)
        )
        """
        )

        cur.execute("""SELECT * from pg_type WHERE typname like 'parametertype'""")
        if not len(cur.fetchall()):
            cur.execute("""CREATE TYPE parametertype as ENUM ('in','out')""")

        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS parameters (
            type parametertype NOT NULL,
            name varchar(255),
            description varchar(1000),
            module varchar(30) NOT NULL,
            function varchar(255) NOT NULL,
            PRIMARY KEY(type, module, function, name)
        )
        """
        )

        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS files (
            module varchar(30) NOT NULL,
            function varchar(255) NOT NULL,
            file varchar(30) NOT NULL,
            PRIMARY KEY(module, function, file)
        )
        """
        )

        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS examples (
            sequence SERIAL,
            module varchar(30) NOT NULL,
            function varchar(255) NOT NULL,
            example varchar(140000),
            PRIMARY KEY(sequence)
        )
        """
        )

        # close the communication with the PostgreSQL
        cur.close()
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")


def load_data():
    conn = None
    try:
        # read connection parameters
        params = config()

        conn = psycopg2.connect(**params)

        # create a cursor
        cur = conn.cursor()

        with open(os.getcwd()+"/webapp/data/kerridge_functions.json", "r") as openfile:
            data = json.load(openfile)

        for module, info in data.items():
            cur.execute("""
            INSERT INTO modules (code, description) VALUES(%s,%s)
            """, [module, info['description']])

            for function, function_dict in info['functions'].items():

                description = "" if 'description' not in function_dict.keys() else function_dict['description']
                detailed_description = "" if 'detailed_description' not in function_dict.keys() else function_dict['detailed_description']

                cur.execute("""
                INSERT INTO functions (name, description, detailed_description, module, definition) VALUES(%s,%s,%s,%s,%s)
                """, [function, description, detailed_description, module, function_dict['function_definition']])

                for file in function_dict['files']:
                    cur.execute("""
                    INSERT INTO files (module, file, function) VALUES(%s,%s,%s)
                    """, [module, file, function])

                if 'params_in' in function_dict.keys():
                    for param, description in function_dict['params_in'].items():
                        cur.execute("""
                        INSERT INTO parameters (type, name, description, module, function) VALUES('in',%s,%s,%s,%s)
                        """, [param, description, module, function])

                    for param, description in function_dict['params_out'].items():
                        cur.execute("""
                        INSERT INTO parameters (type, name, description, module, function) VALUES('out',%s,%s,%s,%s)
                        """, [param, description, module, function])

        cur.close()
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")


if __name__ == "__main__":
    connect()
    load_data()
