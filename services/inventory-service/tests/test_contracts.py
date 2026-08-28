import uuid

from techshop_contracts.events import EventEnvelope, EventType


def test_event_envelope_serializes_the_versioned_contract() -> None:
    order_id = uuid.uuid4()
    event = EventEnvelope(
        event_type=EventType.ORDER_CREATED,
        correlation_id=order_id,
        payload={"order_id": str(order_id), "items": []},
    )

    serialized = event.model_dump(mode="json")

    assert serialized["event_type"] == "order.created.v1"
    assert serialized["correlation_id"] == str(order_id)
