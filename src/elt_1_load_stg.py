import requests

from db import get_connection


POSTS_URL = "https://jsonplaceholder.typicode.com/posts"


def fetch_posts():
    response = requests.get(POSTS_URL, timeout=10)
    response.raise_for_status()

    posts = response.json()

    if not isinstance(posts, list):
        raise RuntimeError(f"unexpected response from {POSTS_URL}")

    return posts


def load_posts_to_stg(posts):
    rows = []

    for post in posts:
        rows.append(
            (
                post["id"],
                post["userId"],
                post["title"],
                post["body"],
            )
        )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("truncate table stg.posts;")

            cur.executemany(
                """
                insert into stg.posts (id, user_id, title, body)
                values (%s, %s, %s, %s);
                """, rows,
            )


def main():
    posts = fetch_posts()
    load_posts_to_stg(posts)
    print(f"loaded {len(posts)} posts to stg.posts")


if __name__ == "__main__":
    main()
