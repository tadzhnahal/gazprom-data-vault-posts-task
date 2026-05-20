import hashlib

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

def show_sample_keys(posts):
    post_id, user_id, title, body, source_system = posts[0]

    user_hash_key = make_hash_key("user", user_id)
    post_hash_key = make_hash_key("post", post_id)
    user_post_hash_key = make_hash_key("user_post", user_id, post_id)

    print(f"read {len(posts)} rows from stg.posts")
    print(f"sample row: user_id={user_id}, post_id={post_id}")
    print(f"user_hash_key length: {len(user_hash_key)}")
    print(f"post_hash_key length: {len(post_hash_key)}")
    print(f"user_post_hash_key length: {len(user_post_hash_key)}")


def main():
    posts = get_stg_posts()

    if not posts:
        raise RuntimeError("stg.posts is empty")

    show_sample_keys(posts)


if __name__ == "__main__":
    main()
