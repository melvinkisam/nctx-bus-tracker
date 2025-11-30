from bs4 import BeautifulSoup
from scraper import get_element_by_id    


html = get_element_by_id("https://www.nctx.co.uk/stops/3390BU05").prettify()
soup = BeautifulSoup(html, "html.parser")


def get_element_ids(html):
    soup = BeautifulSoup(html, "html.parser")
    return [tag.get("id") for tag in soup.find_all(id=True)]


def get_element_classes(html):
    soup = BeautifulSoup(html, "html.parser")
    class_set = set()

    for tag in soup.find_all(class_=True):
        class_set.update(tag.get("class"))

    return list(class_set)


results = []

for item in soup.select("li.departure-board__item"):
    a = item.find("a")

    # Extract fields
    service = a.select_one(".single-visit__name").get_text(strip=True)
    destination = a.select_one(".single-visit__description").get_text(strip=True)
    departure_time = a.select_one(".single-visit__arrival-time__cell").get_text(strip=True)

    # Determine if it is real-time or scheduled
    status = "expected" if "single-visit--expected" in a.get("class", []) else "scheduled"

    # You can also extract the sr-only text (if needed)
    sr_text = a.select_one("p.sr-only").get_text(" ", strip=True)

    results.append({
        "service": service,
        "destination": destination,
        "departure_time": departure_time,
        "status": status,
        "sr_text": sr_text,
        "href": a.get("href"),
        "journey": a.get("data-journey")
    })


# Print results
for r in results:
    print(r["service"])
    print(r["destination"])
    print(r["departure_time"])
    print(r["status"])
    print("=" * 20)

print("element_ids:", get_element_ids(html))
print("element_classes:", get_element_classes(html))