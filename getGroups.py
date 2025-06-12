import requests

# Tally server details
TALLY_URL = "http://localhost:9000"

def send_to_tally(xml: str) -> str:
    """Send XML request to Tally and return the response."""
    headers = {"Content-Type": "application/xml"}
    try:
        response = requests.post(TALLY_URL, data=xml.encode('utf-8'), headers=headers)
        response.raise_for_status()
        print("\n[DEBUG] Raw Response Bytes:\n", response.content)
        print("\n[DEBUG] Raw Tally Response:\n", response.content.decode('utf-8', errors='replace'))
        return response.content.decode('utf-8', errors='replace')
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to Tally: {str(e)}")
        return ""

def fetch_all_groups(company_name: str):
    """Fetch the raw Tally response for all groups."""
    xml = f"""
    <ENVELOPE>
      <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>List of Groups</ID>
      </HEADER>
      <BODY>
        <DESC>
          <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="List of Groups" ISINITIALIZE="Yes">
                <TYPE>Group</TYPE>
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
    return response

def main():
    """Main function to fetch and display the raw Tally response for all groups."""
    company_name = "Test"  # Replace with your company name
    print(f"Fetching all groups for company '{company_name}' at {TALLY_URL}")
    fetch_all_groups(company_name)

if __name__ == "__main__":
    main()