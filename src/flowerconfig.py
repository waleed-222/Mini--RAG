from dotenv import dotenv_values
config= dotenv_values(".env")

# Flower Configuration
port =5555
max_tasks = 10000
auto_refresh = True

#db= 'flower.db' # SQLite database for presistent storage

# Authentication
basic_auth = [f'admin:{config["CELERY_FLOWER_PASSWORD"]}']