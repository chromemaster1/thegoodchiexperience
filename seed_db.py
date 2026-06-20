from Goodchiwebsite import app, db, Post

# ──────────────────────────────────────────────────────────────
# ALL 7 POSTS
# ──────────────────────────────────────────────────────────────
POSTS = [
    {
        'slug': 'welcoming-intro',
        'title': 'Welcoming Intro to the Portfolio',
        'excerpt': (
            'I have taken the time to create a beautiful server where my portfolio of works '
            'can live, and you can view and tag along — we might make some fun music or code '
            'something fun while on our adventure, who knows.'
        ),
        'content': '''\
<p>I have taken the time to create a beautiful server where my portfolio of works can live,
and you can view and tag along — we might make some fun music or code something fun while
on our adventure, who knows.</p>

<p>This portfolio represents years of dedication to both music and software development.
Every project showcased here tells a story of growth, learning, and passion.</p>

<p>Feel free to explore, reach out, and let\'s collaborate on something amazing!</p>''',
        'date': 'October 29, 2025',
        'image': 'images/play_15606020.png',
    },
    {
        'slug': 'journey-founder-creative',
        'title': 'My Journey: As Founder and Creative Entrepreneur',
        'excerpt': (
            'Since we registered the company in 2023 on my birthday, it\'s been a beautiful '
            'learning curve — several projects, milestones met, and some tough circumstances. '
            'But what is life without challenges?'
        ),
        'content': '''\
<p>Since we registered the company in 2023 on my birthday, it\'s been a beautiful learning
curve — several projects, milestones met, and some tough circumstances. But what is life
without challenges?</p>

<p>Building a company from scratch taught me resilience, adaptability, and the importance
of surrounding yourself with the right people. Every challenge became a learning
opportunity.</p>

<p>The journey has been transformative, and I\'m excited about what the future holds.</p>''',
        'date': 'April 28, 2023',
        'image': 'images/customer-journey_17247993.png',
    },
    {
        'slug': 'who-knew-release',
        'title': 'Who Knew — Release of Our First Studio Project as Goodchi',
        'excerpt': (
            'This was really the beginning of everything we have been doing — not only our '
            'first break into the creative industry, but a marking point of me no longer '
            'sitting on the sidelines with my craft and skillsets.'
        ),
        'content': '''\
<p><em>Who Knew</em> was more than a song — it was a testament to the fact that no matter
how long it takes, you can do it and accomplish that goal or dream.</p>

<p>This release marked a turning point. It wasn\'t just music; it was a declaration that I
was serious about my craft and ready to share it with the world.</p>

<p>The response from the community was overwhelming, and it fuelled my determination to
keep creating and pushing boundaries.</p>

<hr style="margin:30px 0;">

<h3>Listen &amp; Download</h3>
<p>Get the track now and add it to your collection:</p>
<a href="/download"
   style="display:inline-block;padding:12px 30px;background:#28a745;color:#fff;
          text-decoration:none;border-radius:5px;font-weight:bold;
          margin-right:15px;margin-bottom:20px;">&#8595; Download Track</a>

<h3 style="margin-top:30px;">Watch the Video</h3>
<p>Check out the official video:</p>
<div style="position:relative;width:100%;max-width:600px;margin:20px 0;">
  <iframe width="100%" height="400"
          src="https://www.youtube.com/embed/ayJSSqSU6BU"
          title="Who Knew - Official Video"
          frameborder="0"
          allow="accelerometer;autoplay;clipboard-write;encrypted-media;gyroscope;picture-in-picture"
          allowfullscreen
          style="border-radius:8px;"></iframe>
</div>''',
        'date': 'November 18, 2023',
        'image': 'images/Who knew art.jpeg',
    },
    {
        'slug': 'cookie-clicker-game',
        'title': 'Cookie Clicker Game — A Web-Based Game Experience',
        'excerpt': (
            'A web-based game I developed that lets users click cookies and earn cookie money '
            'to purchase upgrades and other fun stuff — a project built to test coding skills '
            'and have fun with it.'
        ),
        'content': '''\
<p>The Cookie Clicker game was initially developed as a personal testing project for my
private entertainment, but it can be fully developed and deployed for commercial or
personal use.</p>

<p>Building this game was a great exercise in logic, user experience, and interactive
design. It combines entertainment with clean code practices.</p>

<p>Whether you\'re a casual player or a developer interested in the mechanics, this project
is a fun and addictive way to pass time while acquiring so much in the "cookie world" — lol.</p>''',
        'date': 'February 12, 2024',
        'image': 'images/cookie_3245050.png',
    },
    {
        'slug': 'genesis-ep-project',
        'title': 'The Genesis EP Project — A Debut That Resonates',
        'excerpt': (
            'Dropped our first debut EP — Genesis — that has gone on massively, with hits like '
            '247pnb, Sticks n Bones, Say Your Mine and Girls Like You standing out as fan '
            'favourites.'
        ),
        'content': '''\
<p>The timing and making of this project was crucial — it came during a period of personal
challenges, but I refused to let that stand in the way of putting it out for the world.</p>

<p>Genesis became more than an EP; it became a statement. Each track represents a different
emotion, story, and moment in time.</p>

<p>Tracks like <strong>247pnb</strong> and <strong>Sticks n Bones</strong> resonated deeply
with listeners, and the appreciation continues to this day.</p>''',
        'date': 'April 18, 2024',
        'image': 'images/genesis-art.jpeg',
    },
    {
        'slug': 'infodorm-news-data',
        'title': 'Infodorm — News and Data Retrieval Platform',
        'excerpt': (
            'A news and data retrieval site I created that shares insight on current events '
            'and lets users pull information around any topic — best suited for researchers '
            'and creators.'
        ),
        'content': '''\
<p>I was going for a regular media site, but I realised that researchers and creators spend
a ton of time searching the web just to update themselves or work on a project. I could
save them time by building something that pulls data from the web around a topic, event, or
date and retrieves all corresponding materials — while still keeping users current with
real-time events.</p>

<p>Infodorm bridges the gap between curiosity and information. It\'s designed for those who
need reliable, organised data without the noise.</p>

<p>Whether you\'re researching for a project or staying updated on current events, Infodorm
delivers relevant information efficiently.</p>''',
        'date': 'April 25, 2024',
        'image': 'images/infodorm-logo1.jpeg',
    },
    {
        'slug': 'stranger-things-single',
        'title': 'Stranger Things Dey Happen — 2nd Single of 2025',
        'excerpt': 'Dropped my 2nd highly anticipated single of the year 2025.',
        'content': '''\
<p>The target for the year was to give my fans raw, uncategorised music — 6 different
singles — and see how they respond to each one.</p>

<p>This single showcases a different side of my artistry while maintaining the essence of
what makes Goodchi recognisable.</p>

<p>Stranger things are indeed happening, and I\'m grateful to share this journey with you
all.</p>''',
        'date': 'May 11, 2025',
        'image': 'images/pic07.jpg',
    },
]


# ──────────────────────────────────────────────────────────────
# SAFE SEED FUNCTION — idempotent, never drops anything
# ──────────────────────────────────────────────────────────────
def seed_posts(verbose=True):
    """
    Insert posts whose slug is not already in the DB.
    Safe to call on every app startup.
    Returns the number of posts actually inserted.
    """
    existing_slugs = {row.slug for row in Post.query.with_entities(Post.slug).all()}
    inserted = 0

    for data in POSTS:
        if data['slug'] in existing_slugs:
            if verbose:
                print(f"  · skip  {data['slug']}  (already exists)")
            continue
        db.session.add(Post(**data))
        inserted += 1
        if verbose:
            print(f"  + added {data['slug']}")

    if inserted:
        db.session.commit()

    if verbose:
        total = len(existing_slugs) + inserted
        print(f"\n✓ Done — {inserted} inserted, {len(existing_slugs)} already present "
              f"({total} total posts)")
    return inserted


def seed_database(verbose=True):
    """Full entry point: create tables + seed posts."""
    with app.app_context():
        db.create_all()   # safe — only creates tables that don't exist yet
        if verbose:
            print("── Goodchi seed ──────────────────────────")
        seed_posts(verbose=verbose)


# ──────────────────────────────────────────────────────────────
# Run manually:  python seed_db.py
# ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    seed_database(verbose=True)
