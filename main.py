from flask import Flask, render_template, redirect, url_for, session, request
from flask_sqlalchemy import SQLAlchemy
from rag_module import initialize_rag_chain
from authlib.integrations.flask_client import OAuth

import os
import dotenv
dotenv.load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback_if_not_found')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    github_id = db.Column(db.String(50), unique=True)

oauth = OAuth(app)  # Initialize OAuth with Authlib

oauth.register('github',
    client_id='843d2c55ae8ae77a0598',
    client_secret='49f12611eb5507da82dd2972c263d2ac4612b9c4',
    request_token_params={'scope': 'user:email'},
    base_url='https://api.github.com/',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
)

# Initialize the RAG chain
rag_chain = initialize_rag_chain()
result = rag_chain.invoke("What is Task Decomposition?")
print(result)

# -- Routes --
@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/login')
def login():
    redirect_uri = url_for('authorized', _external=True)
    return oauth.github.authorize_redirect(redirect_uri)

@app.route('/logout')
def logout():
    session.pop('github_token')
    return redirect(url_for('index'))


@app.route('/login/authorized')
def authorized():
    token = oauth.github.authorize_access_token()
    resp = oauth.github.get('https://api.github.com/user')
    profile = resp.json()
    github_id = str(profile['id'])

    user = User.query.filter_by(github_id=github_id).first()

    if user is None:
        new_user = User(github_id=github_id)
        db.session.add(new_user)
        db.session.commit()

    session['user_id'] = github_id

    return redirect(url_for('authorized_success'))

@app.route('/authorized_success')
def authorized_success():
    return render_template('authorized.html', user_db_id=session['user_id'])

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # This line creates the tables based on your SQLAlchemy models
    app.run(debug=True)
