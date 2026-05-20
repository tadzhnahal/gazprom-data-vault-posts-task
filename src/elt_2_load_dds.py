import hashlib
from datetime import datetime, timezone

from db import get_connection

def make_hash_key(*values):
    value = "||".join(str(item) for item in values)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def get_stg_posts():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select id, user_id, title, body, source_system
                from stg.posts
                order by id;
                """
            )

            return cur.fetchall()


def load_hubs(cur, posts, load_date):
    user_rows = {}
    post_rows = []

    for post_id, user_id, title, body, source_system in posts:
        user_hash_key = make_hash_key("user", user_id)
        post_hash_key = make_hash_key("post", post_id)

        user_rows[user_hash_key] = (user_hash_key, user_id, load_date, source_system)
        post_rows.append((post_hash_key, post_id, load_date, source_system))

    cur.executemany(
        """
        insert into dds.h_user (user_hash_key, user_id, load_date, record_source)
        values (%s, %s, %s, %s)
        on conflict (user_hash_key) do nothing;
        """, list(user_rows.values())
    )

    cur.executemany(
        """
        insert into dds.h_post (post_hash_key, post_id, load_date, record_source)
        values (%s, %s, %s, %s)
        on conflict (post_hash_key) do nothing;
        """, post_rows,
    )


def load_posts_to_dds(posts):
    load_date = datetime.now(timezone.utc)

    with get_connection() as conn:
        with conn.cursor() as cur:
            load_hubs(cur, posts, load_date)


def main():
    posts = get_stg_posts()

    if not posts:
        raise RuntimeError("stg.posts is empty")

    load_posts_to_dds(posts)
    print(f"processed {len(posts)} stg rows into dds hubs")


if __name__ == "__main__":
    main()
