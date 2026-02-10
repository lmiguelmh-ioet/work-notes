from datetime import datetime, timezone
from typing import Any, Callable, Dict

import pytest


class TestWmsI1041BreakagesTrigger:
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

    @pytest.mark.parametrize("facility", ["LSLO", "LLAS"])
    def test__moves_breakage_file_to_archive__when_breakage_is_processed_successfully(
        self,
        rxt_file_content_factory: Callable[..., bytes],
        facility: str,
        generate_event_request: Callable[..., Dict[str, Any]],
        lambda_handler_fixture: Callable[..., Dict[str, Any]],
        aws_context_factory: Any,
        insert_file_data: Callable[..., None],
        file_movement_listener: Callable[..., bool],
    ) -> None:
        today_datetime = datetime.now(tz=timezone.utc)
        file_content = rxt_file_content_factory(did_lenses_break=True, did_frame_break=True)
        source_file_path = f"vendors/innovations_lms/Out/{facility}/TEST.RXT"
        expected_movement_path_prefix = (
            f"vendors/innovations_lms/Archive/{facility}/{today_datetime.strftime('%Y%m%d')}"
            "/TEST.RXT"
        )
        event = generate_event_request(file_path=source_file_path, rice_id="WMS-I-1041")
        context = aws_context_factory
        insert_file_data(file_path=source_file_path, file_content=file_content)

        response: Dict[str, Any] = lambda_handler_fixture(event, context)

        assert response["statusCode"] == 200
        assert response["body"] == "Events processed successfully"
        is_file_on_archive = file_movement_listener(prefix=expected_movement_path_prefix)
        assert is_file_on_archive, "File was not moved to archive"
