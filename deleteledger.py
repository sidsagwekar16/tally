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

def delete_ledger(ledger_name: str, company_name: str):
    """Send a request to Tally to delete a specific ledger and show the raw response."""
    xml = f"""
    <ENVELOPE>
      <HEADER>
        <TALLYREQUEST>Import Data</TALLYREQUEST>
      </HEADER>
      <BODY>
        <IMPORTDATA>
          <REQUESTDESC>
            <REPORTNAME>All Masters</REPORTNAME>
            <STATICVARIABLES>
              <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
            </STATICVARIABLES>
          </REQUESTDESC>
          <REQUESTDATA>
            <TALLYMESSAGE>
              <LEDGER NAME="{ledger_name}" ACTION="Delete">
                <NAME>{ledger_name}</NAME>
              </LEDGER>
            </TALLYMESSAGE>
          </REQUESTDATA>
        </IMPORTDATA>
      </BODY>
    </ENVELOPE>
    """
    print("\n[DEBUG] XML Sent to Tally:\n", xml)
    response = send_to_tally(xml)
    return response

def main():
    """Main function to delete a ledger and display the raw Tally response."""
    ledger_name = "MONEY"  # Replace with the ledger name to delete
    company_name = "Test"    # Replace with your company name
    print(f"Deleting ledger '{ledger_name}' in company '{company_name}' at {TALLY_URL}")
    delete_ledger(ledger_name, company_name)

if __name__ == "__main__":
    main()