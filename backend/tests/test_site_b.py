from pathlib import Path
from unittest.mock import MagicMock

from app.scrapers.stage import StageScraper


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "stage_list.html"


HTML_DETAIL_1 = """
<html>
    <body>
        <article>
            <h1>Stage Développeur Python</h1>
            <p>
                Nous recherchons un stagiaire en développement Python
                sur Casablanca.
            </p>
        </article>
    </body>
</html>
"""


HTML_DETAIL_2 = """
<html>
    <body>
        <article>
            <h1>Stage Data Science</h1>
            <p>
                Nous recherchons un stagiaire en Data Science
                sur Rabat.
            </p>
        </article>
    </body>
</html>
"""


def test_stage_scraper(mocker):
    scraper = StageScraper()

    # Lecture du fichier HTML local
    html_list = FIXTURE_PATH.read_text(encoding="utf-8")

    res_list = MagicMock()
    res_list.status_code = 200
    res_list.text = html_list

    res_detail_1 = MagicMock()
    res_detail_1.status_code = 200
    res_detail_1.text = HTML_DETAIL_1

    res_detail_2 = MagicMock()
    res_detail_2.status_code = 200
    res_detail_2.text = HTML_DETAIL_2

    # Aucun appel réseau réel
    mocker.patch.object(
        scraper,
        "get",
        side_effect=[
            res_list,
            res_detail_1,
            res_detail_2,
        ],
    )

    offers = scraper.fetch_offers()

    assert len(offers) == 2

    assert offers[0].title == "Stage Développeur Python"
    assert offers[0].url == (
        "https://www.stage.ma/offres-stage/9357-stage-python"
    )

    assert offers[1].title == "Stage Data Science"
    assert offers[1].url == (
        "https://www.stage.ma/offres-stage/9355-stage-data"
    )

    assert "stagiaire en développement Python" in offers[0].description
    assert "stagiaire en Data Science" in offers[1].description