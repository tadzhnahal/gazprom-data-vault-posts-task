from db import get_connection


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


def main():
    posts = get_stg_posts()

    if not posts:
        raise RuntimeError("stg.posts is empty")

    print(f"read {len(posts)} rows from stg.posts")


if __name__ == "__main__":
    main()
