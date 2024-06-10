# template-flask-rest-api
This repository contains the boilerplate for developing Flask REST API services.
If you use PyCharm as your IDE, it will also load the workspace configuration provided.

## Project structure
```
├───.github
│   └───workflows
├───.idea
│   ├───inspectionProfiles
│   └───runConfigurations
└───app
    ├───api
    │   └───example
    └───config
```

## How to use
**Modify requirements.txt to your needs**

At the root of the project, you can find the `requirements.txt` file. You can modify this file according to your needs. 

**Starting the server**

Run `server.py` and *boom*, the server is alive. By default, the server will bind to port `5000`, you can change this in `server.py`.

**Viewing the Swagger API documentation**

Included in this project is `flask-restx` which enables automatic swagger documentation generation. By default, you can visit this at `http://127.0.0.1:5000/v1/docs`.

## Contribution
If you have any amendments you wish to make, feel free to raise a Pull Request.
Please view `CONTRIBUTING` for more information.


## License
This repository is licensed under the **Mozilla Public License 2.0**. A copy can be found in `LICENSE` located in the project root.