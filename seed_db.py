from Goodchiwebsite import app, db, Post

posts_data = [
    {
        'slug': 'welcoming-intro',
        'title': 'welcoming intro TO the portforlio',
        'excerpt': 'i have taken the time to create a beautiful server where my portfolio of works can live, and you can view, and tag along, we might make some fun music or code something fun while on our adventure who knows.',
        'content': '''<p>i have taken the time to create a beautiful server where my portfolio of works can live, and you can view, and tag along, we might make some fun music or code something fun while on our adventure who knows.</p>
        <p>This portfolio represents years of dedication to both music and software development. Every project showcased here tells a story of growth, learning, and passion.</p>
        <p>Feel free to explore, reach out, and let's collaborate on something amazing!</p>''',
        'date': 'October 29, 2025',
        'image': 'images/play_15606020.png'
    },
    {
        'slug': 'journey-founder-creative',
        'title': 'My journey: As founder and creative entreprenuer so far has been nothing short of fun, experimentation and pure adventures',
        'excerpt': 'since we registered the company in 2023 on my birthday, its been a beautiful learn curve process with several projects and milestones met and some circumstances but what is life without challenges.',
        'content': '''<p>since we registered the company in 2023 on my birthday, its been a beautiful learn curve process with several projects and milestones met and some circumstances but what is life without challenges.</p>
        <p>Building a company from scratch taught me resilience, adaptability, and the importance of surrounding yourself with the right people. Every challenge became a learning opportunity.</p>
        <p>The journey has been transformative, and I'm excited about what the future holds.</p>''',
        'date': 'April 28, 2023',
        'image': 'images/customer-journey_17247993.png'
    },
    {
        'slug': 'who-knew-release',
        'title': 'Who knew - Release of our first studio project as Goodchi',
        'excerpt': 'this for me was really the beginning to everything and anything we have been doing, because its nothing only our first break in into the creative industry but a marking point of me no longer sitting on the side lines wit my craft and skillsets',
        'content': '''<p>Who knew, was more than a song but a testimnet to the afct that no matter how long it takes you can do it to and accomplish that goal or dream.</p>
        <p>This release marked a turning point. It wasn't just music; it was a declaration that I was serious about my craft and ready to share it with the world.</p>
        <p>The response from the community was overwhelming, and it fueled my determination to keep creating and pushing boundaries.</p>

        <hr style="margin: 30px 0;">

        <h3>Listen & Download</h3>
        <p>Get the track now and add it to your collection:</p>
        <a href="/download" style="display: inline-block; padding: 12px 30px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; margin-right: 15px; margin-bottom: 20px;">📥 Download Track</a>

        <h3 style="margin-top: 30px;">Watch the Video</h3>
        <p>Check out the official video:</p>
        <div style="position: relative; width: 100%; max-width: 600px; margin: 20px 0;">
            <iframe width="100%" height="400" src="https://www.youtube.com/embed/ayJSSqSU6BU" title="Who Knew - Official Video" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="border-radius: 8px;"></iframe>
        </div>''',
        'date': 'November 18, 2023',
        'image': 'images/Who knew art.jpeg'
    },
    {
        'slug': 'cookie-clicker-game',
        'title': 'Cookie clicker game - a web based game experience',
        'excerpt': 'this is a web based game i developed that lets users click cookies and earn cookie money which can be used to purchase upgrades and other fun stuff, its a fun project that i built to test out some of my coding skills and also to have fun with it.',
        'content': '''<p>The cookie clicker game was initial developed as a personal testing project for my private entertainment but can be fully developed and deployed for commercial users or personal use.</p>
        <p>Building this game was a great exercise in logic, user experience, and interactive design. It combines entertainment with clean code practices.</p>
        <p>Whether you're a casual player or a developer interested in the mechanics, this project is a fun and addictive way to pass time while still acquiring so much in the cookie world' lol .</p>''',
        'date': 'February 12, 2024',
        'image': 'images/cookie_3245050.png'
    },
    {
        'slug': 'genesis-ep-project',
        'title': 'The Genesis Ep project - A debut that resonates',
        'excerpt': 'dropped our first debut Ep project Genesis, that has gone on to do Massively, With hits like 247pnb, Sticks n bones, say your mine and girls like you, standing out as fan favorites',
        'content': '''<p>The timing of this project and making was a crucial one for me as it was at a point where i was going thru some personal challenges on my own but refused to let that get in the way of the project and having it put out for the users.</p>
        <p>Genesis became more than an EP; it became a statement. Each track represents a different emotion, story, and moment in time.</p>
        <p>Tracks like 247pnb and Sticks n bones resonated deeply with listeners, and the appreciation continues to this day.</p>''',
        'date': 'April 18, 2024',
        'image': 'images/genesis-art.jpeg'
    },
    {
        'slug': 'infodorm-news-data',
        'title': 'Infodorm - News and data retrieval platform',
        'excerpt': 'This a news, and data retrival site i created, that shares insight on happening events and lets users retrieve information from the data point of any information, best suited for researchers and creators',
        'content': '''<p>i was going for a regular media site but i realised that researchers and creators spend ton of time trying to serach the web searching for information sometimes just to update themselve or for project, and i could save them time by providing something that lets you pull up data from the web entered around a topic, event or date and will retrieve all corresponding available materials to the users search, while still enjoying real time insight into current events.</p>
        <p>Infodorm bridges the gap between curiosity and information. It's designed for those who need reliable, organized data without the noise.</p>
        <p>Whether you're researching for a project or staying updated on current events, Infodorm delivers relevant information efficiently.</p>''',
        'date': 'April 25, 2024',
        'image': 'images/infodorm-logo1.jpeg'
    },
    {
        'slug': 'stranger-things-single',
        'title': 'Stranger things dey happen - 2nd single of 2025',
        'excerpt': 'Dropped my 2nd highly anticipated single of the year 2025',
        'content': '''<p>the target for the year was to give my fans, a raw and uncategoried music 6 different singles, from what they already know about me and see how they love each one.</p>
        <p>This single showcases a different side of my artistry while maintaining the essence of what makes Goodchi recognizable.</p>
        <p>Stranger things are indeed happening, and I'm grateful to share this journey with you all.</p>''',
        'date': 'May 11, 2025',
        'image': 'images/pic07.jpg'
    }
]

def seed_database():
    with app.app_context():
        db.drop_all()
        db.create_all()

        for post_data in posts_data:
            post = Post(**post_data)
            db.session.add(post)

        db.session.commit()
        print(f"✓ Database seeded with {len(posts_data)} posts")

if __name__ == '__main__':
    seed_database()
