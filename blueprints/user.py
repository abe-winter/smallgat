import flask
from ..util import misc, con

APP = flask.Blueprint('user', __name__)

@APP.route('/home')
@misc.require_session
def home():
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    cur.execute('select name, age, address from users where userid = %s', (flask.g.session_body['userid'],))
    name, age, address = cur.fetchone()
  return flask.render_template('home.htm', email=flask.g.session_body['email'], name=name, age=age, address=address, incomplete=not (name and age and address))

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

@APP.route('/edit', methods=['POST'])
@misc.require_session
def edit_field():
  body = flask.request.json
  assert body['field'] in ('name', 'age', 'address')
  val = int(body['val']) if body['field'] == 'age' else body['val']
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    cur.execute(f'update users set {body["field"]} = %s, modified = now() where userid = %s', (val, flask.g.session_body['userid']))
    dbcon.commit()
  if body['field'] == 'address':
    # todo: address API
    # todo: enqueue this instead of inline processing
    pass
  return flask.jsonify({'ok': True, 'body': body})
