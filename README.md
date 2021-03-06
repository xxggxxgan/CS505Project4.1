# project 4.1

project description:

Instagram data curation. Scrape all the Instagram posts/captions (hashtags and associated comments) from two Instagram sites:
Swisher Sweets(https://www.instagram.com/swishersweets/) and Backwoods(https://www.instagram.com/backwoods_cigars/) from 2018, 2019, and 2020.

Annotate the posts/captions with:
```
1.whether/not they contain tobacco use warnings,
2.explicit sponsorship hashtags (#sponsored, #ad, or #paid)
3. ambiguous sponsorship hashtags (#thanks, #sp, #spon, #ambassador, #collab).
```

hints:
For tobacco warning, you can find examples of tobacco warning in other text (maybe from government anti-tobacco advertisements etc.), and then you can use sentence embedding such as Labse (https://github.com/bojone/labse) to find if two texts are similar or not (either using cosine similarity) or train a tobacco warning detection model (with positive examples being tobacco warning texts and negative examples being other texts) based on text features (vectors) obtained from Labse / BERT etc.

Scraped data are all undered the downloaded_files directories including posts/comments and photos

The annotated comments are in comment_final_v0.csv; the annotated posts are in posts_final_v0.csv

warning.txt are the sample tobacco use warnings we found online, which are used to compare with comments/posts/captions in order to determine their similarities

ins_download.py is used for scraping data

annotate.py is used for annotate explicit/ambiguous hashtags in the posts/captions/comments

bert_annotate.py is used for annotate tobacco use warning in the posts/captions/comments
