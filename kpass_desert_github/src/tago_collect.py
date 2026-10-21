"""
TAGO 버스노선정보 수집 스크립트 (본인 PC에서 실행)
--------------------------------------------------
사용법
  1) pip install requests
  2) 아래 SERVICE_KEY 에 공공데이터포털 '일반 인증키(Decoding)' 붙여넣기
  3) python tago_collect.py
결과
  tago_cities.csv          : 도시코드 목록
  tago_routes.csv          : 도시별 노선 목록 (노선유형, 첫차/막차)
  tago_route_info.csv      : 노선별 배차간격(평일/토/일)
  tago_route_stops.csv     : 노선별 경유 정류장 (COLLECT_STOPS=True 일 때)
특징
  - 중간에 끊겨도 다시 실행하면 이어서 수집 (이미 받은 노선은 건너뜀)
  - 일일 호출 한도 초과(에러코드 22) 시 자동 중단 → 다음 날 다시 실행
"""
import csv, os, time, sys, random
import requests

SERVICE_KEY = "여기에_디코딩_인증키"
COLLECT_STOPS = False         # 노선별 경유정류장 (호출 수 2배라 기본 끔)
SLEEP = 0.05                  # 초당 호출 제한(30tps) 여유
BASE = "http://apis.data.go.kr/1613000/BusRouteInfoInqireService"


class LimitExceeded(Exception):
    pass


def call(op, **params):
    p = {"serviceKey": SERVICE_KEY, "_type": "json", "numOfRows": 1000, "pageNo": 1}
    p.update(params)
    items, page = [], 1
    while True:
        p["pageNo"] = page
        for attempt in range(3):
            try:
                r = requests.get(f"{BASE}/{op}", params=p, timeout=20)
                if "LIMITED_NUMBER_OF_SERVICE_REQUESTS" in r.text:
                    raise LimitExceeded()
                try:
                    j = r.json()
                except ValueError:              # JSON이 아닌 응답(XML 오류 등)
                    j = {}
                break
            except LimitExceeded:
                raise
            except Exception as e:
                if attempt == 2:
                    print("  실패:", op, params, e)
                    return items
                time.sleep(2)
        resp = j.get("response") if isinstance(j, dict) else None
        body = resp.get("body") if isinstance(resp, dict) else None
        if not isinstance(body, dict):          # 빈 응답·비정상 응답은 결과 없음으로 처리
            time.sleep(SLEEP)
            return items
        it = body.get("items") or {}
        it = it.get("item", []) if isinstance(it, dict) else []
        if isinstance(it, dict):
            it = [it]
        items += [x for x in it if isinstance(x, dict)]
        try:
            total = int(body.get("totalCount", 0) or 0)
        except (TypeError, ValueError):
            total = 0
        time.sleep(SLEEP)
        if page * p["numOfRows"] >= total:
            return items
        page += 1


def append(path, rows, fields):
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerows(rows)


def done_ids(path, key="routeid"):
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8-sig") as f:
        return {row[key] for row in csv.DictReader(f)}


def main():
    try:
        # 1) 도시코드
        if not os.path.exists("tago_cities.csv"):
            cities = call("getCtyCodeList")
            append("tago_cities.csv", cities, ["citycode", "cityname"])
        with open("tago_cities.csv", encoding="utf-8-sig") as f:
            cities = list(csv.DictReader(f))
        print("도시 수:", len(cities))

        # 2) 도시별 노선 목록
        got_city = done_ids("tago_routes.csv", "citycode")
        for c in cities:
            if c["citycode"] in got_city:
                continue
            rs = call("getRouteNoList", cityCode=c["citycode"])
            for r in rs:
                r["citycode"], r["cityname"] = c["citycode"], c["cityname"]
            append("tago_routes.csv", rs or [{"citycode": c["citycode"], "cityname": c["cityname"]}],
                   ["citycode", "cityname", "routeid", "routeno", "routetp",
                    "startnodenm", "endnodenm", "startvehicletime", "endvehicletime"])
            print(f"  노선목록 {c['cityname']}: {len(rs)}")

        with open("tago_routes.csv", encoding="utf-8-sig") as f:
            routes = [r for r in csv.DictReader(f) if r.get("routeid")]
        print("노선 수:", len(routes))

        # 3) 노선별 배차간격
        got = done_ids("tago_route_info.csv")
        todo = [r for r in routes if r["routeid"] not in got]
        random.Random(42).shuffle(todo)   # 남은 노선을 도시 구분 없이 고르게 섞어서 수집
        print("배차간격 남은 노선:", len(todo))
        for i, r in enumerate(todo, 1):
            info = call("getRouteInfoIem", cityCode=r["citycode"], routeId=r["routeid"])
            row = info[0] if info else {"routeid": r["routeid"]}
            row["citycode"] = r["citycode"]
            append("tago_route_info.csv", [row],
                   ["citycode", "routeid", "routeno", "routetp", "startvehicletime", "endvehicletime",
                    "intervaltime", "intervalsattime", "intervalsuntime"])
            if i % 200 == 0:
                print(f"  {i}/{len(todo)}")

        # 4) 노선별 경유 정류장
        if COLLECT_STOPS:
            got = done_ids("tago_route_stops.csv")
            todo = [r for r in routes if r["routeid"] not in got]
            print("경유정류장 남은 노선:", len(todo))
            for i, r in enumerate(todo, 1):
                st = call("getRouteAcctoThrghSttnList", cityCode=r["citycode"], routeId=r["routeid"])
                for s in st:
                    s["citycode"] = r["citycode"]
                append("tago_route_stops.csv", st or [{"routeid": r["routeid"], "citycode": r["citycode"]}],
                       ["citycode", "routeid", "nodeid", "nodenm", "nodeno", "nodeord",
                        "gpslati", "gpslong", "updowncd"])
                if i % 200 == 0:
                    print(f"  {i}/{len(todo)}")
        print("완료")
    except LimitExceeded:
        print("\n오늘 호출 한도를 다 썼습니다. 내일 같은 명령으로 다시 실행하면 이어서 받습니다.")
        sys.exit(0)


if __name__ == "__main__":
    main()
