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

create table institutions (
  instid uuid primary key default uuid_generate_v4(),
  email_domain text, -- optional
  created timestamp not null default now(),
  modified timestamp not null default now()
);

-- for controlling institutions
create table roles (
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
