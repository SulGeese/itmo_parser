import requests
from bs4 import BeautifulSoup


def parse_all():
    urls = [
        "https://abit.itmo.ru/rating/bachelor/budget/1844",
        "https://abit.itmo.ru/rating/bachelor/budget/1870",
        "https://abit.itmo.ru/rating/bachelor/budget/1845",
        "https://abit.itmo.ru/rating/bachelor/budget/1872",
        "https://abit.itmo.ru/rating/bachelor/budget/1846",
        "https://abit.itmo.ru/rating/bachelor/budget/1847",
        "https://abit.itmo.ru/rating/bachelor/budget/1848",
        "https://abit.itmo.ru/rating/bachelor/budget/1849",
        "https://abit.itmo.ru/rating/bachelor/budget/1850",
        "https://abit.itmo.ru/rating/bachelor/budget/1851",
        "https://abit.itmo.ru/rating/bachelor/budget/1852",
        "https://abit.itmo.ru/rating/bachelor/budget/1853",
        "https://abit.itmo.ru/rating/bachelor/budget/1854",
        "https://abit.itmo.ru/rating/bachelor/budget/1855",
        "https://abit.itmo.ru/rating/bachelor/budget/1856",
        "https://abit.itmo.ru/rating/bachelor/budget/1857",
        "https://abit.itmo.ru/rating/bachelor/budget/1858",
        "https://abit.itmo.ru/rating/bachelor/budget/1859",
        "https://abit.itmo.ru/rating/bachelor/budget/1860",
        "https://abit.itmo.ru/rating/bachelor/budget/1861",
        "https://abit.itmo.ru/rating/bachelor/budget/1862",
        "https://abit.itmo.ru/rating/bachelor/budget/1863",
        "https://abit.itmo.ru/rating/bachelor/budget/1864",
        "https://abit.itmo.ru/rating/bachelor/budget/1865",
        "https://abit.itmo.ru/rating/bachelor/budget/1866",
        "https://abit.itmo.ru/rating/bachelor/budget/1867",
        "https://abit.itmo.ru/rating/bachelor/budget/1869",
    ]
    users = {}
    places = {}

    def parse_page(url: str):
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")
        course = int(url.split("/")[-1])

        def add_user(user_div: BeautifulSoup, olymp: bool):
            place, user_id = (user_div.find("p", class_="RatingPage_table__position__uYWvi")
                              .text.replace("№", "").split())
            place = int(place)
            priority = int(user_div.find("div", class_="RatingPage_table__infoLeft__Y_9cA").find("span").text)
            original = (user_div.find_all("div", class_="RatingPage_table__info__quwhV")[-1].find_all("div")[-1]
                        .find("span").text.strip())
            if not olymp:
                result = int(
                    user_div.find_all("div", class_="RatingPage_table__infoLeft__Y_9cA")[1].find_all("span")[1].text)
            else:
                result = 0
            if original == "да":
                users[user_id] = (users.get(user_id, []) +
                                  [{"priority": priority, "result": result, "olymp": olymp, "course": course,
                                    "place": place}])

        headers = list(map(lambda x: x.text, soup.find_all("h5", class_="RatingPage_title__zlsGy")))
        pass_type = {headers[i]: soup.find_all("div", class_="RatingPage_table__FbzTn")[i] for i in range(len(headers))}

        data = soup.find("div", class_="RatingPage_rating__placesBlock__6P3FC").find("p", class_="high").text
        plc = {"КМ": int(data.split()[2])}
        for p in data.split("(")[1].strip(")").split(", "):
            count, name = p.split()
            count = int(count)
            plc.setdefault(name, count)

        if data := pass_type.get("Без вступительных испытаний"):
            for elem in data.find_all("div", class_="RatingPage_table__item__qMY0F"):
                add_user(elem, True)

        for name, abr in (("Целевая квота", "ЦК"), ("Особая квота", "ОcК"), ("Отдельная квота", "ОтК")):
            if data := pass_type.get(name):
                data = list(filter(lambda x: x.find_all("div", class_="RatingPage_table__info__quwhV")[-1]
                                   .find_all("div")[-1].find("span").text.strip() == "да", data))
                ln = len(data)
                if ln >= plc[abr]:
                    plc["КМ"] = plc.get("КМ") - plc[abr]
                else:
                    plc["КМ"] = plc.get("КМ") - ln
        places[course] = plc.get("КМ")

        if data := pass_type.get("Общий конкурс"):
            for elem in data.find_all("div", class_="RatingPage_table__item__qMY0F"):
                add_user(elem, False)

    for url in urls:
        parse_page(url)

    for id in users:
        users[id].sort(key=lambda x: x["priority"])
    return users, places


def main(users: dict):
    competition_group = {}
    not_added_users_ids = list(users)

    # Добавляет людей, которые еще не участвуют в конкурсе, в competition_group по более высокому приоритету
    def fill_competition_group(users_ids):
        for user_id in users_ids:
            if users[user_id] and (application := users[user_id].pop(0)):
                competition_group[application["course"]] = (competition_group.get(application["course"], []) +
                                                            [[user_id, application]])
            else:
                print(user_id)

    # Убирает людей, которые не прошли по конкурсу, из competition_group и добавляет их в not_added_users
    def filter_competition_group():
        not_added_users = []
        for course, group in competition_group.items():
            group.sort(key=lambda x: (x[1]["olymp"], x[1]["result"], -x[1]["place"]), reverse=True)
            num_of_places = places[course]
            if len(group) > num_of_places:
                not_added_users.extend(list(map(lambda x: x[0], group))[num_of_places:])
                competition_group[course] = group[:num_of_places]
        return not_added_users

    # Заполняет competition_group до тех пор, пока не закончатся not_added_users_ids
    while not_added_users_ids:
        fill_competition_group(not_added_users_ids)
        not_added_users_ids = filter_competition_group()
    return competition_group


if __name__ == "__main__":
    users, places = parse_all()
    competition_group = main(users)
    for course, group in competition_group.items():
        if course not in [1845, 1872, 1846, 1855, 1856, 1857, 1860, 1861, 1862, 1863, 1866, 1867, 1869]:
            print(course, group)
            print(course, group[-1][1]["result"])
            print()

