# Instagram Token Renewal

Your Instagram access token expires every 60 days. When it does, posts will fail.

**Next renewal due:** around late May 2026

## Steps to renew
1. Go to developers.facebook.com → your app → Tools → Graph API Explorer
2. Select your app → Generate Access Token
3. Check: instagram_basic, instagram_content_publish, pages_read_engagement, pages_show_list
4. Copy the short token

5. Open this URL in browser (your App ID is 866371822870634):
```
https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=866371822870634&client_secret=0efbf1ecdc04383daa111cfd9e615fdb&fb_exchange_token=PASTE_SHORT_TOKEN_HERE
```

6. Copy the long `access_token` from the result

7. Go to github.com/VVOAYAD/instagram-vault → Settings → Secrets → Actions
8. Click INSTAGRAM_ACCESS_TOKEN → Update → paste new token → Save
