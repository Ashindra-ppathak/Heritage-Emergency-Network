"""
Recommendation engine: produces recommended next actions and suggests a
target organization for routing, based on issue type.
"""

from utils.helpers import load_json

ORG_DATA = load_json("organizations.json")

ISSUE_RECOMMENDATIONS = {
    "Structural Damage": "Urgent conservation inspection",
    "Water Damage": "Assess drainage and moisture control measures",
    "Fire Damage": "Immediate structural safety assessment",
    "Vandalism": "Request site inspection and document damage",
    "Illegal Construction": "Escalate to local administration for encroachment review",
    "Encroachment": "Escalate to local administration for encroachment review",
    "Neglect": "Schedule local heritage inspection",
    "Pollution": "Engage municipal / environmental authority",
    "Natural Disaster": "Immediate structural safety assessment",
    "Theft": "Report to authorities and document missing elements",
    "Abandonment": "Schedule site condition inspection",
    "Tradition at Risk": "Engage cultural organization and document active practitioners",
    "Craft Decline": "Engage cultural organization and document active practitioners",
    "Other": "Schedule preliminary expert review",
}


def recommend_action(issue_type: str) -> str:
    return ISSUE_RECOMMENDATIONS.get(issue_type, "Schedule preliminary expert review")


def route_organization(issue_type: str) -> dict:
    """
    Return the best-matching prototype organization for a given issue type.
    This is a simple demo routing engine — not a real institutional link.
    """
    orgs = ORG_DATA.get("organizations", [])
    for org in orgs:
        if issue_type in org.get("handles", []):
            return org
    # default fallback organization
    return {
        "name": "State Culture Department",
        "type": "Government Culture Body",
        "handles": [],
    }


def organizations_disclaimer() -> str:
    return ORG_DATA.get(
        "disclaimer",
        "All organizations listed are PROTOTYPE / DEMO entities for simulation purposes only.",
    )
