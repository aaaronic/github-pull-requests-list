import os

from flask import Flask, request, g, session, redirect, url_for, escape
from flask import render_template_string, render_template
from flask.ext.github import GitHub

from lib import *

app = Flask(__name__)
app.secret_key = os.environ['APP_SECRET']
app.config.from_object(__name__)

app.config['GITHUB_CLIENT_ID'] = os.environ['GITHUB_CLIENT_ID']
app.config['GITHUB_CLIENT_SECRET'] = os.environ['GITHUB_CLIENT_SECRET']


github = GitHub(app)

@app.route('/')
def index():

  prs = [issue for issue in github.get('issues?per_page=100&filter=all') if 'pull_request' in issue]

  prs = [github.get(pr['pull_request']['url'].replace(github.base_url, "")) for pr in prs]

  g.repos = {}  # group these prs by-repo
  for pr in prs:
    repo_name = pr['base']['repo']['full_name']
    if repo_name in g.repos:
      g.repos[repo_name]['pull_requests'].append(pr)
    else:
      g.repos[repo_name] = pr['base']['repo']
      g.repos[repo_name]['pull_requests'] = [pr]

  g.repos = g.repos.values()
  return render_template('index.html')

@app.route('/login')
def login():
  if 'oauth_token' in session:
    flash("Already Logged In!")
    return redirect(url_for('index'))
  else:
    return github.authorize(scope="repo")

@app.route('/github-callback')
@github.authorized_handler
def authorized(oauth_token):
  next_url = request.args.get('next') or url_for('index')
  if oauth_token is None:
    flash("Authorization failed.")
    return redirect(next_url)

  #user = User.query.filter_by(github_access_token=oauth_token).first()
  #if user is None:
    #user = User(oauth_token)
    #db_session.add(user)

  #user.github_access_token = oauth_token
  #db_session.commit()
  session['oauth_token'] = oauth_token
  session.permanent = True
  return redirect(next_url)

@github.access_token_getter
def token_getter():
  return session['oauth_token'] if 'oauth_token' in session else None

if __name__ == '__main__':
    app.run(debug=True)
