from typing import Any, Callable, Dict

import pytest
from faker import Faker
from pytest_mock import MockerFixture

from ....._exceptions import InvalidItemNumberError, InvalidPickedDateError
from ....._ports import (
    GetProductIdentifiersRequest,
    GetProductIdentifiersResponse,
    ProductIdentifiers,
)
from .._request import ScaleWmsMaterialIssueRequest
from ._material_issue_preprocessor import (
    MaterialIssuePreprocessor,
    MaterialIssuePreprocessorResponse,
)


class TestMaterialIssuePreprocessorCleanPickedDate:
    @pytest.mark.parametrize(
        "input_date, expected_date",
        [
            ("2025-11-21 08:51:57.035751", "2025-11-21 08:51:57"),
            ("2025-01-15 14:30:00.123456", "2025-01-15 14:30:00"),
            ("2025-12-31 23:59:59.999999", "2025-12-31 23:59:59"),
            ("2025-11-21 08:51:57", "2025-11-21 08:51:57"),
            ("2025-06-15 00:00:00", "2025-06-15 00:00:00"),
        ],
    )
    def test__clean_picked_date__should_remove_microseconds(
        self, input_date: str, expected_date: str
    ) -> None:
        result = MaterialIssuePreprocessor._clean_picked_date(input_date)

        assert result == expected_date


class TestMaterialIssuePreprocessor:
    @pytest.fixture
    def dependencies_factory(self, mocker: MockerFixture) -> Callable[..., Dict[str, Any]]:
        def factory(**kwargs: Any) -> Dict[str, Any]:
            return {
                "erp_product_readers": mocker.Mock(
                    read_product_identifiers=mocker.AsyncMock(
                        return_value=kwargs.get("product_identifiers_response")
                    )
                )
            }

        return factory

    @pytest.mark.asyncio
    async def test__fetch_item_numbers__should_return_upc_to_item_number_mapping(
        self,
        faker: Faker,
        dependencies_factory: Callable[..., Dict[str, Any]],
    ) -> None:
        upc_1 = faker.bothify("############")
        upc_2 = faker.bothify("############")
        item_number_1 = faker.bothify("ITEM-####")
        item_number_2 = faker.bothify("ITEM-####")

        product_identifiers_response = GetProductIdentifiersResponse(
            products={
                upc_1: ProductIdentifiers(number=item_number_1, upc=upc_1),
                upc_2: ProductIdentifiers(number=item_number_2, upc=upc_2),
            }
        )
        dependencies = dependencies_factory(
            product_identifiers_response=product_identifiers_response
        )
        preprocessor = MaterialIssuePreprocessor(**dependencies)

        result = await preprocessor._fetch_item_numbers({upc_1, upc_2})

        assert result == {upc_1: item_number_1, upc_2: item_number_2}
        dependencies["erp_product_readers"].read_product_identifiers.assert_awaited_once()
        call_args = dependencies["erp_product_readers"].read_product_identifiers.call_args
        request: GetProductIdentifiersRequest = call_args.kwargs["request"]
        assert request.identifier_type == GetProductIdentifiersRequest.ProductIdentifierType.UPC
        assert sorted(request.identifiers) == sorted([upc_1, upc_2])

    @pytest.mark.asyncio
    async def test__call__should_preprocess_work_orders_with_item_numbers_and_clean_dates(
        self,
        faker: Faker,
        dependencies_factory: Callable[..., Dict[str, Any]],
        work_detail_factory: Callable[..., ScaleWmsMaterialIssueRequest.WorkDetail],
        work_order_factory: Callable[..., ScaleWmsMaterialIssueRequest.WorkOrder],
    ) -> None:
        upc_1 = faker.bothify("############")
        upc_2 = faker.bothify("############")
        item_number_1 = faker.bothify("ITEM-####")
        item_number_2 = faker.bothify("ITEM-####")
        picked_with_microseconds = "2025-11-21 08:51:57.035751"
        expected_cleaned_date = "2025-11-21 08:51:57"

        work_orders = [
            work_order_factory(
                picked=picked_with_microseconds,
                work_details=[
                    work_detail_factory(item=upc_1),
                    work_detail_factory(item=upc_2),
                ],
            )
        ]

        product_identifiers_response = GetProductIdentifiersResponse(
            products={
                upc_1: ProductIdentifiers(number=item_number_1, upc=upc_1),
                upc_2: ProductIdentifiers(number=item_number_2, upc=upc_2),
            }
        )
        dependencies = dependencies_factory(
            product_identifiers_response=product_identifiers_response
        )
        preprocessor = MaterialIssuePreprocessor(**dependencies)

        result = await preprocessor(work_orders)

        assert isinstance(result, MaterialIssuePreprocessorResponse)
        assert len(result.work_orders) == 1
        assert result.work_orders[0].picked == expected_cleaned_date
        assert result.work_orders[0].work_details[0].item == item_number_1
        assert result.work_orders[0].work_details[1].item == item_number_2
        assert result.upc_to_item_number_map == {upc_1: item_number_1, upc_2: item_number_2}
        assert result.item_number_to_upc_map == {item_number_1: upc_1, item_number_2: upc_2}

    @pytest.mark.asyncio
    async def test__call__should_raise_invalid_picked_date_error__when_date_is_invalid(
        self,
        dependencies_factory: Callable[..., Dict[str, Any]],
        work_order_factory: Callable[..., ScaleWmsMaterialIssueRequest.WorkOrder],
    ) -> None:
        dependencies = dependencies_factory()
        preprocessor = MaterialIssuePreprocessor(**dependencies)
        work_orders = [
            work_order_factory(picked="invalid-date-format"),
        ]

        with pytest.raises(InvalidPickedDateError):
            await preprocessor(work_orders)

    @pytest.mark.asyncio
    async def test__call__should_preserve_other_work_order_fields(
        self,
        faker: Faker,
        dependencies_factory: Callable[..., Dict[str, Any]],
        work_detail_factory: Callable[..., ScaleWmsMaterialIssueRequest.WorkDetail],
        work_order_factory: Callable[..., ScaleWmsMaterialIssueRequest.WorkOrder],
    ) -> None:
        upc = faker.bothify("############")
        item_number = faker.bothify("ITEM-####")
        work_unit = faker.bothify("WU#####")
        erp_order = faker.bothify("WO#####")
        order_type = "Work Order"
        warehouse = "LSLO"

        work_orders = [
            work_order_factory(
                work_unit=work_unit,
                erp_order=erp_order,
                order_type=order_type,
                warehouse=warehouse,
                picked="2025-11-21 08:51:57.035751",
                work_details=[work_detail_factory(item=upc)],
            )
        ]

        product_identifiers_response = GetProductIdentifiersResponse(
            products={
                upc: ProductIdentifiers(number=item_number, upc=upc),
            }
        )
        dependencies = dependencies_factory(
            product_identifiers_response=product_identifiers_response
        )
        preprocessor = MaterialIssuePreprocessor(**dependencies)

        result = await preprocessor(work_orders)

        assert isinstance(result, MaterialIssuePreprocessorResponse)
        assert result.work_orders[0].work_unit == work_unit
        assert result.work_orders[0].erp_order == erp_order
        assert result.work_orders[0].order_type == order_type
        assert result.work_orders[0].warehouse == warehouse

    @pytest.mark.asyncio
    async def test__call__should_preserve_work_detail_fields_except_item(
        self,
        faker: Faker,
        dependencies_factory: Callable[..., Dict[str, Any]],
        work_detail_factory: Callable[..., ScaleWmsMaterialIssueRequest.WorkDetail],
        work_order_factory: Callable[..., ScaleWmsMaterialIssueRequest.WorkOrder],
        serial_number_factory: Callable[..., ScaleWmsMaterialIssueRequest.SerialNumber],
    ) -> None:
        upc = faker.bothify("############")
        item_number = faker.bothify("ITEM-####")
        pick_from_subinventory = "Active"
        picked_quantity = 10
        serial_numbers = [serial_number_factory()]

        work_orders = [
            work_order_factory(
                picked="2025-11-21 08:51:57",
                work_details=[
                    work_detail_factory(
                        item=upc,
                        pick_from_subinventory=pick_from_subinventory,
                        picked_quantity=picked_quantity,
                        serial_numbers=serial_numbers,
                    )
                ],
            )
        ]

        product_identifiers_response = GetProductIdentifiersResponse(
            products={
                upc: ProductIdentifiers(number=item_number, upc=upc),
            }
        )
        dependencies = dependencies_factory(
            product_identifiers_response=product_identifiers_response
        )
        preprocessor = MaterialIssuePreprocessor(**dependencies)

        result = await preprocessor(work_orders)

        assert isinstance(result, MaterialIssuePreprocessorResponse)
        assert result.work_orders[0].work_details[0].item == item_number
        assert result.work_orders[0].work_details[0].pick_from_subinventory == pick_from_subinventory
        assert result.work_orders[0].work_details[0].picked_quantity == picked_quantity
        assert result.work_orders[0].work_details[0].serial_numbers == serial_numbers

    @pytest.mark.asyncio
    async def test__call__should_handle_multiple_work_orders(
        self,
        faker: Faker,
        dependencies_factory: Callable[..., Dict[str, Any]],
        work_detail_factory: Callable[..., ScaleWmsMaterialIssueRequest.WorkDetail],
        work_order_factory: Callable[..., ScaleWmsMaterialIssueRequest.WorkOrder],
    ) -> None:
        upc_1 = faker.bothify("############")
        upc_2 = faker.bothify("############")
        item_number_1 = faker.bothify("ITEM-####")
        item_number_2 = faker.bothify("ITEM-####")

        work_orders = [
            work_order_factory(
                picked="2025-11-21 08:51:57.035751",
                work_details=[work_detail_factory(item=upc_1)],
            ),
            work_order_factory(
                picked="2025-12-15 10:30:00.123456",
                work_details=[work_detail_factory(item=upc_2)],
            ),
        ]

        product_identifiers_response = GetProductIdentifiersResponse(
            products={
                upc_1: ProductIdentifiers(number=item_number_1, upc=upc_1),
                upc_2: ProductIdentifiers(number=item_number_2, upc=upc_2),
            }
        )
        dependencies = dependencies_factory(
            product_identifiers_response=product_identifiers_response
        )
        preprocessor = MaterialIssuePreprocessor(**dependencies)

        result = await preprocessor(work_orders)

        assert isinstance(result, MaterialIssuePreprocessorResponse)
        assert len(result.work_orders) == 2
        assert result.work_orders[0].picked == "2025-11-21 08:51:57"
        assert result.work_orders[0].work_details[0].item == item_number_1
        assert result.work_orders[1].picked == "2025-12-15 10:30:00"
        assert result.work_orders[1].work_details[0].item == item_number_2
        assert result.upc_to_item_number_map == {upc_1: item_number_1, upc_2: item_number_2}

    @pytest.mark.asyncio
    async def test__call__should_deduplicate_upcs_when_fetching_item_numbers(
        self,
        faker: Faker,
        dependencies_factory: Callable[..., Dict[str, Any]],
        work_detail_factory: Callable[..., ScaleWmsMaterialIssueRequest.WorkDetail],
        work_order_factory: Callable[..., ScaleWmsMaterialIssueRequest.WorkOrder],
    ) -> None:
        shared_upc = faker.bothify("############")
        item_number = faker.bothify("ITEM-####")

        work_orders = [
            work_order_factory(
                picked="2025-11-21 08:51:57",
                work_details=[
                    work_detail_factory(item=shared_upc),
                    work_detail_factory(item=shared_upc),
                ],
            ),
            work_order_factory(
                picked="2025-12-15 10:30:00",
                work_details=[work_detail_factory(item=shared_upc)],
            ),
        ]

        product_identifiers_response = GetProductIdentifiersResponse(
            products={
                shared_upc: ProductIdentifiers(number=item_number, upc=shared_upc),
            }
        )
        dependencies = dependencies_factory(
            product_identifiers_response=product_identifiers_response
        )
        preprocessor = MaterialIssuePreprocessor(**dependencies)

        await preprocessor(work_orders)

        call_args = dependencies["erp_product_readers"].read_product_identifiers.call_args
        request: GetProductIdentifiersRequest = call_args.kwargs["request"]
        assert len(request.identifiers) == 1
        assert request.identifiers[0] == shared_upc

    @pytest.mark.asyncio
    async def test__call__should_raise_invalid_item_number_error__when_upc_not_found(
        self,
        faker: Faker,
        dependencies_factory: Callable[..., Dict[str, Any]],
        work_detail_factory: Callable[..., ScaleWmsMaterialIssueRequest.WorkDetail],
        work_order_factory: Callable[..., ScaleWmsMaterialIssueRequest.WorkOrder],
    ) -> None:
        upc_in_request = faker.bothify("############")
        upc_in_response = faker.bothify("############")
        item_number = faker.bothify("ITEM-####")

        work_orders = [
            work_order_factory(
                picked="2025-11-21 08:51:57",
                work_details=[work_detail_factory(item=upc_in_request)],
            )
        ]

        product_identifiers_response = GetProductIdentifiersResponse(
            products={
                upc_in_response: ProductIdentifiers(number=item_number, upc=upc_in_response),
            }
        )
        dependencies = dependencies_factory(
            product_identifiers_response=product_identifiers_response
        )
        preprocessor = MaterialIssuePreprocessor(**dependencies)

        with pytest.raises(InvalidItemNumberError):
            await preprocessor(work_orders)

    @pytest.mark.asyncio
    async def test__call__should_return_response_with_upc_to_item_number_map(
        self,
        faker: Faker,
        dependencies_factory: Callable[..., Dict[str, Any]],
        work_detail_factory: Callable[..., ScaleWmsMaterialIssueRequest.WorkDetail],
        work_order_factory: Callable[..., ScaleWmsMaterialIssueRequest.WorkOrder],
    ) -> None:
        upc_1 = faker.bothify("############")
        upc_2 = faker.bothify("############")
        item_number_1 = faker.bothify("ITEM-####")
        item_number_2 = faker.bothify("ITEM-####")

        work_orders = [
            work_order_factory(
                picked="2025-11-21 08:51:57",
                work_details=[work_detail_factory(item=upc_1)],
            ),
            work_order_factory(
                picked="2025-12-15 10:30:00",
                work_details=[work_detail_factory(item=upc_2)],
            ),
        ]

        product_identifiers_response = GetProductIdentifiersResponse(
            products={
                upc_1: ProductIdentifiers(number=item_number_1, upc=upc_1),
                upc_2: ProductIdentifiers(number=item_number_2, upc=upc_2),
            }
        )
        dependencies = dependencies_factory(
            product_identifiers_response=product_identifiers_response
        )
        preprocessor = MaterialIssuePreprocessor(**dependencies)

        result = await preprocessor(work_orders)

        assert isinstance(result, MaterialIssuePreprocessorResponse)
        assert result.upc_to_item_number_map == {upc_1: item_number_1, upc_2: item_number_2}
        assert len(result.upc_to_item_number_map) == 2
