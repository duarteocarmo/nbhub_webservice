import subprocess
import secrets
import fastapi
import uuid
import pathlib
import json
import sys


app = fastapi.FastAPI()
security = fastapi.security.HTTPBasic()

NOTEBOOK_STORAGE = pathlib.Path.cwd() / "notebooks"
SITENAME = "localhost"
SITEPORT = 8000
SITE_POST_LABEL = "notebook-data"
NOTEBOOK_SIZE_LIMIT = 15 # mb



@app.get("/")
async def home():
    home_page = pathlib.Path("static/home.html").read_text()
    return fastapi.responses.HTMLResponse(content=home_page, status_code=200)


@app.post("/upload")
async def respond(request: fastapi.Request):
    unique_id = str(uuid.uuid4()).split("-")[0]
    id_list = [item.stem for item in NOTEBOOK_STORAGE.glob("**/*.html")]

    while unique_id in id_list:
        unique_id = str(uuid.uuid4()).split("-")[0]

    notebook_path = NOTEBOOK_STORAGE / f"{unique_id}.ipynb"
    html_path = NOTEBOOK_STORAGE / f"{unique_id}.html"

    try:

        form = await request.form()
        filename = form[SITE_POST_LABEL].filename
        contents = await form[SITE_POST_LABEL].read()

        notebook_json_keys = json.loads(contents).keys()

        assert "nbformat" in notebook_json_keys
        assert len(notebook_json_keys) == 4
        assert sys.getsizeof(contents) / 1000000 < NOTEBOOK_SIZE_LIMIT

        file = open(notebook_path, "wb")
        file.write(contents)
        file.close()

        converter = subprocess.run(
            ["jupyter", "nbconvert", notebook_path], capture_output=True
        )

        notebook_path.unlink()
        return {
            "status": "success",
            "path": f"http://{SITENAME}:{SITEPORT}/notebook/{html_path.stem}",
            "password": "None",
            "expiry date": "None",
        }
    except Exception as e:
        print(str(e))
        raise fastapi.HTTPException(status_code=404, detail="ERROR")


@app.get("/notebook/{notebook_id}")
async def read_notebook(notebook_id: str):
    file = pathlib.Path(NOTEBOOK_STORAGE / f"{notebook_id}.html")
    if file.is_file():
        return fastapi.responses.FileResponse(file)

    else:
        raise fastapi.HTTPException(
            status_code=404, detail="Notebook does not exist."
        )
