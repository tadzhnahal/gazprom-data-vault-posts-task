create table if not exists dds.h_user (
	user_hash_key varchar(64) primary key,
	user_id integer not null,
	load_date timestamptz not null,
	record_source text not null,
	unique (user_id)
);

create table if not exists dds.h_post (
	post_hash_key varchar(64) primary key,
	post_id integer not null,
	load_date timestamptz not null,
	record_source text not null,
	unique (post_id)
);

create table if not exists dds.l_user_post (
	user_post_hash_key varchar(64) primary key,
	user_hash_key varchar(64) not null references dds.h_user(user_hash_key),
	post_hash_key varchar(64) not null references dds.h_post(post_hash_key),
	load_date timestamptz not null,
	record_source text not null,
	unique (user_hash_key, post_hash_key)
);

create table if not exists dds.s_post_details (
	post_hash_key varchar(64) not null references dds.h_post(post_hash_key),
	load_date timestamptz not null,
	title text not null,
	body text not null,
	hash_diff varchar(64) not null,
	record_source text not null,
	primary key (post_hash_key, load_date)
);
