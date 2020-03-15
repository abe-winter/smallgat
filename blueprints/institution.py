import flask
from ..util import misc, con

APP = flask.Blueprint('institution', __name__)

@APP.route('/new')
@misc.require_session
def get_new():
  return flask.render_template('new_inst.htm')

@APP.route('/new', methods=['POST'])
@misc.require_session
def post_new():
  form = flask.request.form
  print(form)
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    role = form['role'] or None
    email_domain = form['email_domain'] or None
    cur.execute('insert into institutions (name, url, email_domain, kind) values (%s, %s, %s, %s) returning instid', (form['name'], form['url'], email_domain, form['kind']))
    instid, = cur.fetchone()
    cur.execute('insert into inst_roles (instid, userid, role) values (%s, %s, %s)', (instid, flask.g.session_body['userid'], role))
    dbcon.commit()
  return flask.redirect(flask.url_for('institution.inst', instid=instid))

@APP.route('/inst/<uuid:instid>')
@misc.require_session
def inst(instid):
  raise NotImplementedError
