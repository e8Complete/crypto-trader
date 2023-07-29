To get a Reddit API key, you need to create an app on the Reddit Developer Console. Here are the steps:

Go to the Reddit Developer Console website at https://www.reddit.com/prefs/apps.
Click the "Create App" button.
Choose "Script" as the type of app you want to create.
Give your app a name and description.
In the "about url" field, you can put your own website if you have one, or you can put any valid URL.
In the "redirect uri" field, put "http://localhost:8000" (this is a default value that will work for most Python scripts).
Click the "Create App" button at the bottom of the page.
You should now see your app's details, including the client ID and client secret. These are the credentials you will need to access the Reddit API.
Note that you will also need to authenticate your Reddit account by providing your Reddit username and password, or by using OAuth2.0 if you want to access more advanced features. Once you have your client ID and client secret, you can use them to authenticate your Python script and start accessing Reddit data.


https://praw.readthedocs.io/en/stable/code_overview/models/subreddit.html