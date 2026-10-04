"""A deliberately small executable model of the documented failure chain."""

from dataclasses import dataclass
import math


INT16_MIN = -32768
INT16_MAX = 32767


def finite_number(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise TypeError(f"{name} must be a finite number")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def convert_int16(value: float) -> int:
    """Model nearest-integer, ties-away conversion; not an Ada/CPU emulator."""
    finite_number("BH", value)
    fraction, integral = math.modf(value)
    if abs(fraction) >= 0.5:
        integral += math.copysign(1.0, fraction)
    result = int(integral)
    if not INT16_MIN <= result <= INT16_MAX:
        raise OverflowError("BH conversion exceeds signed 16-bit range")
    return result


@dataclass(frozen=True)
class Stimulus:
    bh: float
    time_s: float
    alignment_end_s: float = 40.0

    def __post_init__(self) -> None:
        for name in ("bh", "time_s", "alignment_end_s"):
            finite_number(name, getattr(self, name))
        if self.time_s < 0 or self.alignment_end_s < 0:
            raise ValueError("Times must be nonnegative; time zero is lift-off")


@dataclass(frozen=True)
class Design:
    alignment_retained: bool = True
    conversion_guard: bool = False
    isolate_alignment_failure: bool = False
    diagnostic_guard: bool = False
    software_in_loop: bool = True
    replicas: int = 2

    def __post_init__(self) -> None:
        for name in (
            "alignment_retained", "conversion_guard",
            "isolate_alignment_failure", "diagnostic_guard", "software_in_loop",
        ):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be boolean")
        if isinstance(self.replicas, bool) or not isinstance(self.replicas, int):
            raise TypeError("replicas must be an integer")
        if self.replicas < 1:
            raise ValueError("replicas must be positive")


@dataclass(frozen=True)
class Outcome:
    conversion_out_of_range: bool
    alignment_exception: bool
    failed_units: int
    navigation_available: bool
    diagnostic_accepted: bool
    unsafe_command: bool
    bus_frame_present: bool = True


def latent_trigger(stimulus: Stimulus) -> bool:
    """Exposure of a retained, unprotected alignment conversion."""
    if stimulus.time_s >= stimulus.alignment_end_s:
        return False
    try:
        convert_int16(stimulus.bh)
    except OverflowError:
        return True
    return False


def evaluate(stimulus: Stimulus, design: Design = Design()) -> Outcome:
    active = design.alignment_retained and stimulus.time_s < stimulus.alignment_end_s
    out_of_range = active and design.software_in_loop and latent_trigger(stimulus)
    exception = out_of_range and not design.conversion_guard
    halted = exception and not design.isolate_alignment_failure
    # Identical implementations share this deterministic failure, not iid faults.
    failed = design.replicas if halted else 0
    diagnostic_accepted = halted and not design.diagnostic_guard
    return Outcome(
        out_of_range, exception, failed, not halted,
        diagnostic_accepted, diagnostic_accepted,
    )


def oracle_detects(outcome: Outcome, oracle: str = "safety") -> bool:
    if oracle == "safety":
        return not outcome.navigation_available or outcome.unsafe_command
    if oracle == "packet":
        return not outcome.bus_frame_present
    raise ValueError(f"Unknown oracle: {oracle}")


def synthetic_trace(
    peak_bh: float,
    design: Design = Design(),
    duration_s: float = 40.0,
    step_s: float = 0.072,
    alignment_end_s: float = 40.0,
) -> list[dict]:
    """Linear BH ramp with latched loss; no dynamics or historical calibration."""
    for name, value in (
        ("peak_bh", peak_bh), ("duration_s", duration_s), ("step_s", step_s),
        ("alignment_end_s", alignment_end_s),
    ):
        finite_number(name, value)
    if duration_s <= 0 or step_s <= 0 or alignment_end_s < 0:
        raise ValueError("Duration/step must be positive and alignment end nonnegative")
    rows = []
    navigation_lost = False
    for index in range(math.floor(duration_s / step_s) + 1):
        time_s = index * step_s
        bh = peak_bh * time_s / duration_s
        outcome = evaluate(Stimulus(bh, time_s, alignment_end_s), design)
        navigation_lost = navigation_lost or not outcome.navigation_available
        rows.append({
            "time_s": time_s,
            "bh": bh,
            "navigation_available": not navigation_lost,
        })
    return rows
