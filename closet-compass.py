import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
import requests
import json

st.set_page_config(page_title="ClosetCompass", page_icon="👕", layout="wide")
st.title("👕 ClosetCompass – Your Weekly Wardrobe Partner")
st.caption("Plan your week with AI • Weather-smart • Fun & interactive")

# ────────────────────────────────────────────────
# SESSION STATE
# ────────────────────────────────────────────────
if "closet" not in st.session_state:
    st.session_state.closet = pd.DataFrame({
        "Item": ["Black blazer", "White shirt", "Jeans", "Navy dress", "Sneakers", "Floral top", "Swim trunks", "Silver necklace", "Leather belt"],
        "Category": ["Top", "Top", "Bottom", "Dress", "Shoes", "Top", "Bottom", "Accessory", "Accessory"],
        "Color": ["Black", "White", "Blue", "Navy", "White", "Multi", "Blue", "Silver", "Brown"],
        "Occasion": ["Formal", "Casual", "Casual", "Formal", "Casual", "Casual", "Pool", "Any", "Any"]
    })

if "profile" not in st.session_state:
    st.session_state.profile = {"age": 35, "country": "USA", "religion": "None", "company": "Casual", "situations": ["Work", "Casual Friday"]}

if "liked_items" not in st.session_state:
    st.session_state.liked_items = []

if "week_plan" not in st.session_state:
    st.session_state.week_plan = {f"Day {i+1}": {"locked": False, "outfit": None, "note": ""} for i in range(7)}

# ────────────────────────────────────────────────
# SIDEBAR – Quick actions & closet preview
# ────────────────────────────────────────────────
with st.sidebar:
    st.header("Your Closet")
    st.dataframe(st.session_state.closet, use_container_width=True, height=220)

    st.subheader("Quick Chat with AI Stylist")
    user_note = st.text_input("Tell your stylist team...", placeholder="Make Wednesday more casual", key="quick_note")
    if user_note:
        st.info(f"📝 Noted: {user_note}\n(I'll apply this when you regenerate days)")

# ────────────────────────────────────────────────
# TABS
# ────────────────────────────────────────────────
tab_week, tab_video, tab_profile, tab_packing = st.tabs(
    ["📆 Weekly Planner (Main)", "📹 Video + Voice Scan", "👤 Profile", "🧳 Packing List"]
)

# ────────────────────────────────────────────────
# WEEKLY PLANNER TAB – the new heart of the app
# ────────────────────────────────────────────────
with tab_week:
    st.subheader("Plan Your Week – Partner with Your AI Stylist Team")

    # Location & Weather
    col1, col2 = st.columns([3,1])
    with col1:
        location = st.text_input("Zip code or City, Country", value="Miami, USA", key="loc")
    with col2:
        if st.button("Get Weather Forecast"):
            try:
                # Open-Meteo – free, no key, great for prototypes
                if "," in location:
                    city = location.split(",")[0].strip()
                    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en"
                    res = requests.get(url).json()
                    if "results" in res and res["results"]:
                        lat = res["results"][0]["latitude"]
                        lon = res["results"][0]["longitude"]
                    else:
                        lat, lon = 25.76, -80.19  # fallback Miami
                else:
                    lat, lon = 25.76, -80.19

                weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=auto&forecast_days=7"
                w = requests.get(weather_url).json()
                st.session_state.weather = w["daily"]
                st.success("Weather loaded! ☀️")
            except:
                st.warning("Weather fetch failed – using mock data")
                st.session_state.weather = {
                    "time": [str(datetime.today() + timedelta(days=i))[:10] for i in range(7)],
                    "temperature_2m_max": [random.randint(68,88) for _ in range(7)],
                    "temperature_2m_min": [random.randint(60,78) for _ in range(7)],
                    "weather_code": [random.choice([0,1,3,45,61]) for _ in range(7)]
                }

    # Show 7-day grid
    if "weather" in st.session_state:
        progress = sum(1 for v in st.session_state.week_plan.values() if v["locked"]) / 7
        st.progress(progress)
        st.caption(f"Week planning progress: {int(progress*100)}% – keep going! 🎉" if progress == 1 else f"{int(progress*100)}% planned")

        for i in range(7):
            day_key = f"Day {i+1}"
            date = datetime.today() + timedelta(days=i)
            day_str = date.strftime("%a %b %d")

            temp_max = st.session_state.weather["temperature_2m_max"][i]
            temp_min = st.session_state.weather["temperature_2m_min"][i]
            code = st.session_state.weather["weather_code"][i]
            weather_emoji = "☀️" if code in [0,1] else "⛅" if code in [3] else "🌧️" if code >= 51 else "🌫️"

            with st.expander(f"**{day_str}**  •  {weather_emoji} {temp_min}–{temp_max}°F"):
                col_top, col_alt1, col_alt2 = st.columns(3)

                # Generate / show 3 options
                for j, col in enumerate([col_top, col_alt1, col_alt2]):
                    if not st.session_state.week_plan[day_key]["locked"]:
                        items = st.session_state.closet.sample(3)
                        outfit = " + ".join(items["Item"].tolist())
                        acc = st.session_state.closet[st.session_state.closet["Category"]=="Accessory"].sample(1)["Item"].values
                        acc = acc[0] if len(acc)>0 else ""
                        full = f"{outfit} + {acc}"

                        # Very basic safety
                        if st.session_state.profile["age"] < 21:
                            full = full.replace("short", "knee-length")

                        label = "**TOP PICK**" if j==0 else f"Alt {j}"
                        with col:
                            st.markdown(f"**{label}**")
                            st.write(full)
                            st.image(f"https://picsum.photos/id/{100 + i*3 + j}/220/300", use_column_width=True)

                            if st.button("Choose this", key=f"pick_{i}_{j}"):
                                st.session_state.week_plan[day_key]["outfit"] = full
                                st.session_state.week_plan[day_key]["locked"] = True
                                st.session_state.liked_items.extend(items["Item"].tolist())
                                st.success("Locked in! 🎯")
                                st.rerun()

                    else:
                        with col:
                            st.success("Locked!")
                            st.write(st.session_state.week_plan[day_key]["outfit"])

                # Controls
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🔄 Regenerate day", key=f"regen_{i}"):
                        st.session_state.week_plan[day_key]["locked"] = False
                        st.rerun()
                with c2:
                    note = st.text_input("Quick note / request", value=st.session_state.week_plan[day_key]["note"], key=f"note_{i}")
                    st.session_state.week_plan[day_key]["note"] = note

    else:
        st.info("Enter location and get weather to start planning your week! 🌤️")

# ────────────────────────────────────────────────
# VIDEO + VOICE SCAN (kept from before)
# ────────────────────────────────────────────────
with tab_video:
    st.subheader("Add items with video + voice")
    video_file = st.file_uploader("15-sec closet video", type=["mp4","mov"])
    voice_desc = st.text_area("What you say while filming", "Black blazer for work, love neutrals...")
    if video_file and st.button("Process"):
        st.success("Items added from video + voice! (simulated)")

# ────────────────────────────────────────────────
# PROFILE (kept)
# ────────────────────────────────────────────────
with tab_profile:
    st.subheader("Your preferences & safety settings")
    st.session_state.profile["age"] = st.number_input("Age", 13, 80, 35)
    st.session_state.profile["country"] = st.selectbox("Country", ["USA","Japan","UAE","India","France"])
    st.session_state.profile["religion"] = st.selectbox("Religion", ["None","Muslim","Christian","Hindu"])
    st.session_state.profile["company"] = st.selectbox("Work culture", ["Casual","Business casual","Formal"])

# ────────────────────────────────────────────────
# PACKING LIST (kept)
# ────────────────────────────────────────────────
with tab_packing:
    st.subheader("Packing List (for trips)")
    if st.button("Generate"):
        st.write("**7-day essentials** (based on plan):")
        st.write("- 7 tops, 5 bottoms, accessories")
        st.write("[Amazon links for gaps](https://amazon.com)")

st.caption("Your weekly wardrobe partner – fun, interactive, weather-smart. Redeploy & enjoy! 🚀")
