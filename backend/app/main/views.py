from app.main import main


@main.route('/')
def f2():
    return '<form method=POST action="/api/auth/login/">' \
           '<input name="username" type="text"/>' \
           '<input name="password" type="text"/>' \
           '<input value="act" type="submit"/>' \
           '</form>'
