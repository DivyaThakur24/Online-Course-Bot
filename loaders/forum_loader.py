from requests import session
import json
import config
from bs4 import BeautifulSoup
import MySQLdb
import re
from datetime import datetime


emoji_pattern = re.compile(config.EMOTICONS, flags=re.UNICODE)

payload = {
    'email': config.EMAIL,
    'password': config.PASSWORD
}

db = MySQLdb.connect(
    host=config.HOST,
    user=config.USER,
    db=config.DATABASE
)

cursor = db.cursor()

cursor.execute('SELECT post_id FROM {};'.format(
    config.FORUM_TABLE
))
pids = [int(pid[0]) for pid in cursor.fetchall()]

new_ids = []

f = open("logs/ud/udfailure{}.txt".format(datetime.now().strftime('%Y%m%d%H%M%S')), 'w')

with session() as c:

    url = config.UDACITY_SIGNIN_URL
    c.post(url, data=json.dumps(payload))

    cnt = 0
    count = 0

    for j in config.UDACITY_FORUM_TABS:
        for i in range(500):

            print("\n PAGE - {} \t ({})\n".format(i + 1, j))

            response = c.get(config.UD_FORUM_URL.format(j, i))

            s = BeautifulSoup(response.text, 'html.parser')

            divs = s.find_all('div', {"itemprop": 'itemListElement'})
            if not divs:
                break

            for div in divs:
                link = div.find('a').get('href')
                topic = emoji_pattern.sub(r'', div.find('span').text).strip()
                post_id = link.split('/')[-1]

                if (int(post_id) in pids) or (int(post_id) in new_ids):
                    print("Repeated {} from {}.".format(link, j))
                    continue

                query = """INSERT INTO {}(post_id, topic, link) VALUES ({}, "{}", "{}");""".format(
                    config.FORUM_TABLE,
                    post_id,
                    topic.replace('\"', '\''),
                    link.replace('\"', '\''),
                )
                print(query)

                try:
                    cursor.execute(query)
                    cnt += 1
                    new_ids.append(int(post_id))
                    print("Added {} posts to db. Discarded {} till now.".format(cnt, count))
                except:
                    count += 1
                    print("\nUnable to add post {} to db.\n".format(link))
                    f.write(link)
                finally:
                    db.commit()

cursor.execute('SELECT * FROM {};'.format(config.FORUM_TABLE))
print(cursor.rowcount)

db.commit()
f.close()
db.close()
