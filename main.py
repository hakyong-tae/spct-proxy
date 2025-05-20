from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime

app = FastAPI()

# Optional: CORS 허용 (프론트에서 직접 호출 시 필요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 보안상 실제 도메인으로 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ /races → 가장 최근 output JSON 로드
@app.get("/races")
def get_races():
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    files = sorted(
        [f for f in os.listdir(output_dir) if f.startswith("events_") and f.endswith(".json")],
        reverse=True
    )

    if not files:
        return JSONResponse(status_code=404, content={"error": "No race data found."})

    latest_file = os.path.join(output_dir, files[0])
    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return JSONResponse(content=data)

# ✅ /player_record → bib 번호 실시간 크롤링
@app.get("/player_record")
def get_player_record(event_no: str = Query(...), bib_no: str = Query(...)):
    url = f"https://time.spct.kr/m2.php?EVENT_NO={event_no}&TargetYear=2025&currentPage=1&BIB_NO={bib_no}"
    print("Fetching player record:", url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    try:
        title = soup.select_one("div.board.view h3.subject").contents[0].strip()
        date = soup.select_one("p.date").get_text(strip=True).replace("🏃", "").strip()
        name = soup.select_one("p.name").contents[0].strip()
        gender_category = soup.select_one("p.name span").text.strip()
        bib = soup.select_one("p.tag span").text.strip()
        total_record = soup.select_one("div.record .time").text.strip()

        start_time_line = soup.select("div.record p")[0].text.strip()
        start_time = start_time_line.split(":")[1].strip()

        finish_time_line = soup.select("div.record p")[1].text.strip()
        finish_time = finish_time_line.split(":")[1].strip()

        sections = []
        rows = soup.select("table tbody tr")
        for row in rows:
            tds = row.find_all("td")
            if len(tds) >= 2:
                sections.append({
                    "section": tds[0].text.strip(),
                    "record": tds[1].text.strip()
                })

        ranks = soup.select("ul.rank li")
        rank_overall = ""
        rank_gender = ""
        if len(ranks) >= 2:
            overall = ranks[0].select("p span")
            gender = ranks[1].select("p span")
            if len(overall) >= 2:
                rank_overall = f"{overall[0].text.strip()}/{overall[1].text.strip()}"
            if len(gender) >= 2:
                rank_gender = f"{gender[0].text.strip()}/{gender[1].text.strip()}"

        return JSONResponse(content={
            "event_no": event_no,
            "bib_no": bib,
            "title": title,
            "date": date,
            "name": name,
            "gender_category": gender_category,
            "total_record": total_record,
            "start_time": start_time,
            "finish_time": finish_time,
            "sections": sections,
            "rank_overall": rank_overall,
            "rank_gender": rank_gender
        })

    except Exception as e:
        print("Parsing error:", e)
        return JSONResponse(status_code=404, content={"error": "Parsing failed or data not found."})

# ✅ 로컬 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
