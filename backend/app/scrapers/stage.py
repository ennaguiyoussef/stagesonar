import re
from datetime import datetime
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, ScrapedOffer


class StageScraper(BaseScraper):
    name = "stage.ma"
    base_url = "https://www.stage.ma"
    search_url = "https://www.stage.ma/offres-stage"

    def fetch_offers(self) -> List[ScrapedOffer]:
        """
        Récupère les offres de stage depuis Stage.ma.
        """

        response = self.get(self.search_url)

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        offers: List[ScrapedOffer] = []

        candidates = soup.select("a.flex.text-lg.capitalize.font-bold")

        seen_urls = set()

        for item in candidates:
            href = item.get("href")

            if not href:
                continue

            url = urljoin(self.base_url, href)

            if url in seen_urls:
                continue

            title = item.get_text(" ", strip=True)

            if not title or len(title) < 5:
                continue

            parent = item.parent
            text = parent.get_text(" ", strip=True) if parent else title

            company = self._extract_company(parent, text)
            city = self._extract_city(text)
            published_at = self._extract_date(text)

            offer = ScrapedOffer(
                title=title,
                company=company,
                location=city,
                url=url,
                description="",
                published_at=published_at,
            )

            offers.append(offer)
            seen_urls.add(url)

        # Récupération des informations détaillées
        # uniquement pour les 20 premières offres.
        for offer in offers[:20]:
            try:
                detail_response = self.get(offer.url)

                if detail_response.status_code != 200:
                    continue

                detail_soup = BeautifulSoup(
                    detail_response.text,
                    "html.parser",
                )

                # Description
                content = self._extract_description(detail_soup)

                if content:
                    offer.description = content[:2000]

                # Ville depuis la page détaillée
                detail_city = self._extract_label_value(
                    detail_soup,
                    "Ville",
                )

                if detail_city:
                    offer.location = detail_city

                # Organisme / entreprise depuis la page détaillée
                detail_company = self._extract_organisme(
                    detail_soup
                )

                if detail_company:
                    offer.company = detail_company

                # Date depuis la page détaillée si elle n'était
                # pas trouvée sur la page de liste.
                if offer.published_at is None:
                    detail_date = self._extract_date(
                        detail_soup.get_text(" ", strip=True)
                    )

                    if detail_date:
                        offer.published_at = detail_date

            except Exception:
                continue

        return offers

    @staticmethod
    def _extract_company(item, text: str) -> str:
        """
        Essaie d'extraire le nom de l'entreprise depuis
        la carte de l'offre.
        """

        if item:
            company_tag = item.select_one(
                ".company, "
                ".company-name, "
                ".employer, "
                ".job-company, "
                "[class*='company']"
            )

            if company_tag:
                company = company_tag.get_text(" ", strip=True)

                if company:
                    return company

        patterns = [
            r"Entreprise\s*[:\-]\s*(.+?)(?:\s+Ville|\s+Localisation|\s+Date|$)",
            r"Société\s*[:\-]\s*(.+?)(?:\s+Ville|\s+Localisation|\s+Date|$)",
            r"Organisme\s*[:\-]\s*(.+?)(?:\s+Ville|\s+Localisation|\s+Date|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)

            if match:
                company = match.group(1).strip()

                if company:
                    return company

        return "Non spécifié"

    @staticmethod
    def _extract_city(text: str) -> str:
        """
        Recherche une ville marocaine connue dans le texte.
        """

        # Cas où le texte contient explicitement :
        # Ville Casablanca
        match = re.search(
            r"\bVille\s*[:\-]?\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']+)",
            text,
            re.IGNORECASE,
        )

        if match:
            city = match.group(1).strip()

            # Évite de récupérer trop de texte après la ville.
            city = re.split(
                r"\b(?:Spécialité|Date|Secteur|Pays|Type|Niveau)\b",
                city,
                flags=re.IGNORECASE,
            )[0].strip()

            if city:
                return city

        cities = [
            "Casablanca",
            "Rabat",
            "Tanger",
            "Marrakech",
            "Fès",
            "Agadir",
            "Kénitra",
            "Meknès",
            "Oujda",
            "El Jadida",
            "Mohammedia",
            "Tétouan",
            "Safi",
            "Béni Mellal",
            "Nador",
        ]

        text_lower = text.lower()

        for city in cities:
            if city.lower() in text_lower:
                return city

        return "Maroc"

    @staticmethod
    def _extract_label_value(
        soup: BeautifulSoup,
        label: str,
    ) -> str:
        """
        Extrait la valeur située à côté d'un label,
        par exemple :

        Ville
        Casablanca
        """

        label_node = soup.find(
            lambda tag: (
                tag.name in ("span", "div", "p")
                and tag.get_text(" ", strip=True).lower()
                == label.lower()
            )
        )

        if not label_node:
            return ""

        parent = label_node.parent

        if not parent:
            return ""

        # Cherche les éléments frères directs.
        for child in parent.find_all(
            ["span", "div", "p"],
            recursive=False,
        ):
            value = child.get_text(" ", strip=True)

            if not value:
                continue

            if value.lower() == label.lower():
                continue

            return value

        # Fallback : élément suivant.
        next_element = label_node.find_next(
            ["span", "div", "p"]
        )

        if next_element and next_element is not label_node:
            value = next_element.get_text(" ", strip=True)

            if value and value.lower() != label.lower():
                return value

        return ""

    @staticmethod
    def _extract_organisme(soup: BeautifulSoup) -> str:
        """
        Essaie de récupérer le nom de l'organisme / entreprise
        depuis la page détaillée.
        """

        # Recherche du bloc contenant "Organisme".
        organisme_node = soup.find(
            string=lambda text: (
                text
                and text.strip().lower() == "organisme"
            )
        )

        if not organisme_node:
            return ""

        parent = organisme_node.parent

        if not parent:
            return ""

        # Cherche le bloc parent contenant les informations
        # de l'organisme.
        container = parent.parent

        if container:
            text = container.get_text(" ", strip=True)

            if text:
                # Nettoyage des libellés qui peuvent suivre.
                text = re.sub(
                    r"\bOrganisme\b",
                    "",
                    text,
                    flags=re.IGNORECASE,
                ).strip()

                # Si le site contient par exemple :
                # Organisme Fondé en 1998 Pays Maroc Secteur ...
                # on récupère uniquement la première partie.
                text = re.split(
                    r"\b(?:Fondé en|Pays|Secteur|Bureau)\b",
                    text,
                    flags=re.IGNORECASE,
                )[0].strip()

                if text and text not in ("---", "--", "-"):
                    return text

        return ""

    @staticmethod
    def _extract_date(text: str):
        """
        Extrait une date de publication si elle existe.
        """

        patterns = [
            r"\b\d{1,2}/\d{1,2}/\d{4}\b",
            r"\b\d{1,2}-\d{1,2}-\d{4}\b",
            r"\b\d{4}-\d{1,2}-\d{1,2}\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if not match:
                continue

            date_text = match.group(0)

            for date_format in (
                "%d/%m/%Y",
                "%d-%m-%Y",
                "%Y-%m-%d",
            ):
                try:
                    return datetime.strptime(
                        date_text,
                        date_format,
                    )
                except ValueError:
                    continue

        return None

    @staticmethod
    def _extract_description(soup: BeautifulSoup) -> str:
        """
        Extrait le contenu principal de la page de détail.
        """

        for tag in soup(
            ["script", "style", "nav", "footer", "header"]
        ):
            tag.decompose()

        content = soup.select_one(
            "article, "
            ".job-description, "
            ".offer-description, "
            ".description, "
            ".entry-content, "
            "main"
        )

        if not content:
            return ""

        text = content.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text)

        return text.strip()