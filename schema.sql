create extension if not exists "uuid-ossp";

create table users (
  userid uuid primary key default uuid_generate_v4(),
  email text not null unique,
  name text,
  age int,
  address text,
  -- todo: cache geocoded address
  created timestamp not null default now(),
  modified timestamp not null default now()
);

create table deleted_users (
  -- todo: unique index across both tables
  userid uuid primary key,
  email text,
  deleted timestamp not null default now(),
  orig_created timestamp,
  orig_modified timestamp
);

create table institutions (
  instid uuid primary key default uuid_generate_v4(),
  name text,
  url text,
  banner_message text,
  email_domain text, -- optional
  kind text, -- optional -- school work etc
  group_size int default 5,
  require_approval boolean default false,
  created timestamp not null default now(),
  modified timestamp not null default now()
);

-- for controlling institutions
create table inst_roles (
  instid uuid,
  userid uuid,
  role text, -- in (owner, admin)
  primary key (instid, userid, role),
  created timestamp not null default now(),
  modified timestamp not null default now()
);

-- for users in institutions
create table memberships (
  instid uuid,
  userid uuid,
  primary key (instid, userid),
  role text, -- 'what do you do there', only used for display
  approved boolean, -- based on institution.require_approval
  created timestamp not null default now(),
  modified timestamp not null default now()
);

create table bans (
  instid uuid,
  userid uuid,
  primary key (instid, userid),
  banned_by_user uuid not null,
  reason text,
  created timestamp not null default now(),
  modified timestamp not null default now()
);

create table groups (
  groupid uuid primary key default uuid_generate_v4(),
  instid uuid not null,
  created timestamp not null default now(),
  modified timestamp not null default now(),
  deleted timestamp not null default now()
);

create table group_members (
  groupid uuid,
  userid uuid,
  primary key (groupid, userid),
  created timestamp not null default now(),
  modified timestamp not null default now()
);
