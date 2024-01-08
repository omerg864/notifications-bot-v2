export PATH="${PATH}:/opt/render/project/.render/chrome/opt/google/chrome"

pip install -r requirements.txt

gunicorn main:app -k uvicorn.workers.UvicornWorker