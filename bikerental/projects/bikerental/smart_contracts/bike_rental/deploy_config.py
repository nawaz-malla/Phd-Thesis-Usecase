import logging
import algokit_utils
from attrs import Factory

logger = logging.getLogger(__name__)


def deploy() -> None:
    """
    Deploy the BikeRental Algorand smart contract using algokit.
    """

    from smart_contracts.artifacts.bike_rental.bike_rental_client import (
        BikeRentalFactory,
    )

    algorand = algokit_utils.AlgorandClient.from_environment()
    deployer_ = algorand.account.from_environment("DEPLOYER")

    factory = algorand.client.get_typed_app_factory(
        BikeRentalFactory, default_sender=deployer_.address
    )

    # Use UpdateApp to keep the same app id when logic changes
    app_client, result = factory.deploy(
        on_update=algokit_utils.OnUpdate.UpdateApp,
        # choose how to handle schema breaks; here we append a new app
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
    )

    if result.operation_performed in [
        algokit_utils.OperationPerformed.Create,
        algokit_utils.OperationPerformed.Replace,
    ]:
        algorand.send.payment(
            algokit_utils.PaymentParams(
                amount=algokit_utils.AlgoAmount(algo=1),
                sender=deployer_.address,
                receiver=app_client.app_address,
            )
        )

    logger.info(
        f"✅ Deployed BikeRental app '{app_client.app_name}' "
        f"(App ID: {app_client.app_id}) successfully."
    )
