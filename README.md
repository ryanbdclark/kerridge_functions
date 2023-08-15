# Kerridge functions

## About
Documentation of K8 by Kerridge Commercial systems is very far and few between, documentation of the proprietry coding language used (KCML) is even more rare.
Even Kerridge themselves claim not to have a list of documented functions. 

Anyone that has done report generator or DX development will know how powerful and useful these functions can be, for example rather than writing derived code
to validate a customer's order number why not just use the function Kerridge wrote already to do this, without documentation this is impossible. This project is
an effort to fill this gap, this website has been written to extract "all" the Kerridge functions from the Kerridge source code and display them in a human readable way.
The website also offers a search function to allow searching of keywords in the function names, description, definition, and user defined examples. A working master version
of this site is available at https://kerridge.clarkscsp.co.uk anyone is free to contribute examples to this site and I encourage you to do so.

## Hosting
Although a master version of this site exists, you can use this repository to create your own local version of the site if you wish.

To do so first clone the repository. Edit the config.json file and specify a CRSF secret_key for the appilcation, a database name, database root user and database root user password.
Next in the docker-compose.yml file change the environment variables to match the details just enetered in the config.json.

Once configured run the docker container `docker compose up -d`
