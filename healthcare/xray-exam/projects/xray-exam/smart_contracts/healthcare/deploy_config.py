# import logging

# import algokit_utils

# logger = logging.getLogger(__name__)


# # define deployment behaviour based on supplied app spec
# def deploy() -> None:
#     from smart_contracts.artifacts.healthcare.healthcare_client import (
#         HealthcareFactory,
#     )

#     algorand = algokit_utils.AlgorandClient.from_environment()
#     deployer_ = algorand.account.from_environment("DEPLOYER")

#     factory = algorand.client.get_typed_app_factory(
#         HealthcareFactory, default_sender=deployer_.address
#     )

#     app_client, result = factory.deploy(
#         on_update=algokit_utils.OnUpdate.AppendApp,
#         on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
#     )

#     if result.operation_performed in [
#         algokit_utils.OperationPerformed.Create,
#         algokit_utils.OperationPerformed.Replace,
#     ]:
#         algorand.send.payment(
#             algokit_utils.PaymentParams(
#                 amount=algokit_utils.AlgoAmount(algo=1),
#                 sender=deployer_.address,
#                 receiver=app_client.app_address,
#             )
#         )

#     logger.info(
#         f" deployed app {app_client.app_name} ({app_client.app_id}) "
#         f"with operation {result.operation_performed.value}"
#     )
import logging

import algokit_utils

logger = logging.getLogger(__name__)


# define deployment behaviour based on supplied app spec
def deploy() -> None:
    from smart_contracts.artifacts.healthcare.healthcare_client import (
        HealthcareFactory,
    )

    algorand = algokit_utils.AlgorandClient.from_environment()
    deployer_ = algorand.account.from_environment("DEPLOYER")

    factory = algorand.client.get_typed_app_factory(
        HealthcareFactory, default_sender=deployer_.address
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
        f"deployed app {app_client.app_name} ({app_client.app_id}) "
        f"with operation {result.operation_performed.value}"
    )
