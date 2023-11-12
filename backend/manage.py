import argparse
import os
import sys

from app import create_app

app = create_app(os.getenv('FLASK_CONFIG', 'default'))


def get_args():
    parser = argparse.ArgumentParser(prog='ITMO-Meetings')
    parser.add_argument('filename')
    parser.add_argument('-p', '--port', type=int, default=5000, help='flasky port')
    parser.add_argument('--host', type=str, default='localhost', help='flasky host')
    return parser.parse_args(sys.argv)


if __name__ == '__main__':
    os.system('. ./init_environ.sh')
    args = get_args()
    app.run(port=args.port, host=args.host)
