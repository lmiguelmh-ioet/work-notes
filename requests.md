- get shipment line from transfer order
	- Transfer Orders can be created by Kaio
	- same can be obtained for each line in UI
	- ![](assets/Pasted%20image%2020260306153218.png)
	- View Shipment and Receipts
	- ![](assets/Pasted%20image%2020260306153336.png)
	- ![](assets/Pasted%20image%2020260306153405.png)
```
curl --verbose --location 'https://fa-evdi-dev1-saasfaprod1.fa.ocs.oraclecloud.com:443/fscmRestApi/resources/11.13.18.05/shipmentLineChangeRequests/action/pickRelease' --header 'Content-Type: application/vnd.oracle.adf.action+json' --header "Authorization: Basic $ERP_BASIC_AUTH" --data '{"details": [{"EntityType": "Line", "ShipmentLine" : 3824163}]}'

< HTTP/2 200 
< content-type: application/vnd.oracle.adf.actionresult+json
< referrer-policy: origin
< x-content-type-options: nosniff
< cache-control: no-cache, no-store, must-revalidate
< location: 
< x-oracle-dms-ecid: 006J9cGQqAJ56isMwiBh6G00DhoD0001AO
< x-oracle-dms-rid: 0:5
< rest-framework-version: 1
< x-xss-protection: 1; mode=block
< pragma: no-cache
< content-language: en
< strict-transport-security: max-age=31536000; includeSubDomains
< date: Mon, 09 Mar 2026 16:40:45 GMT
< content-length: 201
< akgrn: 0.4cbe3cc8.1773074444.99d865ed
< 
{
  "result" : {
    "Message" : "Concurrent requests submitted: 1. Concurrent requests failed: 0. Pick release request ID 105160251 was created for the selected lines.",
    "ReturnStatus" : "S"
  }
}
```

- get ShipmentLine from TransferOrder
```
curl --header "Authorization: Basic $ERP_BASIC_AUTH" --location 'https://fa-evdi-dev1-saasfaprod1.fa.ocs.oraclecloud.com/fscmRestApi/resources/11.13.18.05/shipmentLines?q=OrderTypeCode=TRANSFER_ORDER;Order=1050844' --header 'Content-Type: application/json' --compressed | jq -r '.items[] | [.ShipmentLine, .OrderTypeCode, .Order] | @csv'

curl --header "Authorization: Basic $ERP_BASIC_AUTH" --location 'https://fa-evdi-dev1-saasfaprod1.fa.ocs.oraclecloud.com/fscmRestApi/resources/11.13.18.05/shipmentLines?q=OrderTypeCode=TRANSFER_ORDER;Order=1050844&onlyData=true&limit=500&totalResults=true' --header 'Content-Type: application/json' --compressed

# from gabo: {{oracle_dev1}}/fscmRestApi/resources/11.13.18.05/shipmentLines?q=OrderType='Transfer order' AND Order='1048842'&onlyData=true&limit=500&totalResults=true

```


- get ERRORED_PO_INTERFACE_HEADER_ID 
```
curl --verbose --location 'https://fa-evdi-test-saasfaprod1.fa.ocs.oraclecloud.com:443/fscmRestApi/resources/11.13.18.05/receivingReceiptRequests?onlyData=true&fields=lines%3AprocessingErrors%2CHeaderInterfaceId&limit=1000&offset=0' \
--header "Authorization: Basic $ERP_BASIC_AUTH"


curl --verbose --location 'https://fa-evdi-test-saasfaprod1.fa.ocs.oraclecloud.com:443/fscmRestApi/resources/11.13.18.05/receivingReceiptRequests/300000687305672/child/lines?onlyData=true&fields=DocumentNumber%2CDocumentLineNumber%2CprocessingErrors' --header "Authorization: Basic $ERP_BASIC_AUTH"
```
