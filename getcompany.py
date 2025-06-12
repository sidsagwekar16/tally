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

def fetch_companies():
    """Fetch the raw Tally response for the list of companies."""
    xml = """
    <ENVELOPE>
      <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>List of Companies</ID>
      </HEADER>
      <BODY>
        <DESC>
          <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="List of Companies" ISINITIALIZE="Yes">
                <TYPE>Company</TYPE>
                <NATIVEMETHOD>NAME</NATIVEMETHOD>
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
    """Main function to fetch and display the raw Tally response for companies."""
    print(f"Fetching companies at {TALLY_URL}")
    fetch_companies()

if __name__ == "__main__":
    main()