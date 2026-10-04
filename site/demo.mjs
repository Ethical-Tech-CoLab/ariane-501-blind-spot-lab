import { compareEvaluation, convertInt16, detectionProbability, budgetFor95 } from "./model.mjs";

const $ = id => document.getElementById(id);
const controls = $("controls");
const flags = ["alignment_retained", "conversion_guard", "isolate_alignment_failure", "diagnostic_guard"];
const format = value => value.toLocaleString("en-US", { maximumFractionDigits: 6 });

function syncRanges() {
  for (const id of ["bh", "time"]) {
    if ($(id).validity.valid) $(`${id}-range`).value = $(id).value;
  }
}

function renderOutcome() {
  const valid = controls.checkValidity();
  $("demo-error").hidden = valid;
  $("outcomes").hidden = !valid;
  if (!valid) {
    $("demo-error").textContent = "Enter a finite BH from -40,000 to 65,535 and a time from 0 to 80 seconds. No result is shown for invalid inputs.";
    return;
  }
  const stimulus = { bh: $("bh").valueAsNumber, time_s: $("time").valueAsNumber };
  const design = Object.fromEntries(flags.map(name => [name, $(name).checked]));
  design.replicas = Number($("replicas").value);
  design.software_in_loop = $("harness").value === "implementation";
  const { actual, observed, detected } = compareEvaluation(stimulus, design, $("oracle").value);
  const lost = !actual.navigation_available;
  const active = design.alignment_retained && stimulus.time_s < 40;
  $("actual-card").dataset.state = lost ? "bad" : "good";
  $("actual-title").textContent = lost ? "Navigation lost" : "Navigation available";
  $("actual-detail").textContent = lost
    ? `${design.replicas} of ${design.replicas} identical units halt. ${actual.unsafe_command ? "A diagnostic frame is accepted as flight data." : "Diagnostics are rejected, but required navigation is still unavailable."}`
    : "This opportunity does not lose navigation under the selected design. That does not establish safety outside this model.";
  $("failed-units").textContent = `${actual.failed_units} / ${design.replicas}`;
  $("navigation").textContent = lost ? "Unavailable" : "Available";
  $("unsafe").textContent = actual.unsafe_command ? "Emitted" : "Not emitted";
  $("evaluation-card").dataset.state = detected ? "bad" : "good";
  $("evaluation-title").textContent = detected ? "FAIL / detected" : "PASS / no detection";
  $("evaluation-detail").textContent = $("oracle").value === "packet"
    ? "The bus frame exists, even when it contains diagnostics. The packet-presence oracle passes."
    : observed.navigation_available
      ? "The selected harness reports navigation available and no unsafe command."
      : "The safety oracle flags missing navigation or an unsafe command.";
  $("explanation").textContent = lost && !detected
    ? design.software_in_loop
      ? "FALSE REASSURANCE: the implementation fails, but the weak oracle scores the diagnostic frame as success. Change the oracle, not the number of tests."
      : "FALSE REASSURANCE: the implementation fails, but the idealized stub bypasses the defective conversion. A better score is not a better implementation."
    : lost
      ? "A useful red result: the evaluation exposes this modeled failure. More identical replicas do not remove its shared cause."
      : "This modeled chain is blocked or not reached. A passing snapshot is not a proof of system safety, and moving time forward is not processor recovery.";
  $("explanation").dataset.state = lost && !detected ? "warning" : "neutral";
  $("conversion-state").textContent = !active
    ? "Not executed in this snapshot"
    : actual.conversion_out_of_range
      ? design.conversion_guard ? "Out of range / guard reports it" : "Out of range"
      : `Representable / result ${format(convertInt16(stimulus.bh))}`;
  $("exception-state").textContent = actual.alignment_exception
    ? design.isolate_alignment_failure ? "Exception isolated / navigation continues" : "Exception halts every replica"
    : "No alignment exception";
  $("diagnostic-state").textContent = lost
    ? actual.diagnostic_accepted ? "Diagnostic accepted as flight data" : "Diagnostic rejected / navigation still lost"
    : "No halt diagnostic in this snapshot";
}

function renderProbability() {
  const valid = $("probability-controls").checkValidity();
  $("probability-error").hidden = valid;
  $("probability-result").hidden = !valid;
  if (!valid) {
    $("probability-error").textContent = "Enter p between 0 and 1, and a whole-number budget between 0 and 10,000,000.";
    return;
  }
  const p = $("probability").valueAsNumber;
  const n = $("budget").valueAsNumber;
  const chance = detectionProbability(p, n);
  const required = budgetFor95(p);
  $("probability-value").textContent = chance === 0 ? "0%" : chance === 1 ? "100% (rounded)"
    : chance > 0.999999 ? ">99.9999%" : `${Number((chance * 100).toPrecision(6))}%`;
  if (p === 1 && n > 0) $("probability-value").textContent = "100%";
  $("probability-bar").style.width = `${chance * 100}%`;
  $("budget-value").textContent = required === null ? "No finite number"
    : Number.isSafeInteger(required) ? `${format(required)} tests` : "Beyond the safe-integer range";
  $("probability-explanation").textContent = p === 0
    ? "If the test world excludes the failure or the oracle cannot see it, no finite number of independent tests helps."
    : "Conditional on your chosen synthetic p and iid opportunities. This is not a launch-risk estimate, a posterior safety probability, or an empirical AI discovery rate.";
}

controls.addEventListener("submit", event => event.preventDefault());
$("probability-controls").addEventListener("submit", event => event.preventDefault());
controls.addEventListener("input", event => {
  if (event.target.id.endsWith("-range")) {
    $(event.target.id.replace("-range", "")).value = event.target.value;
  } else {
    syncRanges();
  }
  renderOutcome();
});
for (const button of document.querySelectorAll("[data-bh], [data-time]")) {
  button.addEventListener("click", () => {
    if (button.dataset.bh) $("bh").value = button.dataset.bh;
    if (button.dataset.time) $("time").value = button.dataset.time;
    syncRanges();
    renderOutcome();
  });
}
for (const button of document.querySelectorAll("[data-preset]")) {
  button.addEventListener("click", () => {
    controls.reset();
    const preset = button.dataset.preset;
    if (preset === "green") $("oracle").value = "packet";
    if (preset === "boundary") $("bh").value = "32767.49";
    if (preset === "stub") $("harness").value = "stub";
    if (preset === "guard") $("diagnostic_guard").checked = true;
    if (preset === "removed") $("alignment_retained").checked = false;
    syncRanges();
    renderOutcome();
  });
}
$("reset").addEventListener("click", () => {
  controls.reset();
  $("probability-controls").reset();
  syncRanges();
  renderOutcome();
  renderProbability();
});
$("probability-controls").addEventListener("input", event => {
  if (event.target.id === "profile" && event.target.value !== "custom") {
    $("probability").value = event.target.value;
  } else if (event.target.id === "probability") {
    $("profile").value = "custom";
  }
  renderProbability();
});
for (const button of document.querySelectorAll("[data-budget]")) {
  button.addEventListener("click", () => {
    $("budget").value = button.dataset.budget;
    renderProbability();
  });
}
renderOutcome();
renderProbability();
