"""Моя библиотека для работы бота с константами на GitHub

Модуль загружает в бота весь графический и текстовый контент
"""
import GitHubConnect
import json

from justdotenv import DotEnv
env = DotEnv()

CONST_CONTENT_LIST = ["image", "audio", "doc"]

# сохраняем список администраторов бота
try:
    CONST_ADMINLIST = list(map(str, env.TELEGRAM_ADMINLIST_COMMONSEP.split(",")))
except AttributeError:
    CONST_ADMINLIST = [str(env.TELEGRAM_YOUR_ID)]

# название файла с константами для бота
CONST_FILENAME = "const.json"

# название ветки на GitHub для хранения контента
CONST_GITHUB_CONTENT_BRANCH_NAME = "content"

# названия папок с контентом на GitHub
CONST_DIR_NAMES = {
    "audios": "audios",
    "images": "images",
    "hints": "hints",
    "replicates": "replicates",
    "files": "files"
}

github = GitHubConnect.GitHub(
    token=env.GITHUB_TOKEN,
    username=env.GITHUB_USERNAME,
    repo=env.GITHUB_REPOSITORY_NAME
)

# получаем файл с константами
CONST = json.loads(github.get_file(filepath=CONST_FILENAME, branch=CONST_GITHUB_CONTENT_BRANCH_NAME))

# загружаем в бота весь текст реплик заранее, чтобы он отвечал быстрее
answer_texts = []
for file in github.dirlist(CONST_DIR_NAMES["replicates"], CONST_GITHUB_CONTENT_BRANCH_NAME):
    answer_texts.append(github.get_file(file["path"], CONST_GITHUB_CONTENT_BRANCH_NAME))

# создаем список с пользователями, которые написали боту
# причем он уже наполнен тем, что лежит в файле user_progress.json в ветке content
try:
    list_players = json.loads(github.get_file(CONST["userProgressFile"], CONST_GITHUB_CONTENT_BRANCH_NAME))
except Exception:
    github.create(filepath=CONST["userProgressFile"], filecontent="{}", branch=CONST_GITHUB_CONTENT_BRANCH_NAME)
    list_players = dict()
