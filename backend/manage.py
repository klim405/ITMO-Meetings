import os

from app import create_app

app = create_app(os.getenv('FLASK_CONFIG', 'default'))


if __name__ == '__main__':
    os.system('. ./init_environ.sh')
    app.run()
