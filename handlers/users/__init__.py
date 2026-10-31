from importlib import import_module

from loader import dp, router

from .different_functions import AccessMiddleware

# The generic message and callback handlers must be registered last.
for module in (
    "profile",
    "user_acceptation",
    "deposit",
    "profile_transporation",
    "output_money",
    "maintenance",
    "start",
    "market",
):
    import_module(f"{__name__}.{module}")

router.message.outer_middleware(AccessMiddleware())
router.callback_query.outer_middleware(AccessMiddleware())

__all__ = ["dp"]
