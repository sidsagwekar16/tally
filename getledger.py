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

def fetch_ledger_details(ledger_name: str, company_name: str):
    """Fetch the raw Tally response for a specific ledger's details."""
    xml = f"""
    <ENVELOPE>
      <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>Ledger Details</ID>
      </HEADER>
      <BODY>
        <DESC>
          <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="Ledger Details" ISINITIALIZE="Yes">
                <TYPE>Ledger</TYPE>
                <FILTERS>LedgerFilter</FILTERS>
                <NATIVEMETHOD>NAME</NATIVEMETHOD>
                <NATIVEMETHOD>PARENT</NATIVEMETHOD>
                <NATIVEMETHOD>OPENINGBALANCE</NATIVEMETHOD>
                <NATIVEMETHOD>CLOSINGBALANCE</NATIVEMETHOD>
                <NATIVEMETHOD>ISDEEMEDPOSITIVE</NATIVEMETHOD>
                <NATIVEMETHOD>CURRENCYNAME</NATIVEMETHOD>
              </COLLECTION>
              <SYSTEM TYPE="Formulae" NAME="LedgerFilter">
                $NAME = "{ledger_name}"
              </SYSTEM>
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
    """Main function to fetch and display the raw Tally response for a specific ledger."""
    ledger_name = "Cash"  # Replace with the desired ledger name
    company_name = "Test"    # Replace with your company name
    print(f"Fetching details for ledger '{ledger_name}' in company '{company_name}' at {TALLY_URL}")
    fetch_ledger_details(ledger_name, company_name)

if __name__ == "__main__":
    main()