"""Three-card spread variants."""

from nekomata.spread.base import Spread


class PastPresentFuture(Spread):
    name = "Past / Present / Future"


class BodyMindSpirit(Spread):
    name = "Body / Mind / Spirit"


class SituationActionResult(Spread):
    name = "Situation / Action / Result"
