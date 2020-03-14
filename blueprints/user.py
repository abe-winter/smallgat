import flask
from ..util import misc, con

APP = flask.Blueprint('user', __name__)

@APP.route('/home')
@misc.require_session
def home():
  return f'hello {flask.g.session_body["email"]}'

@APP.route('/delete')
@misc.require_session
def delete_me():
  "delete a user, move them to deleted_users table so we can reconstruct as needed"
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    userid = flask.g.session_body['userid']
    cur.execute('select created, modified from users where userid = %s', (userid,))
    created, modified = cur.fetchone()
    cur.excute(
      'insert into deleted_users (userid, email, orig_created, orig_modified) values (%s, %s, %s, %s)',
      (userid, flask.g.session_body['userid'], created, modified)
    )
    cur.execute('delete from users where userid = %s', (userid,))
    dbcon.commit()
  con.REDIS.delete(misc.session_key(flask.session['sessionid']))
  del flask.session['sessionid'] # todo: clear session completely instead
  return flask.redirect(flask.url_for('auth.get_login'))
