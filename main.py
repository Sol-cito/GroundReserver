import requests, calendar, json
from datetime import datetime


def login(loginInfo, session):
    URL = "http://www.futsalbase.com/api/login"
    params = {
        "id": loginInfo.get("id"),
        "password": loginInfo.get("password")
    }
    # activate session
    res = session.post(URL, params)
    print("[Login Response Code] : ", res.status_code)
    return res.json().get("user").get("szId")


def getDateList():
    targetYear = datetime.today().year
    targetMonth = datetime.today().month + 1
    if targetMonth == 1: targetYear += 1

    targetMonthInfo = calendar.monthrange(targetYear, targetMonth)

    # 5 and 6 are sat, sun respectively
    date_firstSaturday = abs(5 - targetMonthInfo[0]) if targetMonthInfo[0] < 6 else 6
    date_firstSunday = abs(6 - targetMonthInfo[0])
    days = targetMonthInfo[1]

    date_list = []
    for i in range(date_firstSaturday, days, 7):
        date_list.append(
            str(datetime.strptime(str(targetYear) + "-" + str(targetMonth) + "-" + str(i + 1), "%Y-%m-%d").date()))
    for i in range(date_firstSunday, days, 7):
        date_list.append(
            str(datetime.strptime(str(targetYear) + "-" + str(targetMonth) + "-" + str(i + 1), "%Y-%m-%d").date()))
    return date_list


def searchAllAvailableFields(session, target_date, target_time):
    date_list = getDateList()
    field_list = ['A', 'B', 'C', 'D', 'E', 'H', 'I']

    result_dictionary = {}

    for field in field_list:
        for date in date_list:
            URL = "http://www.futsalbase.com/api/reservation/allList/?stadium=" + field + "&date=" + date
            res = session.get(URL)
            if not res.ok: continue
            for element in res.json().get('data'):
                if 'szDInfo' not in element.keys():  # if not reserved
                    if target_date and str(element.get('ssdate')) not in target_date: continue
                    if target_time and not isTargetTimeIncluded(element.get('strtime'), target_time): continue
                    result_dictionary[field] = element
    return result_dictionary


def isTargetTimeIncluded(available_time, target_time):
    return str(available_time).strip() in target_time


def reserveGround(result_dictionary, szId, session):
    URL = "http://www.futsalbase.com/api/reservation/addList"
    params = {
        "szId": szId,
        "szStadium": "",
        "szDDate": "",
        "selectedList": []
    }
    print(params)
    # res = session.post(URL, params)


if __name__ == '__main__':
    # TO-DO
    # 1. logger
    # 2. Kakao Notification
    # 3. actually making reservation

    LOGIN_INFO = {
        "id": "dataenggu",
        "password": "Solda9010!"
    }

    target_date = set([
        '2022-03-26'
    ])

    target_time = set([
        '02:00 ~ 04:00',
    ])

    with requests.session() as session:
        szId = login(LOGIN_INFO, session)

        result_dictionary = searchAllAvailableFields(session, target_date, target_time)
        print(result_dictionary)

        if result_dictionary:
            reserveGround(result_dictionary, szId, session)
