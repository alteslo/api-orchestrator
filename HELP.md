# Help

## venv:

### Windows
python -m venv venv
venv\Scripts\activate
venv\Scripts\deactivate

### Linux
python3 -m venv venv
venv/bin/activate
venv/bin/deactivate

## pip:

pip freeze > backend/requirements.txt
pip install -r backend/requirements.txt

## Git
git reset --hard HEAD       (going back to HEAD)
git reset --hard HEAD~1     (going back to the commit before HEAD)
git reset --hard f414f31
git pull origin develop
git log --oneline --graph 
git rebase --abort

## poetry
curl -sSL https://install.python-poetry.org | python3 -
poetry --version
poetry init
poetry lock
poetry install
poetry update
poetry show --tree

# Для Python 3.10
poetry env use python3.10
# Для Python 3.11
poetry env use python3.11

poetry env info --path
poetry shell
source $(poetry env info --path)/bin/activate  # Linux/macOS

poetry env remove <python-version>
poetry env list
poetry add --group dev <package-name> 
poetry export --without-hashes --with dev > backend/requirements_dev.txt
poetry export --without dev --without-hashes -o backend/requirements.txt

## Docker
## For Local start you need  to copy .env.local to .env
docker compose up --build
docker compose down && docker volume rm $(docker volume ls -qf dangling=true) && docker compose up
docker-compose -f docker-compose.yml up -d
docker build . -t python-backend -f Dockerfile.compile  --no-cache --progress=plain
docker build . -t [name]:[tag] [location]
docker run --name backend python-backend
docker stop backend
docker rm backend -f
docker rm -vf $(docker ps -aq)
docker volume rm $(docker volume ls -qf dangling=true)
docker volume prune
docker rmi -f $(docker images -aq)
docker exec api ls -lah /app
docker inspect --format "{{json .Mounts}}" api
docker system prune -a
docker exec pg_container env
docker exec -it main-local bash
docker compose -f docker-compose.debug.yml up --build
docker compose -f docker-compose.debug_init.yml up --build

## Linux
sudo mkdir -p {path}
sudo chown -R {UID}:{GID} {path}
chmod -R 764 {path}
sudo chmod ugo+rwx -R {path}
sudo chown -R user:user backend

pg_hba.conf host  all  all 0.0.0.0/0 md5
uvicorn api:app --port 8000 --reload


## MinIO:

### MinIO Docs
<https://github.com/minio/minio-py>
<https://min.io/docs/minio/linux/developers/python/API.html#list_objects>

### MinIO service links


## Tests:

python -m pytest tests/ <!--- Запуск тестов --> 
python -m pytest tests/ -vvv <!--- Запуск тестов с расширенным выводом --> 
python -m pytest tests/ -x <!--- Запуск тестов до первой ошибки теста --> 
python -m pytest tests/ -vvv -x <!--- Запуск тестов с расширенным выводом и до первой ошибки --> 
python -m pytest tests/ -vvv | tee myoutput.log <!--- Запуск тестов с расширенным выводом в файл 

## Pytest in Docker:

docker compose exec files python -m pytest tests/ -vvv
docker compose -f docker-compose.debug.yml exec files python -m pytest tests/ -vvv
