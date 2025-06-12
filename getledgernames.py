import requests
import xml.etree.ElementTree as ET
import re

# Tally server details
TALLY_URL = "http://localhost:9000"

def sanitize_xml(text: str) -> str:
    """Sanitize the XML by removing invalid characters and ensuring proper encoding."""
    # Remove control characters (except tab, newline, carriage return)
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    # Ensure the response is UTF-8 encoded
    return text.encode('utf-8').decode('utf-8', errors='replace')

def send_to_tally(xml: str) -> str:
    """Send XML request to Tally and return the response."""
    headers = {"Content-Type": "application/xml"}
    try:
        response = requests.post(TALLY_URL, data=xml, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to Tally: {str(e)}")
        return ""

def fetch_ledgers(selected_company: str) -> str:
    """Fetch all ledger names and their parent groups from Tally."""
    xml = f"""
    <ENVELOPE>
      <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>All Ledgers</ID>
      </HEADER>
      <BODY>
        <DESC>
          <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            <SVCURRENTCOMPANY>{selected_company}</SVCURRENTCOMPANY>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="All Ledgers" ISINITIALIZE="Yes">
                <TYPE>Ledger</TYPE>
                <NATIVEMETHOD>NAME</NATIVEMETHOD>
                <NATIVEMETHOD>PARENT</NATIVEMETHOD>
              </COLLECTION>
            </TDLMESSAGE>
          </TDL>
        </DESC>
      </BODY>
    </ENVELOPE>
    """
    print("\n[DEBUG] XML Sent to Tally:\n", xml)
    response = send_to_tally(xml)
    # Sanitize the response before parsing
    sanitized_response = sanitize_xml(response)
    print("\n[DEBUG] Tally Raw Response:\n", sanitized_response)
    return sanitized_response

def parse_and_display_ledgers(response: str):
    """Parse the Tally response and display ledger names with their parent groups."""
    if not response:
        print("❌ No response received from Tally.")
        return

    try:
        root = ET.fromstring(response)
        ledgers = []
        for ledger in root.findall(".//LEDGER"):
            name = ledger.find(".//LANGUAGENAME.LIST/NAME.LIST/NAME")
            parent = ledger.find(".//PARENT")
            if name is not None and name.text:
                ledger_info = {
                    "name": name.text,
                    "parent": parent.text.strip() if parent is not None and parent.text else "Unknown"
                }
                ledgers.append(ledger_info)

        if not ledgers:
            print("❌ No ledgers found in the response.")
            return

        print("\n📂 Ledgers Found:")
        for i, ledger in enumerate(ledgers):
            print(f"  {i+1}. {ledger['name']} (Group: {ledger['parent']})")

    except ET.ParseError as e:
        print(f"❌ Failed to parse Tally response: {str(e)}")

def main():
    """Main function to fetch and display ledgers from Tally."""
    company_name = "Test"
    print(f"Fetching ledgers for company '{company_name}' at {TALLY_URL}")
    response = fetch_ledgers(company_name)
    parse_and_display_ledgers(response)

if __name__ == "__main__":
    main()