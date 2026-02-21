"""
Fetches patent data from the European Patent Office (EPO) OPS API.
Uses python-epo-ops-client for OAuth2 token management.
"""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

import epo_ops

logger = logging.getLogger(__name__)

# Map company names to their applicant codes / search terms for EPO
EPO_APPLICANT_MAP: dict[str, str] = {
    "Lockheed Martin": "LOCKHEED MARTIN",
    "BAE Systems": "BAE SYSTEMS",
    "Rheinmetall": "RHEINMETALL",
    "Thales": "THALES",
    "Leonardo": "LEONARDO",
    "Airbus": "AIRBUS",
    "General Dynamics": "GENERAL DYNAMICS",
    "Northrop Grumman": "NORTHROP GRUMMAN",
    "Raytheon": "RAYTHEON",
}


@dataclass
class PatentRecord:
    patent_id: str          # e.g. "EP3456789"
    title: str
    abstract: str
    claims: str
    applicant: str
    filing_date: str
    publication_date: str
    ipc_codes: list[str] = field(default_factory=list)
    pdf_url: Optional[str] = None
    company_name: str = ""
    source_type: str = "patent"


class EPOClient:
    def __init__(self, consumer_key: str, consumer_secret: str):
        self.client = epo_ops.Client(
            key=consumer_key,
            secret=consumer_secret,
            accept_type="json",
        )

    def _search_patents_sync(self, applicant_name: str, max_results: int) -> list[dict]:
        """Search published data (OPS published-data/search)."""
        cql = f'pa="{applicant_name}"'
        try:
            response = self.client.published_data_search(
                cql=cql,
                range_begin=1,
                range_end=min(max_results, 100),
            )
            data = response.json()
            results = (
                data.get("ops:world-patent-data", {})
                .get("ops:biblio-search", {})
                .get("ops:search-result", {})
                .get("exchange-documents", [])
            )
            if isinstance(results, dict):
                results = [results]
            return results
        except Exception as exc:
            logger.error("EPO search error for '%s': %s", applicant_name, exc)
            return []

    def _parse_exchange_doc(self, doc: dict, company_name: str) -> Optional[PatentRecord]:
        try:
            ed = doc.get("exchange-document", doc)
            biblio = ed.get("bibliographic-data", {})

            # Patent ID
            pub_ref = biblio.get("publication-reference", {}).get("document-id", {})
            if isinstance(pub_ref, list):
                pub_ref = pub_ref[0]
            country = pub_ref.get("country", {}).get("$", "EP")
            doc_number = pub_ref.get("doc-number", {}).get("$", "")
            kind = pub_ref.get("kind", {}).get("$", "")
            patent_id = f"{country}{doc_number}{kind}"

            # Title
            titles = biblio.get("invention-title", [])
            if isinstance(titles, dict):
                titles = [titles]
            title = next(
                (t.get("$", "") for t in titles if t.get("@lang") == "en"),
                titles[0].get("$", "") if titles else "",
            )

            # Abstract
            abstract_data = ed.get("abstract", [])
            if isinstance(abstract_data, dict):
                abstract_data = [abstract_data]
            abstract = " ".join(
                p.get("$", "")
                for a in abstract_data
                for p in (a.get("p", []) if isinstance(a.get("p"), list) else [a.get("p", {})])
            )

            # Claims
            claims_data = ed.get("claims", {}).get("claim", [])
            if isinstance(claims_data, dict):
                claims_data = [claims_data]
            claims = " ".join(
                c.get("claim-text", {}).get("$", "")
                if isinstance(c.get("claim-text"), dict)
                else ""
                for c in claims_data
            )

            # IPC codes
            ipc_raw = biblio.get("classification-ipc", {}).get("text", {})
            ipc_codes = [ipc_raw.get("$", "")] if isinstance(ipc_raw, dict) else []

            # Dates
            filing_date = (
                biblio.get("application-reference", {})
                .get("document-id", {})
                .get("date", {})
                .get("$", "")
            )
            pub_date = pub_ref.get("date", {}).get("$", "")

            # PDF link (OPS rendering endpoint)
            pdf_url = (
                f"https://ops.epo.org/3.2/rest-services/published-data/publication/"
                f"epodoc/{country}{doc_number}/fulltext"
            )

            return PatentRecord(
                patent_id=patent_id,
                title=title,
                abstract=abstract,
                claims=claims,
                applicant=company_name,
                filing_date=filing_date,
                publication_date=pub_date,
                ipc_codes=ipc_codes,
                pdf_url=pdf_url,
                company_name=company_name,
            )
        except Exception as exc:
            logger.warning("Could not parse patent doc: %s", exc)
            return None

    async def fetch_patents(self, company_name: str, max_results: int = 30) -> list[PatentRecord]:
        applicant = EPO_APPLICANT_MAP.get(company_name, company_name.upper())
        loop = asyncio.get_event_loop()
        raw_docs = await loop.run_in_executor(
            None, self._search_patents_sync, applicant, max_results
        )
        records = []
        for doc in raw_docs:
            record = self._parse_exchange_doc(doc, company_name)
            if record:
                records.append(record)
        logger.info("Fetched %d patents for %s", len(records), company_name)
        return records


def get_epo_client(consumer_key: str, consumer_secret: str) -> EPOClient:
    return EPOClient(consumer_key=consumer_key, consumer_secret=consumer_secret)
