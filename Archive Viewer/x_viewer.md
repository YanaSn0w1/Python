# [PayPal-Donations](https://www.paypal.com/donate/?hosted_button_id=9LWWH273HEVC4 "Donate to YanaHeat") ⬅️

# 🔍 [X Archive Viewer](https://github.com/YanaSn0w1/Python/blob/main/Archive%20Viewer/x_viewer.py "X Archive Viewer") ⬅️

A compact Streamlit app that loads your **Twitter/X archive ZIP**, classifies every post, and lets you **filter, search, sort, and export** everything fast.

## ✨ Features
- Auto‑detect archive in **Downloads**
- Classifies: **Posts, Replies, Quotes, Retweets**
- Filters: type, links‑only, search, date range
- Sorting: newest/oldest
- Exports: **CSV, JSON, TXT, HTML**
- Copy up to 1000 URLs to clipboard
- Clean, wide Streamlit UI

## 🚀 Install
```bash
pip install streamlit pandas
```

## 

## 📁 How to Use
1. Download your X archive to your Downloads folder (`twitter-*.zip`)
2. In powershell Run
```bash
streamlit run x_viewer.py
```
3. Apply filters in the sidebar
4. Export or copy URLs
5. Load the JSON with [X Bulk Deleter](https://github.com/YanaSn0w1/Tampermonkey#x-bulk-deleter-%EF%B8%8F "X Bulk Deleter") ⬅️

## 🧠 How It Works
- Loads all `data/tweets/*.js` files
- Strips the JS wrapper (`window.YTD... =`)
- Builds a DataFrame with:
  - Date  
  - Text  
  - Type (Post/Reply/Quote/Retweet)  
  - Link presence  
  - Direct URL to the post  
- Filters + sorting update instantly

## 📤 Export Formats
- **CSV** — full dataset  
- **JSON** — structured records  
- **TXT** — simple list  
- **HTML** — clickable links

  <img width="1600" height="900" alt="firefox_hXeYcu4gk0" src="https://github.com/user-attachments/assets/17ff8f9a-56eb-48ee-b31b-f9a4fa96cb08" />

## 📄 License
MIT
