import flask
from ..util import misc, con, rates

APP = flask.Blueprint('institution', __name__)

MAX_INST = 5

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
    # todo: check complete user
    cur.execute('select count(*) from institutions join inst_roles using (instid) where userid = %s', (flask.g.session_body['userid'],))
    count, = cur.fetchone()
    if count >= MAX_INST:
      return f"Error: you have {MAX_INST} institutions already, delete some before making new ones"
    role = form['role'] or None
    email_domain = form['email_domain'] or None
    cur.execute('insert into institutions (name, url, email_domain, kind) values (%s, %s, %s, %s) returning instid', (form['name'], form['url'], email_domain, form['kind']))
    instid, = cur.fetchone()
    cur.execute('insert into inst_roles (instid, userid, role) values (%s, %s, %s)', (instid, flask.g.session_body['userid'], role))
    dbcon.commit()
  return flask.redirect(flask.url_for('institution.inst', instid=instid))

RATE_INST_IP = rates.MemRateLimiter(200, 60)

@APP.route('/inst/<uuid:instid>')
@misc.require_session
def inst(instid):
  misc.abort_rate('Per-IP accesses exceeded', RATE_INST_IP, misc.external_ip())
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    cur.execute('select name, url, email_domain, kind, group_size from institutions where instid = %s', (str(instid),))
    row = cur.fetchone()
    if row is None:
      flask.abort(404)
    name, url, email_domain, kind, group_size = row
    cur.execute('select name, email, role from inst_roles join users using (userid) where instid = %s', (str(instid),))
    managers = cur.fetchall()
    inst_user = (str(instid), flask.g.session_body['userid'])
    cur.execute('select role from memberships where instid = %s and userid = %s', inst_user)
    member_row = cur.fetchone()
    inst_row = None
    group_row = None
    if member_row: # i.e. assume that owners don't have or need memberships
      cur.execute('select groups.groupid from groups join group_members using (groupid) where instid = %s and userid = %s', inst_user)
      group_row = cur.fetchone()
    else: # i.e. assume that owners don't have or need memberships
      # todo: fold this into the inst_roles query above
      cur.execute('select role from inst_roles where instid = %s and userid = %s', inst_user)
      inst_row = cur.fetchone()
  return flask.render_template('inst.htm', instid=instid, name=name, url=url, email_domain=email_domain, kind=kind, group_size=group_size, member_row=member_row, inst_row=inst_row, group_row=group_row, managers=managers)

@APP.route('/join/<uuid:instid>', methods=['POST'])
@misc.require_session
def join(instid):
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    # todo: check complete user
    cur.execute('select email_domain, require_approval from institutions where instid = %s', (str(instid),))
    email_domain, require_approval = cur.fetchone()
    if email_domain and not flask.g.session_body['email'].endswith('@' + email_domain):
      return f'Error: you need an email in {email_domain} to join'
    cur.execute(
      'insert into memberships (instid, userid, role, approved) values (%s, %s, %s, %s)',
      (str(instid), flask.g.session_body['userid'], flask.request.form['role'], not require_approval)
    )
    dbcon.commit()
  return flask.redirect(flask.url_for('institution.inst', instid=instid))

@APP.route('/leave/<uuid:instid>', methods=['POST'])
@misc.require_session
def leave(instid):
  raise NotImplementedError

@APP.route('/flag/<uuid:userid>', methods=['POST'])
@misc.require_session
def flag(userid):
  "mark this user as bad"
  # not doing this for now -- admins can take care of this
  raise NotImplementedError
