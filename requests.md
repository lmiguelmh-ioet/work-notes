- get ERRORED_PO_INTERFACE_HEADER_ID 
	- [from Josué](https://ioetec.slack.com/archives/C068GL1LHQD/p1769694602897449)
```
curl --verbose --location 'https://fa-evdi-test-saasfaprod1.fa.ocs.oraclecloud.com:443/fscmRestApi/resources/11.13.18.05/receivingReceiptRequests?onlyData=true&fields=lines%3AprocessingErrors%2CHeaderInterfaceId&limit=1000&offset=0' \
--header "Authorization: Basic $ERP_BASIC_AUTH"


curl --location 'https://fa-evdi-test-saasfaprod1.fa.ocs.oraclecloud.com:443/fscmRestApi/resources/11.13.18.05/receivingReceiptRequests/300000687305672/child/lines?onlyData=true&fields=DocumentNumber%2CDocumentLineNumber%2CprocessingErrors' --header "Authorization: Basic $ERP_BASIC_AUTH"
```
