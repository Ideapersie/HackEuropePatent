import requests
import base64
import xml.etree.ElementTree as ET

public_key = "JjdHDCaVZO09eeJDwV0vZ25bgd7fmcvj2RqplB1f3CQGfKhh"
secret_key = "D3bOi7SAAhpJJyfamMArmerFsFYG"


access_token = "xAlK17aLQckVpaDlbeG9jWA2gO8e"

ns = "{http://www.epo.org/exchange}"
ns_ft = "{http://www.epo.org/fulltext}"


def print_tree(tree):
    for elem in tree.iter():
        print(elem.tag, elem.text)


def get_abstract_from_docid(patent_id):
    url = f"https://ops.epo.org/rest-services/published-data/publication/epodoc/{patent_id}/abstract"
    header = {"Authorization": f"Bearer {access_token}"}
    x = requests.get(url, headers=header)
    if x.status_code != 200:
        return None
    tree = ET.fromstring(x.text)
    abstract_el = tree.find(f".//{ns}abstract/{ns}p")
    if abstract_el is None:
        return None
    return {
        "abstract": abstract_el.text,
        "doc_number": tree.find(f".//{ns}doc-number").text,
        "country": tree.find(f".//{ns}country").text,
        "kind": tree.find(f".//{ns}kind").text,
        "date": tree.find(f".//{ns}date").text,
    }


def get_description(patent_id):
    url = f"https://ops.epo.org/rest-services/published-data/publication/epodoc/{patent_id}/description"
    header = {"Authorization": f"Bearer {access_token}"}
    x = requests.get(url, headers=header)
    if x.status_code != 200:
        return None
    tree = ET.fromstring(x.text)
    paragraphs = [p.text for p in tree.findall(f".//{ns_ft}description/{ns_ft}p")]
    if not paragraphs:
        return None
    return {
        "doc_number": tree.find(f".//{ns_ft}doc-number").text,
        "kind": tree.find(f".//{ns_ft}kind").text,
        "description": paragraphs,
    }


def get_claims(patent_id):
    url = f"https://ops.epo.org/rest-services/published-data/publication/epodoc/{patent_id}/claims"
    header = {"Authorization": f"Bearer {access_token}"}
    x = requests.get(url, headers=header)
    if x.status_code != 200:
        return None
    tree = ET.fromstring(x.text)
    claims = [c.text for c in tree.findall(f".//{ns_ft}claim-text")]
    if not claims:
        return None
    return {
        "doc_number": tree.find(f".//{ns_ft}doc-number").text,
        "kind": tree.find(f".//{ns_ft}kind").text,
        "claims": claims,
    }


def get_doc_ids_from_applicant(company, range_start, range_end):
    url = "http://ops.epo.org/rest-services/published-data/search"

    header = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/exchange+xml",
        "X-OPS-Range": f"{range_start}-{range_end}"
    }

    query = (
        f'pa any "{company}"'
        " AND (cpc=G06N OR cpc=G06T OR cpc=G06V)"
        " AND (ti=military OR ti=defence OR ti=defense OR ti=battlefield"
        " OR ti=targeting OR ti=combat OR ti=surveillance OR ti=reconnaissance)"
    )

    x = requests.get(url, headers=header, params={"q": query})
    tree = ET.fromstring(x.text)

    ns_ops = "{http://ops.epo.org}"
    results = []
    for ref in tree.findall(f".//{ns_ops}publication-reference"):
        doc = ref.find(f".//{ns}document-id")
        country = doc.find(f"{ns}country").text
        doc_number = doc.find(f"{ns}doc-number").text
        kind = doc.find(f"{ns}kind").text
        results.append(f"{country}{doc_number}.{kind}")

    return results


# patent_id = "EP1000000"

# print(get_abstract_from_docid(patent_id))
# print(get_description(patent_id))
# print(get_claims(patent_id))
print(get_doc_ids_from_applicant("SAAB AB",1,100))



# "RTX Corporation"