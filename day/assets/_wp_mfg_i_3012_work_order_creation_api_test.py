from typing import Any, Callable, Dict

import pytest

from ..._adapters import Settings


class TestMfgI3012WorkOrdersTrigger:
    @pytest.fixture
    def s3_bucket_name(self, config_fixture: Settings) -> str:
        return config_fixture.aws_anaplan_data_bucket

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
                    "Bucket": config_fixture.aws_anaplan_data_bucket,
                    "Key": file_path,
                    "Body": file_content,
                }
            )

        return handler

    def test__moves_work_order_file_to_archive__when_orders_are_processed_successfully(
        self,
        work_order_file_factory: Callable[..., bytes],
        generate_event_request: Callable[..., Dict[str, Any]],
        lambda_handler_fixture: Callable[..., Dict[str, Any]],
        insert_file_data: Callable[..., None],
        file_movement_listener: Callable[..., bool],
        aws_context_factory: Any,
    ) -> None:
        file_contents = work_order_file_factory()
        source_file_path = "In/SRW_Work_Orders_Import.csv"
        expected_movement_path_prefix = (
            f"Archive/SRW_Work_Orders_Import__{aws_context_factory.aws_request_id}_"
        )
        event_request = generate_event_request(file_path=source_file_path, rice_id="MFG-I-3012")
        insert_file_data(file_path=source_file_path, file_content=file_contents)

        response: Dict[str, Any] = lambda_handler_fixture(event_request, aws_context_factory)

        assert response["statusCode"] == 200
        assert response["body"] == "Events processed successfully"
        is_file_on_archive = file_movement_listener(prefix=expected_movement_path_prefix)
        assert is_file_on_archive, "File was not moved to archive"
