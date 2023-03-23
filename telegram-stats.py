# https://medium.com/mcd-unison/telegram-group-chat-analysis-5b49446c2ec9

import re
from collections import Counter
import emoji
import numpy
import pandas as pd
from matplotlib import pyplot
from wordcloud import WordCloud, STOPWORDS

df = pd.read_json('./result.json', dtype={'from_id': str})
df = df[df.from_id != 'nan'] # This is a telegram service, likely updates

# Grab all unique Id's, and re-write the names.
from_ids = df['from_id'].unique()
for from_id in from_ids:
    df.loc[df.from_id == from_id, 'from'] = df['from']

# Plot Stickers sent / Messages sent
df[['type','from']].groupby(['from']).count().sort_values(['type'], ascending=False)
df[['media_type', 'id']].groupby('media_type', as_index=False).count()
df[['type', 'id']].groupby('type', as_index=False).count()

sticker_df = df.loc[df['media_type'] == 'sticker'][['from', 'id']]\
    .groupby(['from'], as_index=False)\
    .agg('count')\
    .sort_values(['id'], ascending=False)

messages_df = df.loc[df['type'] == 'message'][['from', 'id']]\
    .groupby(['from'], as_index=False)\
    .agg('count')\
    .sort_values(['id'], ascending=False)

import plotly.express as px
fig = px.pie(sticker_df, hole=.5, values=sticker_df['id'], names=sticker_df['from'],
             title='Stickers sent')
fig.update_traces(textposition='inside', textinfo='value+label+percent')
fig.show()

import plotly.express as px
fig = px.pie(messages_df, hole=.5, values=messages_df['id'], names=messages_df['from'],
             title='Messages sent')
fig.update_traces(textposition='inside', textinfo='value+label+percent')
fig.show()

# how emojis and words are distributed and counted
def get_emojis_in_message(row):
    message = row.text
    emojis = ""
    # Telegram may save some messages as json
    if message is None or type(message) != str:
        return None
    return emojis.join(char for char in message if emoji.is_emoji(char))

def get_words_count(row):
    message = row.text
    # Telegram may save some messages as json
    if message is None or type(message) != str:
        return None
    return re.sub("[^\w]", " ",  message).split().__len__()

df["emojis"] = df[["text"]].apply(get_emojis_in_message, axis=1)
df["word_count"] = df[["text"]].apply(get_words_count, axis=1)

people = df['from'].unique()

for name in people:
    user_df = df[df["from"] == name]
    words_per_message = numpy.sum(user_df['word_count'])
    print('stats for ', name)
    print(name, ' sent ', int(words_per_message), ' words, average ', words_per_message/user_df.shape[0], ' per message')

# how the emoji distribution is looking
total_emojis_list = list(df.emojis)
emoji_dict = dict(Counter(total_emojis_list))
emoji_dict = sorted(emoji_dict.items(), key=lambda x: x[1], reverse=True)

emoji_df = pd.DataFrame(emoji_dict, columns=['emoji', 'count'])
emoji_df.replace(to_replace='None', value=numpy.nan).dropna()
emoji_df.replace(to_replace=0, value=numpy.nan).dropna()

import plotly.express as px
fig = px.pie(emoji_df.loc[2:].head(60), hole=.5, values='count', names='emoji',
             title='Emoji Distribution')
fig.update_traces(textposition='inside', textinfo='percent+label')
fig.show()

# word cloud
text_df = df.text.dropna()
text = " ".join(review for review in df.text.dropna() if review is not None and type(review) == str)
print ("There are {} words in all the messages.".format(len(text)))

stopwords = set(STOPWORDS)
stopwords.update(["pero", "en", "que", "lo", "de", "si", "con","se","tengo","por", "la", "el", "ya", "los", "es", "tiene", "como","mi","te","un","esta","del", "tu", "Yo","eso", "pue","para","las","porque","al","bueno","al","donde","ese","son","una","ese","sí","son","le","está","estaba","dice","creo"])
# Generate a word cloud image
wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(text)
# Display the generated image:
pyplot.figure( figsize=(10,5))
pyplot.imshow(wordcloud, interpolation='bilinear')
pyplot.axis("off")
pyplot.show()

# number of words shared as time moves on.
df["datetime"] = pd.to_datetime(df['date'])
df.index = df['datetime']
date_df = df.resample("D").sum()
date_df.reset_index(inplace=True)
fig = px.line(date_df, x="datetime", y="word_count", title='Number of words shared as time moves on.')
fig.update_xaxes(nticks=30)
fig.show()

# how active we were each day of the week
def dayofweek(i):
  l = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
  return l[i];
day_df=pd.DataFrame(df["word_count"])
day_df['day_of_date'] = df['datetime'].dt.weekday
day_df['day_of_date'] = day_df["day_of_date"].apply(dayofweek)
day_df["messagecount"] = 1
day = day_df.groupby("day_of_date").sum()
day.reset_index(inplace=True)

fig = px.line_polar(day, r='messagecount', theta='day_of_date', line_close=True)
fig.update_traces(fill='toself')
fig.update_layout(
  polar=dict(
    radialaxis=dict(
      visible=True
    )),
  showlegend=False
)
fig.show()
