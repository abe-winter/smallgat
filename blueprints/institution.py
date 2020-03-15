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
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    cur.execute('select name, url, email_domain, kind, group_size from institutions where instid = %s', (str(instid),))
    row = cur.fetchone()
    if row is None:
      raise NotImplementedError # todo: 404
    name, url, email_domain, kind, group_size = row
    inst_user = (str(instid), flask.g.session_body['userid'])
    cur.execute('select role from memberships where instid = %s and userid = %s', inst_user)
    member_row = cur.fetchone()
    inst_row = None
    group_row = None
    if member_row: # i.e. assume that owners don't have or need memberships
      cur.execute('select groups.groupid from groups join group_members using (groupid) where instid = %s and userid = %s', inst_user)
      group_row = cur.fetchone()
    else: # i.e. assume that owners don't have or need memberships
      cur.execute('select role from inst_roles where instid = %s and userid = %s', inst_user)
      inst_row = cur.fetchone()
  return flask.render_template('inst.htm', instid=instid, name=name, url=url, email_domain=email_domain, kind=kind, group_size=group_size, member_row=member_row, inst_row=inst_row, group_row=group_row)

@APP.route('/join/<uuid:instid>', methods=['POST'])
@misc.require_session
def join(instid):
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    cur.execute('select email_domain, require_approval from institutions where instid = %s', (str(instid),))
    email_domain, require_approval = cur.fetchone()
    if email_domain:
      raise NotImplementedError('todo: email domain restriction')
    cur.execute(
      'insert into memberships (instid, userid, role, approved) values (%s, %s, %s, %s)',
      (str(instid), flask.g.session_body['userid'], flask.request.form['role'], not require_approval)
    )
    dbcon.commit()
  return flask.redirect(flask.url_for('institution.inst', instid=instid))
