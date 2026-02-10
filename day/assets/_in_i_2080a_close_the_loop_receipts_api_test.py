import json
from typing import Any, Callable, Dict

import pytest

from ..._domain import InboundTransferOrderShipment, TransferOrderReceipt


class TestINI2080ACloseTheLoopReceipts:
    @pytest.fixture
    def insert_file_data(
        self,
        insert_aws_s3_file: Callable[[Dict[str, Any]], None],
        config_fixture: Any,
    ) -> Callable[..., None]:
        def handler(**kwargs: Any) -> None:
            file_path = kwargs.get("file_path")
            file_content = kwargs.get("file_content")
            insert_aws_s3_file(
                {
                    "Bucket": config_fixture.aws_transfer_data_bucket,
                    "Key": file_path,
                    "Body": file_content,
                }
            )

        return handler

    @pytest.fixture
    def receipt_file_content_factory(self) -> Callable[..., bytes]:
        def factory(tracking_number: str) -> bytes:
            json_content = {
                "Items": [
                    {"trackingNumber": tracking_number, "processedOn": "2025-10-22 14:51:00"},
                ]
            }
            return json.dumps(json_content).encode("utf-8")

        return factory

    @pytest.fixture
    def insert_inbound_shipment_factory(
        self,
        inbound_transfer_order_shipment_factory: Callable[..., InboundTransferOrderShipment],
        transfer_order_receipt_factory: Callable[..., TransferOrderReceipt],
        insert_inbound_transfer_order_shipments: Callable[..., None],
        insert_transfer_order_receipts: Callable[..., None],
    ) -> Callable[..., None]:
        def factory(**kwargs: Any) -> None:
            inbound_to_shipment = inbound_transfer_order_shipment_factory(
                tracking_number=kwargs.get("tracking_number")
            )
            transfer_order_receipt = transfer_order_receipt_factory(
                order_number=inbound_to_shipment.order_number,
                shipment_number=inbound_to_shipment.shipment_number,
            )

            insert_inbound_transfer_order_shipments([inbound_to_shipment])
            insert_transfer_order_receipts("DCTL", [transfer_order_receipt])

        return factory

    def test__close_the_loop_receipt_processed_successfully__moves_file_to_processing(
        self,
        receipt_file_content_factory: Callable[..., bytes],
        generate_event_request: Callable[..., Dict[str, Any]],
        lambda_handler_fixture: Callable[..., Dict[str, Any]],
        aws_context_factory: Any,
        insert_file_data: Callable[..., None],
        insert_inbound_shipment_factory: Callable[..., None],
    ) -> None:
        tracking_number = "TRK123456789"
        file_content = receipt_file_content_factory(tracking_number)
        source_file_path = "vendors/CTL/In/daily_transfer_order_receipts_20250818.json"

        event = generate_event_request(file_path=source_file_path, rice_id="in-i-2080a")
        insert_inbound_shipment_factory(tracking_number=tracking_number)
        insert_file_data(file_path=source_file_path, file_content=file_content)

        response: Dict[str, Any] = lambda_handler_fixture(event, aws_context_factory)

        assert response["statusCode"] == 200
        assert response["body"] == "Events processed successfully"
