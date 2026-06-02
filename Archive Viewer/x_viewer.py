import streamlit as st
import pandas as pd
import json
import os
import re
import zipfile
import io
from pathlib import Path

st.set_page_config(page_title="My X Archive Viewer", layout="wide")
st.title("🔍 My X Archive Viewer")

# ====================== ZIP LOADING ======================
st.text_input("Path to zip file (or type 'Downloads')", value="Downloads", key="zip_path_input")
zip_input = st.session_state.zip_path_input

if zip_input.lower() == "downloads":
    downloads_folder = Path.home() / "Downloads"
    zip_files = list(downloads_folder.glob("twitter-*.zip")) + list(downloads_folder.glob("archive*.zip"))
    if zip_files:
        zip_path = str(max(zip_files, key=lambda f: f.stat().st_mtime))
        st.info(f"✅ Found archive: {Path(zip_path).name}")
    else:
        st.error("No Twitter archive zip found in Downloads folder.")
        st.stop()
else:
    if zip_input and not zip_input.endswith(".zip"):
        possible = list(Path(zip_input).glob("twitter-*.zip")) + list(Path(zip_input).glob("*.zip"))
        zip_path = str(possible[0]) if possible else zip_input
    else:
        zip_path = zip_input

if not os.path.exists(zip_path) or os.path.isdir(zip_path):
    st.error("Please select a valid .zip file.")
    st.stop()

@st.cache_data(show_spinner=False)
def load_tweets_from_zip(zip_path):
    tweets = []
    with zipfile.ZipFile(zip_path, 'r') as z:
        for f in sorted([f for f in z.namelist() if 'data/tweets' in f and f.endswith('.js')]):
            with z.open(f) as file:
                content = file.read().decode('utf-8')
            content = re.sub(r"^window\.YTD\.tweets\.part\d+\s*=\s*", "", content).rstrip(";\n").strip()
            try:
                data = json.loads(content)
                tweets.extend([item.get("tweet", {}) for item in data])
            except:
                pass
    return tweets

tweets = load_tweets_from_zip(zip_path)
st.success(f"Loaded {len(tweets):,} posts")

# ====================== PROCESS DATA ======================
records = []
for t in tweets:
    entities = t.get("entities", {})
    urls = entities.get("urls", [])
    text = t.get("full_text", "")
    
    quoted_id = t.get("quoted_status_id_str")
    quoted_permalink = t.get("quoted_status_permalink", {})
    if isinstance(quoted_permalink, dict):
        quoted_permalink = quoted_permalink.get("url", "")
    has_status_url = any("/status/" in (u.get("expanded_url") or "") for u in urls)
    
    is_quote = bool(quoted_id or quoted_permalink or has_status_url)
    is_retweet = bool(t.get("retweeted_status")) or bool(t.get("retweeted_status_id_str")) or text.startswith("RT @")
    is_reply = bool(t.get("in_reply_to_status_id_str"))
    has_any_link = len(urls) > 0 and not is_quote and not is_retweet

    records.append({
        "date": t.get("created_at", ""),
        "text": text,
        "is_reply": is_reply,
        "is_quote": is_quote,
        "is_retweet": is_retweet,
        "has_any_link": has_any_link,
        "url": f"https://x.com/i/status/{t.get('id_str', '')}"
    })

df = pd.DataFrame(records)
df["date"] = pd.to_datetime(df["date"], format="%a %b %d %H:%M:%S %z %Y", errors="coerce")

# ====================== FILTERS ======================
st.sidebar.header("Filters")

show_original = st.sidebar.checkbox("Show Original Posts", value=True)
show_replies = st.sidebar.checkbox("Show Replies", value=True)
show_quotes = st.sidebar.checkbox("Show Quote Tweets", value=True)
show_retweets = st.sidebar.checkbox("Show Retweets", value=False)
only_links = st.sidebar.checkbox("Only posts with links 🔗", value=False)
search = st.sidebar.text_input("Search text (optional)")

if not df.empty:
    min_d, max_d = df["date"].min().date(), df["date"].max().date()
    date_range = st.sidebar.date_input("Date range", (min_d, max_d))
else:
    date_range = []

filtered = df.copy()

mask = pd.Series([False] * len(filtered))
if show_original:
    mask |= (~filtered["is_reply"] & ~filtered["is_quote"] & ~filtered["is_retweet"])
if show_replies:
    mask |= filtered["is_reply"]
if show_quotes:
    mask |= filtered["is_quote"]
if show_retweets:
    mask |= filtered["is_retweet"]
filtered = filtered[mask]

if only_links:
    filtered = filtered[filtered["has_any_link"]]
if search:
    filtered = filtered[filtered["text"].str.contains(search, case=False, na=False)]
if len(date_range) == 2:
    filtered = filtered[(filtered["date"].dt.date >= date_range[0]) & (filtered["date"].dt.date <= date_range[1])]

# ====================== SORTING ======================
sort_option = st.sidebar.selectbox(
    "Sort by",
    ["Date (Newest First)", "Date (Oldest First)", "No Sorting"],
    index=0
)

if sort_option == "Date (Newest First)":
    filtered = filtered.sort_values("date", ascending=False)
elif sort_option == "Date (Oldest First)":
    filtered = filtered.sort_values("date", ascending=True)

st.sidebar.metric("Showing", f"{len(filtered):,} items")

# ====================== RESULTS ======================
st.subheader("Results")

if len(filtered) == 0:
    st.warning("No results match your filters.")
else:
    export_df = filtered.copy()

    def get_type(row):
        if row["is_retweet"]: return "Retweet"
        if row["is_quote"]: return "Quote"
        if row["is_reply"]: return "Reply"
        return "Post"

    export_df["Type"] = export_df.apply(get_type, axis=1)
    export_df["Date"] = export_df["date"].dt.strftime("%Y-%m-%d %H:%M")
    export_columns = ["Date", "Type", "text", "url"]

    # ====================== EXPORT OPTIONS ======================
    st.markdown("### 📥 Export Options")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.download_button("📄 CSV", export_df[export_columns].to_csv(index=False), "x_archive_links.csv", "text/csv")
    with col2:
        st.download_button("📦 JSON (Single File)", 
                           export_df[export_columns].to_json(orient="records", indent=2), 
                           "x_archive_links.json", "application/json")
    with col3:
        txt = "\n".join(export_df.apply(lambda r: f"{r['Date']} | {r['Type']} | {r['url']}", axis=1))
        st.download_button("📝 TXT", txt, "x_archive_links.txt", "text/plain")
    with col4:
        html = "<br>".join([f"<a href='{u}' target='_blank'>{d} | {t} | {u}</a>" for d, t, u in zip(export_df['Date'], export_df['Type'], export_df['url'])])
        st.download_button("🌐 HTML", f"<html><body>{html}</body></html>", "x_archive_links.html", "text/html")

    # ====================== SPLIT JSON WITH INDEX (UPDATED) ======================
    st.markdown("---")
    st.markdown("### 📦 Split JSON (Best for X Bulk Deleter)")

    col_split1, col_split2, col_split3 = st.columns([1.3, 1.3, 2.4])

    with col_split1:
        chunk_size = st.number_input(
            "Items per file", 
            min_value=1000, 
            max_value=20000, 
            value=8000, 
            step=1000,
            help="Higher = fewer files. Try 8000–12000 for big archives."
        )

    with col_split2:
        create_zip = st.checkbox("Download as one ZIP file", value=True)

    with col_split3:
        if st.button("Generate Split JSON Files", type="primary"):
            if len(export_df) == 0:
                st.warning("No data to export.")
            else:
                # === ADD GLOBAL INDEX ===
                export_df_indexed = export_df.reset_index(drop=True).copy()
                export_df_indexed["index"] = export_df_indexed.index   # Global index starting from 0

                export_columns_with_index = ["index"] + export_columns

                chunks = [
                    export_df_indexed[i:i + chunk_size] 
                    for i in range(0, len(export_df_indexed), chunk_size)
                ]
                st.success(f"Created {len(chunks)} part(s) with global index")

                if create_zip:
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for idx, chunk in enumerate(chunks, 1):
                            start_idx = chunk["index"].iloc[0]
                            end_idx = chunk["index"].iloc[-1]
                            
                            json_str = chunk[export_columns_with_index].to_json(orient="records", indent=2)
                            filename = f"x_archive_part{idx}_of_{len(chunks)}.json"
                            zip_file.writestr(filename, json_str)
                    
                    zip_buffer.seek(0)
                    st.download_button(
                        label=f"📦 Download All as ZIP ({len(chunks)} files) — Index {chunks[0]['index'].iloc[0]} → {chunks[-1]['index'].iloc[-1]}",
                        data=zip_buffer,
                        file_name="x_archive_split_json.zip",
                        mime="application/zip"
                    )
                else:
                    for idx, chunk in enumerate(chunks, 1):
                        start_idx = chunk["index"].iloc[0]
                        end_idx = chunk["index"].iloc[-1]
                        
                        json_str = chunk[export_columns_with_index].to_json(orient="records", indent=2)
                        filename = f"x_archive_part{idx}_of_{len(chunks)}.json"
                        st.download_button(
                            label=f"⬇️ {filename} ({len(chunk):,} items) — Index {start_idx} to {end_idx}",
                            data=json_str,
                            file_name=filename,
                            mime="application/json",
                            key=f"split_{idx}"
                        )

    # ====================== TABLE ======================
    if len(filtered) <= 1000:
        if st.button("📋 Copy URLs to Clipboard"):
            st.session_state.visible_urls = "\n".join(export_df["url"].tolist())
            st.success(f"Copied {len(filtered)} URLs")
        if "visible_urls" in st.session_state:
            st.text_area("Copied URLs", st.session_state.visible_urls, height=120)
    else:
        st.caption("Copy hidden for large results. Use downloads above.")

    display_df = export_df[["Date", "Type", "has_any_link", "text", "url"]].copy()
    display_df.columns = ["Date", "Type", "Has Link", "Text", "Open on X"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)
