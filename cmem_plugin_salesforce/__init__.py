"""main packages."""

from cmem_plugin_salesforce.helper import MarkdownLink

# list of used links in the markdown documentation
LINKS = {
    "SOQL_INTRO": MarkdownLink(
        "https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/"
        "soql_sosl/sforce_api_calls_soql.htm",
        "developer.salesforce.com",
    ),
    "SOQL_SYNTAX": MarkdownLink(
        "https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/"
        "soql_sosl/sforce_api_calls_soql_select.htm",
        "Salesforce SOQL SELECT Syntax",
    ),
    "OBJECT_REFERENCE": MarkdownLink(
        "https://developer.salesforce.com/docs/atlas.en-us.238.0."
        "object_reference.meta/object_reference/sforce_api_objects_list.htm",
        "Salesforce Standard Objects list",
    ),
    "DEV_CONSOLE": MarkdownLink(
        "https://help.salesforce.com/s/articleView?id=sf.code_dev_console.htm&type=5",
        "Salesforce Developer Console",
    ),
    "TOKEN_DOCU": MarkdownLink(
        "https://help.salesforce.com/"
        "s/articleView?id=sf.user_security_token.htm&type=5",
        "Salesforce Reset Token Documentation",
    ),
    "LEAD_REFERENCE": MarkdownLink(
        "https://developer.salesforce.com/docs/atlas.en-us.238.0."
        "object_reference.meta/object_reference/sforce_api_objects_lead.htm",
        "Lead Object Reference",
    ),
}

USERNAME_DESCRIPTION = (
    "Username of the Salesforce Account. This is typically your email address."
)

SECURITY_TOKEN_DESCRIPTION = f"""
In addition to your standard account credentials, you need to provide a security
token to access your data.

Refer to the {LINKS["TOKEN_DOCU"]} to learn how to retrieve or reset your token.
"""
