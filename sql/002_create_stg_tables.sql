create table if not exists stg.posts (
	id integer not null,
	user_id integer not null,
	title text not null,
	body text not null,
	source_system text not null default 'jsonplaceholder_posts',
	loaded_at timestamptz not null default now(),
	primary key (id)
);
